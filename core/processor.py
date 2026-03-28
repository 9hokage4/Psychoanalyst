from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any

import pandas as pd


_QCOL_RE = re.compile(r"^\s*(\d{1,3})\s*[\.\)]\s*")


def _extract_qnum(col: str) -> int | None:
    """
    Извлекает номер вопроса из названия колонки:
    '1) ...' -> 1
    '1. ...' -> 1
    """
    if not isinstance(col, str):
        return None

    match = _QCOL_RE.match(col)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


def _extract_answer_number(value: Any) -> int:
    """
    Преобразует значение ответа вида:
    '1 - никогда' -> 1
    '2' -> 2
    3 -> 3
    NaN -> 0
    """
    if pd.isna(value):
        return 0

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    text = str(value).strip()
    match = re.match(r"^\s*(\d+)", text)
    if match:
        return int(match.group(1))

    return 0


def _replace_answer_with_weight(value: Any, answer_weights: Dict[int, int]) -> int:
    """
    Берет номер ответа и заменяет его на вес из answer_weights.
    Если ответ пустой/не распознан -> 0.
    """
    answer_number = _extract_answer_number(value)

    if answer_number == 0:
        return 0

    if answer_number not in answer_weights:
        raise KeyError(
            f"Для варианта ответа '{answer_number}' не найден вес в answer_weights."
        )

    return int(answer_weights[answer_number])


def _format_count_percent(count: int, total: int) -> str:
    """Форматирует значение как 'N чел./X%'"""
    percent = 0 if total == 0 else int(round(count / total * 100))
    return f"{count} чел./{percent}%"


def _interpret_sum(
    total: float,
    bounds: Dict[str, int],
    level_order: List[str],
    level_ru: Dict[str, str],
    scale_title: str,
) -> Tuple[str, str]:
    """
    Определяет уровень по сумме баллов, используя динамические границы из scales_config.

    bounds приходит в формате, например:
    {
        "low_max": 25,
        "mid_low_min": 26,
        "mid_low_max": 40,
        "mid_high_min": 41,
        "mid_high_max": 65,
        "high_min": 66,
        "high_max": 200
    }

    Возвращает:
    (
        технический_ключ_уровня,
        текстовая_интерпретация
    )
    """
    if pd.isna(total):
        return "", ""

    total = float(total)

    for level_key in level_order:
        min_key = f"{level_key}_min"
        max_key = f"{level_key}_max"

        level_min = bounds.get(min_key, float("-inf"))
        level_max = bounds.get(max_key, float("inf"))

        if level_min <= total <= level_max:
            level_name_ru = level_ru.get(level_key, level_key)
            interpretation = f'{level_name_ru} ({int(total)} баллов)'
            return level_key, interpretation

    return "", ""


def _build_distribution_long(
    df: pd.DataFrame,
    scope_type: str,
    scope_value_column: str,
    scale_name: str,
    level_code_column: str,
    level_order: List[str],
    level_ru: Dict[str, str],
) -> pd.DataFrame:
    """
    Формирует tidy-таблицу для графиков:
    одна строка = одна комбинация (область, шкала, уровень)
    """
    rows: List[Dict[str, Any]] = []

    for scope_value, sub_df in df.groupby(scope_value_column, dropna=False):
        total = len(sub_df)
        counts = sub_df[level_code_column].value_counts(dropna=False).to_dict()

        for level_key in level_order:
            count = int(counts.get(level_key, 0))
            percent = 0.0 if total == 0 else (count / total * 100)

            rows.append(
                {
                    "Тип области": scope_type,
                    "Название области": str(scope_value),
                    "Название шкалы": scale_name,
                    "Код уровня": level_key,
                    "Название уровня": level_ru.get(level_key, level_key),
                    "Количество обучающихся": total,
                    "Количество по уровню": count,
                    "Процент по уровню": percent,
                }
            )

    return pd.DataFrame(rows)


