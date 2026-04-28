from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


# --- Дефолтный конфиг (если пользователь не сохранил свой) ---
DEFAULT_SCALES: Dict[str, Dict[str, Any]] = {
    "cyn": {
        "title_ru": "цинизма/у",
        "qnums": [1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 19, 20, 22],
        "bounds": {"low_max": 25, "mid_high_min": 40, "high_min": 65},
    },
    "agr": {
        "title_ru": "агрессивности",
        "qnums": [5, 14, 15, 16, 21, 23, 24, 26, 27],
        "bounds": {"low_max": 15, "mid_high_min": 30, "high_min": 45},
    },
    "hos": {
        "title_ru": "враждебности",
        "qnums": [8, 13, 17, 18, 25],
        "bounds": {"low_max": 10, "mid_high_min": 18, "high_min": 25},
    },
}

DEFAULT_LEVEL_ORDER = ["low", "mid_low", "mid_high", "high"]
DEFAULT_LEVEL_RU = {
    "low": "низкий показатель",
    "mid_low": "средний показатель с тенденцией к низкому",
    "mid_high": "средний показатель с тенденцией к высокому",
    "high": "высокий показатель",
}
DEFAULT_ANSWER_WEIGHTS = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}


_QCOL_RE = re.compile(r"^\s*(\d{1,3})\s*[\.\)]\s*")


def _extract_qnum(col: str) -> int | None:
    """Извлекает номер вопроса из названия колонки вида '1. ...' / '1) ...'."""
    if not isinstance(col, str):
        return None

    match = _QCOL_RE.match(col)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


def _answer_to_int(x: Any) -> int:
    """
    Преобразует ответ в номер варианта.
    Поддерживает:
    - '1 - никогда'
    - '2'
    - int / float
    - NaN -> 0
    """
    if pd.isna(x):
        return 0

    if isinstance(x, (int, np.integer)):
        return int(x)

    if isinstance(x, (float, np.floating)):
        return int(x)

    s = str(x).strip()
    match = re.match(r"^\s*(\d+)", s)
    if match:
        return int(match.group(1))

    return 0


def _mk_year(series: pd.Series) -> pd.Series:
    """Пытается извлечь год из даты/строки."""
    dt = pd.to_datetime(series, errors="coerce")
    year = dt.dt.year.astype("Int64")

    out = year.astype(str)
    mask_bad = dt.isna()

    if mask_bad.any():
        out.loc[mask_bad] = series.astype(str).str.split("-", n=1).str[0].loc[mask_bad]

    return out


def _format_count_pct(count: int, n: int) -> str:
    pct = 0 if n == 0 else int(round(count / n * 100))
    return f"{count} ({pct}%)"


def _distribution_long(
    df: pd.DataFrame,
    scale_name: str,
    level_code_col: str,
    scope_type: str,
    scope_value_col: str,
    level_order: list[str],
) -> pd.DataFrame:
    """Tidy/long распределение уровней по области группировки."""
    rows: list[dict[str, Any]] = []

    for scope_value, sub in df.groupby(scope_value_col, dropna=False):
        n = len(sub)
        vc = sub[level_code_col].value_counts(dropna=False).to_dict()

        for code in level_order:
            count = int(vc.get(code, 0))
            pct = 0.0 if n == 0 else (count / n * 100.0)

            rows.append(
                {
                    "scope_type": scope_type,
                    "scope_value": str(scope_value),
                    "scale": scale_name,
                    "level_code": code,
                    "count": count,
                    "percent": pct,
                    "n": n,
                }
            )

    return pd.DataFrame(rows)


def _distribution_wide(df_long: pd.DataFrame, level_order: list[str]) -> pd.DataFrame:
    """Pivot в широкую таблицу по уровням."""
    if df_long.empty:
        return pd.DataFrame(
            columns=["scope_type", "scope_value", "scale", "n", *level_order]
        )

    tmp = df_long.copy()
    tmp["cell"] = tmp.apply(
        lambda r: _format_count_pct(int(r["count"]), int(r["n"])),
        axis=1,
    )

    wide = (
        tmp.pivot_table(
            index=["scope_type", "scope_value", "scale", "n"],
            columns="level_code",
            values="cell",
            aggfunc="first",
            fill_value="0 (0%)",
        )
        .reset_index()
    )

    for code in level_order:
        if code not in wide.columns:
            wide[code] = "0 (0%)"

    return wide[["scope_type", "scope_value", "scale", "n", *level_order]]


