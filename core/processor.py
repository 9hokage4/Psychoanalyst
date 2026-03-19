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
    percent = 0 if total == 0 else int(round(count / total * 100))
    return f"{count} ({percent}%)"


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
            interpretation = f'{level_name_ru} по шкале "{scale_title}"'
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


def _build_distribution_wide(
    df_long: pd.DataFrame,
    level_order: List[str],
    level_ru: Dict[str, str],
) -> pd.DataFrame:
    """
    Формирует широкую таблицу:
    колонки уровней содержат значения вида '3 (13%)'
    """
    if df_long.empty:
        return pd.DataFrame()

    tmp = df_long.copy()
    tmp["Ячейка"] = tmp.apply(
        lambda row: _format_count_percent(
            int(row["Количество по уровню"]),
            int(row["Количество обучающихся"]),
        ),
        axis=1,
    )

    wide = (
        tmp.pivot_table(
            index=["Тип области", "Название области", "Название шкалы", "Количество обучающихся"],
            columns="Название уровня",
            values="Ячейка",
            aggfunc="first",
            fill_value="0 (0%)",
        )
        .reset_index()
    )

    ordered_level_columns = [level_ru.get(level_key, level_key) for level_key in level_order]
    for col in ordered_level_columns:
        if col not in wide.columns:
            wide[col] = "0 (0%)"

    wide = wide[
        ["Тип области", "Название области", "Название шкалы", "Количество обучающихся"]
        + ordered_level_columns
    ]

    return wide


def process_data(
    df: pd.DataFrame,
    scales_config: Dict[str, Dict],
    level_order: List[str],
    level_ru: Dict[str, str],
    answer_weights: Dict[int, int],
) -> pd.DataFrame:
    """
    Основная функция обработки результатов теста.

    Параметры:
    - df: исходный DataFrame с ответами
    - scales_config: конфиг шкал из SettingsDialog
    - level_order: порядок уровней
    - level_ru: русские названия уровней
    - answer_weights: веса ответов

    Возвращает:
    - DataFrame с индивидуальными результатами
    - сводки лежат в df.attrs["сводки"]
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("process_data ожидает pandas.DataFrame.")

    if "Группа" not in df.columns:
        raise KeyError("В исходном DataFrame отсутствует обязательная колонка 'Группа'.")

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
    # 2. Создаем числовые колонки по вопросам, где значение = вес ответа
    # ------------------------------------------------------------------
    weighted_question_columns: Dict[int, str] = {}

    for question_number, original_column in question_number_to_column.items():
        weighted_column_name = f"Вес ответа на вопрос {question_number}"
        df_result[weighted_column_name] = df_result[original_column].map(
            lambda x: _replace_answer_with_weight(x, answer_weights)
        )
        weighted_question_columns[question_number] = weighted_column_name

    # ------------------------------------------------------------------
    # 3. Считаем суммы и интерпретации по всем пользовательским шкалам
    # ------------------------------------------------------------------
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

        sum_column_name = f'Сумма баллов по шкале "{scale_title}"'
        level_code_column_name = f'Технический уровень по шкале "{scale_title}"'
        interpretation_column_name = f'Интерпретация по шкале "{scale_title}"'

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

    # ------------------------------------------------------------------
    # 4. Добавляем средние по группе и по колледжу
    #    (средние по годам удалены)
    # ------------------------------------------------------------------
    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)
        sum_column_name = f'Сумма баллов по шкале "{scale_title}"'

        mean_group_column_name = f'Средний балл по группе по шкале "{scale_title}"'
        mean_college_column_name = f'Средний балл по колледжу по шкале "{scale_title}"'

        df_result[mean_group_column_name] = (
            df_result.groupby("Группа")[sum_column_name].transform("mean")
        )
        df_result[mean_college_column_name] = df_result[sum_column_name].mean()

    # ------------------------------------------------------------------
    # 5. Формируем сводки по группам и по колледжу
    # ------------------------------------------------------------------
    long_parts: List[pd.DataFrame] = []

    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)
        level_code_column_name = f'Технический уровень по шкале "{scale_title}"'

        # Сводка по группам
        long_parts.append(
            _build_distribution_long(
                df=df_result,
                scope_type="Группа",
                scope_value_column="Группа",
                scale_name=scale_title,
                level_code_column=level_code_column_name,
                level_order=level_order,
                level_ru=level_ru,
            )
        )

        # Сводка по колледжу
        temp_df = df_result.copy()
        temp_df["Колледж"] = "Весь колледж"

        long_parts.append(
            _build_distribution_long(
                df=temp_df,
                scope_type="Колледж",
                scope_value_column="Колледж",
                scale_name=scale_title,
                level_code_column=level_code_column_name,
                level_order=level_order,
                level_ru=level_ru,
            )
        )

    summary_long = pd.concat(long_parts, ignore_index=True) if long_parts else pd.DataFrame()
    summary_wide = _build_distribution_wide(
        df_long=summary_long,
        level_order=level_order,
        level_ru=level_ru,
    )

    # ------------------------------------------------------------------
    # 6. Складываем сводки в attrs
    # ------------------------------------------------------------------
    df_result.attrs["сводки"] = {
        "длинная_таблица": summary_long,
        "широкая_таблица": summary_wide,
        "порядок_уровней": level_order,
        "русские_названия_уровней": level_ru,
        "конфигурация_шкал": scales_config,
        "веса_ответов": answer_weights,
    }

    return df_result