def _build_summary_table(
    df: pd.DataFrame,
    scope_type: str,
    scope_value_column: str,
    scales_config: Dict[str, Dict],
    level_order: List[str],
    level_ru: Dict[str, str],
    scale_columns: Dict[str, Dict],
) -> Dict[str, pd.DataFrame]:
    """
    Строит сводные таблицы распределения для каждой группы/курса.

    Возвращает словарь: {название_группы/курса: DataFrame с таблицей распределения}
    """
    result = {}

    for scope_value, sub_df in df.groupby(scope_value_column, dropna=False):
        total_respondents = len(sub_df)
        rows = []

        for scale_name, scale_config in scales_config.items():
            scale_title = scale_config.get("title_ru", scale_name)
            
            # Используем имена колонок из scale_columns
            if scale_name not in scale_columns:
                continue
                
            level_code_column_name = scale_columns[scale_name]["level"]

            if level_code_column_name not in sub_df.columns:
                continue

            level_counts = sub_df[level_code_column_name].value_counts(dropna=False).to_dict()

            row = {"Шкала": scale_title}
            for level_key in level_order:
                count = int(level_counts.get(level_key, 0))
                cell_value = _format_count_percent(count, total_respondents)
                row[level_ru.get(level_key, level_key)] = cell_value

            rows.append(row)

        if rows:
            summary_df = pd.DataFrame(rows)
            # Добавляем итоговую строку с количеством респондентов
            result[str(scope_value)] = {
                "table": summary_df,
                "total_respondents": total_respondents
            }
    
    return result


def _build_charts_data(
    df: pd.DataFrame,
    scales_config: Dict[str, Dict],
    level_order: List[str],
    level_ru: Dict[str, str],
    scale_columns: Dict[str, Dict],
    has_group: bool = True,
    has_course: bool = True,
) -> Dict[str, pd.DataFrame]:
    """
    Строит данные для графиков.

    Возвращает словарь с данными для различных типов графиков:
    - by_scale_level: распределение по уровням для каждой шкалы (общее)
    - by_group_scale: распределение по группам для каждой шкалы (если есть колонка "Группа")
    - by_course_scale: распределение по курсам для каждой шкалы (если есть колонка "Курс")
    - mean_scores: средние баллы по шкалам
    """
    charts_data = {}

    # 1. Распределение по уровням для каждой шкалы (общее)
    rows_by_scale = []
    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)

        # Используем имена колонок из scale_columns
        if scale_name not in scale_columns:
            continue

        level_code_column_name = scale_columns[scale_name]["level"]
        sum_column_name = scale_columns[scale_name]["sum"]

        if level_code_column_name not in df.columns:
            continue

        total = len(df)
        level_counts = df[level_code_column_name].value_counts(dropna=False).to_dict()
        mean_score = df[sum_column_name].mean() if sum_column_name in df.columns else 0

        for level_key in level_order:
            count = int(level_counts.get(level_key, 0))
            percent = 0.0 if total == 0 else (count / total * 100)

            rows_by_scale.append({
                "Название шкалы": scale_title,
                "Код уровня": level_key,
                "Название уровня": level_ru.get(level_key, level_key),
                "Количество по уровню": count,
                "Процент по уровню": percent,
                "Средний балл": round(mean_score, 1),
            })

    charts_data["by_scale_level"] = pd.DataFrame(rows_by_scale) if rows_by_scale else pd.DataFrame()

    # 2. Распределение по группам для каждой шкалы (только если есть колонка "Группа")
    if has_group:
        long_parts_group: List[pd.DataFrame] = []
        for scale_name, scale_config in scales_config.items():
            scale_title = scale_config.get("title_ru", scale_name)

            if scale_name not in scale_columns:
                continue

            level_code_column_name = scale_columns[scale_name]["level"]

            long_parts_group.append(
                _build_distribution_long(
                    df=df,
                    scope_type="Группа",
                    scope_value_column="Группа",
                    scale_name=scale_title,
                    level_code_column=level_code_column_name,
                    level_order=level_order,
                    level_ru=level_ru,
                )
            )

        charts_data["by_group_scale"] = pd.concat(long_parts_group, ignore_index=True) if long_parts_group else pd.DataFrame()
    else:
        charts_data["by_group_scale"] = pd.DataFrame()

    # 3. Распределение по курсам для каждой шкалы (только если есть колонка "Курс")
    if has_course:
        long_parts_course: List[pd.DataFrame] = []
        for scale_name, scale_config in scales_config.items():
            scale_title = scale_config.get("title_ru", scale_name)

            if scale_name not in scale_columns:
                continue

            level_code_column_name = scale_columns[scale_name]["level"]

            long_parts_course.append(
                _build_distribution_long(
                    df=df,
                    scope_type="Курс",
                    scope_value_column="Курс",
                    scale_name=scale_title,
                    level_code_column=level_code_column_name,
                    level_order=level_order,
                    level_ru=level_ru,
                )
            )

        charts_data["by_course_scale"] = pd.concat(long_parts_course, ignore_index=True) if long_parts_course else pd.DataFrame()
    else:
        charts_data["by_course_scale"] = pd.DataFrame()

    # 4. Средние баллы по шкалам (общие)
    mean_rows = []
    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)

        if scale_name not in scale_columns:
            continue

        sum_column_name = scale_columns[scale_name]["sum"]

        if sum_column_name in df.columns:
            mean_rows.append({
                "Название шкалы": scale_title,
                "Средний балл": round(df[sum_column_name].mean(), 1),
                "Мин": int(df[sum_column_name].min()),
                "Макс": int(df[sum_column_name].max()),
            })

    charts_data["mean_scores"] = pd.DataFrame(mean_rows) if mean_rows else pd.DataFrame()

    return charts_data