def _normalize_config(config: dict[str, Any] | None) -> tuple[dict, list[str], dict, dict[int, int]]:
    """
    Приводит конфиг к единому виду.

    На входе может быть:
    - None -> используем дефолт
    - config из MainWindow / SettingsWidget
    """
    if not config:
        return (
            DEFAULT_SCALES,
            DEFAULT_LEVEL_ORDER,
            DEFAULT_LEVEL_RU,
            DEFAULT_ANSWER_WEIGHTS,
        )

    scales = config.get("scales") or DEFAULT_SCALES
    level_order = config.get("level_order") or DEFAULT_LEVEL_ORDER
    levels = config.get("levels") or DEFAULT_LEVEL_RU
    answer_weights_raw = config.get("answer_weights") or DEFAULT_ANSWER_WEIGHTS

    answer_weights: dict[int, int] = {}
    for key, value in answer_weights_raw.items():
        try:
            answer_weights[int(key)] = int(value)
        except (TypeError, ValueError):
            continue

    if not answer_weights:
        answer_weights = DEFAULT_ANSWER_WEIGHTS.copy()

    return scales, list(level_order), levels, answer_weights


def _answer_to_weight(x: Any, answer_weights: dict[int, int]) -> float:
    """Преобразует сырой ответ в вес согласно пользовательской таблице весов."""
    answer_number = _answer_to_int(x)
    if answer_number == 0:
        return np.nan
    return float(answer_weights.get(answer_number, answer_number))


def _sorted_bounds(bounds: dict[str, Any], level_order: Iterable[str]) -> list[tuple[str, float | None, float | None]]:
    """
    Собирает границы уровня в список:
    [(level_code, min_value|None, max_value|None), ...]
    """
    result: list[tuple[str, float | None, float | None]] = []

    for level_code in level_order:
        min_key = f"{level_code}_min"
        max_key = f"{level_code}_max"

        min_value = bounds.get(min_key)
        max_value = bounds.get(max_key)

        try:
            min_value = float(min_value) if min_value is not None else None
        except (TypeError, ValueError):
            min_value = None

        try:
            max_value = float(max_value) if max_value is not None else None
        except (TypeError, ValueError):
            max_value = None

        result.append((level_code, min_value, max_value))

    return result


def _interpret_sum(
    total: float,
    bounds: dict[str, Any],
    level_order: list[str],
    level_ru: dict[str, str],
    scale_title: str,
) -> Tuple[str, str]:
    """
    Универсальная интерпретация суммы по пользовательским границам.

    Поддерживает:
    - диапазон min/max
    - только max
    - только min
    """
    if pd.isna(total):
        return "", ""

    total = float(total)
    normalized_bounds = _sorted_bounds(bounds, level_order)

    matched_code: str | None = None

    for level_code, min_value, max_value in normalized_bounds:
        min_ok = True if min_value is None else total >= min_value
        max_ok = True if max_value is None else total <= max_value

        if min_ok and max_ok:
            matched_code = level_code
            break

    # Фолбэк на случай кривой конфигурации:
    if matched_code is None and normalized_bounds:
        # Берём последний уровень, для которого пройдена нижняя граница.
        for level_code, min_value, _ in reversed(normalized_bounds):
            if min_value is not None and total >= min_value:
                matched_code = level_code
                break

        # Если и это не сработало, берём первый уровень.
        if matched_code is None:
            matched_code = normalized_bounds[0][0]

    if matched_code is None:
        return "", ""

    level_name = level_ru.get(matched_code, matched_code)
    return matched_code, f"{level_name} {scale_title}"


def process_data(df: pd.DataFrame, config: dict[str, Any] | None = None) -> pd.DataFrame:
    """
    Обрабатывает Excel-таблицу по пользовательскому конфигу.

    Ожидает:
    - колонку 'Группа'
    - колонку 'Время создания'
    - вопросы вида '1. ...' или '1) ...'
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("process_data ожидает pandas DataFrame (df).")

    scales, level_order, level_ru, answer_weights = _normalize_config(config)
    df0 = df.copy()

    qnum_to_col: Dict[int, str] = {}
    for col in df0.columns:
        qn = _extract_qnum(col)
        if qn is not None:
            qnum_to_col[qn] = col

    if "Группа" not in df0.columns:
        raise KeyError("В df нет обязательной колонки 'Группа'.")

    if "Время создания" not in df0.columns:
        raise KeyError("В df нет обязательной колонки 'Время создания'.")

    df0["year"] = _mk_year(df0["Время создания"])

    # Сырые ответы -> веса
    for qn, col in qnum_to_col.items():
        df0[f"q{qn:03d}_weight"] = df0[col].map(
            lambda value: _answer_to_weight(value, answer_weights)
        ).astype("Float64")

    summary_parts: list[pd.DataFrame] = []

    for index, (scale_key, scale_cfg) in enumerate(scales.items(), start=1):
        scale_title = scale_cfg.get("title_ru") or str(scale_key)
        qnums = scale_cfg.get("qnums") or []
        bounds = scale_cfg.get("bounds") or {}

        if not qnums:
            raise ValueError(f"У шкалы '{scale_title}' не указаны номера вопросов.")

        qcols = [f"q{int(qn):03d}_weight" for qn in qnums if f"q{int(qn):03d}_weight" in df0.columns]

        if len(qcols) != len(qnums):
            missing = sorted(set(int(q) for q in qnums) - {int(col[1:4]) for col in qcols})
            raise KeyError(
                f"Не найдены колонки для вопросов шкалы '{scale_title}': {missing}. "
                f"Проверьте названия вопросов в Excel."
            )

        # Используем технические имена колонок, чтобы не было проблем с русским текстом
        # в последующей логике, но рядом сохраняем и человекочитаемые названия.
        sum_col = f"scale_{index}_sum"
        level_code_col = f"scale_{index}_level_code"
        level_text_col = f"scale_{index}_level"

        df0[sum_col] = df0[qcols].sum(axis=1, min_count=len(qcols))

        interpreted = df0[sum_col].map(
            lambda total: _interpret_sum(
                total=total,
                bounds=bounds,
                level_order=level_order,
                level_ru=level_ru,
                scale_title=scale_title,
            )
        )

        df0[level_code_col] = interpreted.map(lambda pair: pair[0])
        df0[level_text_col] = interpreted.map(lambda pair: pair[1])

        # Дублируем в человекочитаемые колонки результата.
        readable_sum_col = f"{scale_title} — сумма"
        readable_level_col = f"{scale_title} — уровень"
        readable_group_mean_col = f"{scale_title} — среднее по группе"
        readable_year_mean_col = f"{scale_title} — среднее по году"
        readable_college_mean_col = f"{scale_title} — среднее по колледжу"

        df0[readable_sum_col] = df0[sum_col]
        df0[readable_level_col] = df0[level_text_col]
        df0[readable_group_mean_col] = df0.groupby("Группа")[sum_col].transform("mean")
        df0[readable_year_mean_col] = df0.groupby("year")[sum_col].transform("mean")
        df0[readable_college_mean_col] = df0[sum_col].mean()

        summary_parts.append(
            _distribution_long(
                df=df0,
                scale_name=scale_title,
                level_code_col=level_code_col,
                scope_type="group",
                scope_value_col="Группа",
                level_order=level_order,
            )
        )

        summary_parts.append(
            _distribution_long(
                df=df0,
                scale_name=scale_title,
                level_code_col=level_code_col,
                scope_type="year",
                scope_value_col="year",
                level_order=level_order,
            )
        )

        tmp = df0.copy()
        tmp["_college"] = "college"
        summary_parts.append(
            _distribution_long(
                df=tmp,
                scale_name=scale_title,
                level_code_col=level_code_col,
                scope_type="college",
                scope_value_col="_college",
                level_order=level_order,
            )
        )

    df_long = pd.concat(summary_parts, ignore_index=True) if summary_parts else pd.DataFrame()
    df_wide = _distribution_wide(df_long, level_order)

    df0.attrs["summaries"] = {
        "long": df_long,
        "wide": df_wide,
        "level_order": level_order,
        "level_ru": level_ru,
        "scales": scales,
        "answer_weights": answer_weights,
    }

    return df0