def process_data(
    df: pd.DataFrame,
    scales_config: Dict[str, Dict],
    level_order: List[str],
    level_ru: Dict[str, str],
    answer_weights: Dict[int, int],
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], Dict[str, Any]]:
    """
    Основная функция обработки результатов теста.

    Параметры:
    - df: исходный DataFrame с ответами
    - scales_config: конфиг шкал из SettingsDialog
    - level_order: порядок уровней
    - level_ru: русские названия уровней
    - answer_weights: веса ответов

    Возвращает:
    - table_df: DataFrame с индивидуальными результатами (для таблицы)
    - charts_data: словарь с данными для графиков
    - summary_data: словарь со сводными таблицами для групп и курсов
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("process_data ожидает pandas.DataFrame.")

    # Проверяем наличие опциональных колонок
    has_group = "Группа" in df.columns
    has_course = "Курс" in df.columns

    df_result = df.copy()

    # ------------------------------------------------------------------
    # 1. Находим колонки вопросов и строим отображение: номер вопроса -> имя колонки
    # ------------------------------------------------------------------
    question_number_to_column: Dict[int, str] = {}
    for column in df_result.columns:
        qnum = _extract_qnum(str(column))
        if qnum is not None:
            question_number_to_column[qnum] = column

    # ------------------------------------------------------------------
    # 2. Сохраняем оригинальные ответы на вопросы (для таблицы)
    # ------------------------------------------------------------------
    original_answer_columns: Dict[int, str] = {}
    for question_number, original_column in question_number_to_column.items():
        df_result[f"Вопрос {question_number}"] = df_result[original_column]
        original_answer_columns[question_number] = f"Вопрос {question_number}"

    # ------------------------------------------------------------------
    # 3. Создаем числовые колонки по вопросам, где значение = вес ответа
    # ------------------------------------------------------------------
    weighted_question_columns: Dict[int, str] = {}

    for question_number, original_column in question_number_to_column.items():
        weighted_column_name = f"Вес_{question_number}"
        df_result[weighted_column_name] = df_result[original_column].map(
            lambda x: _replace_answer_with_weight(x, answer_weights)
        )
        weighted_question_columns[question_number] = weighted_column_name

    # ------------------------------------------------------------------
    # 4. Считаем суммы и интерпретации по всем пользовательским шкалам
    # ------------------------------------------------------------------
    scale_columns = {}  # Для хранения имён колонок шкал
    
    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)
        qnums = scale_config.get("qnums", [])
        bounds = scale_config.get("bounds", {})

        missing_questions = [q for q in qnums if q not in weighted_question_columns]
        if missing_questions:
            raise KeyError(
                f'Для шкалы "{scale_title}" не найдены колонки вопросов: {missing_questions}.'
            )

        scale_question_columns = [weighted_question_columns[q] for q in qnums]

        sum_column_name = f'Сумма_{scale_name}'
        level_code_column_name = f'Уровень_{scale_name}'
        interpretation_column_name = f'Шкала_{scale_title}'

        df_result[sum_column_name] = df_result[scale_question_columns].sum(axis=1)

        interpreted = df_result[sum_column_name].map(
            lambda total: _interpret_sum(
                total=total,
                bounds=bounds,
                level_order=level_order,
                level_ru=level_ru,
                scale_title=scale_title,
            )
        )

        df_result[level_code_column_name] = interpreted.map(lambda x: x[0])
        df_result[interpretation_column_name] = interpreted.map(lambda x: x[1])
        
        scale_columns[scale_name] = {
            "title": scale_title,
            "sum": sum_column_name,
            "level": level_code_column_name,
            "interpretation": interpretation_column_name,
        }

    # ------------------------------------------------------------------
    # 5. Формируем итоговый DataFrame для таблицы
    # ------------------------------------------------------------------
    # Базовые колонки (только существующие)
    base_columns = ["Дата", "ФИО"]
    if has_group:
        base_columns.append("Группа")
    if has_course:
        base_columns.append("Курс")

    # Колонки с ответами на вопросы
    question_cols = [original_answer_columns[q] for q in sorted(original_answer_columns.keys())]

    # Колонки со шкалами (интерпретация)
    scale_cols = [scale_columns[s]["interpretation"] for s in scale_columns]

    table_columns = base_columns + question_cols + scale_cols

    # Фильтруем только существующие колонки
    existing_columns = [col for col in table_columns if col in df_result.columns]
    table_df = df_result[existing_columns].copy()
    
    # Переименовываем колонки вопросов для красоты
    rename_map = {}
    for q_num in sorted(original_answer_columns.keys()):
        old_name = original_answer_columns[q_num]
        rename_map[old_name] = str(q_num)

    table_df = table_df.rename(columns=rename_map)

    # ------------------------------------------------------------------
    # 6. Строим данные для графиков
    # ------------------------------------------------------------------
    charts_data = _build_charts_data(
        df=df_result,
        scales_config=scales_config,
        level_order=level_order,
        level_ru=level_ru,
        scale_columns=scale_columns,
        has_group=has_group,
        has_course=has_course,
    )

    # ------------------------------------------------------------------
    # 7. Строим сводные таблицы для групп и курсов (если есть колонки)
    # ------------------------------------------------------------------
    summary_data = {
        "has_group": has_group,
        "has_course": has_course,
        "level_order": level_order,
        "level_ru": level_ru,
        "scales_config": scales_config,
    }
    
    # Добавляем сводные таблицы только если есть соответствующие колонки
    if has_group:
        summary_data["group_summary"] = _build_summary_table(
            df=df_result,
            scope_type="Группа",
            scope_value_column="Группа",
            scales_config=scales_config,
            level_order=level_order,
            level_ru=level_ru,
            scale_columns=scale_columns,
        )
    else:
        summary_data["group_summary"] = {}
    
    if has_course:
        summary_data["course_summary"] = _build_summary_table(
            df=df_result,
            scope_type="Курс",
            scope_value_column="Курс",
            scales_config=scales_config,
            level_order=level_order,
            level_ru=level_ru,
            scale_columns=scale_columns,
        )
    else:
        summary_data["course_summary"] = {}

    return table_df, charts_data, summary_data
