from __future__ import annotations

import re
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# --- Конфиг шкал (по Кука–Медлей) ---

SCALES: Dict[str, Dict] = {
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

LEVEL_ORDER = ["low", "mid_low", "mid_high", "high"]
LEVEL_RU = {
    "low": "низкий показатель",
    "mid_low": "средний показатель с тенденцией к низкому",
    "mid_high": "средний показатель с тенденцией к высокому",
    "high": "высокий показатель",
}


# --- Вспомогательные функции ---

_QCOL_RE = re.compile(r"^\s*(\d{1,2})\s*[\.\)]\s*")  # "1. ..." или "1) ..."

def _extract_qnum(col: str) -> int | None:
    """Вернуть номер вопроса из названия колонки, если это вопрос."""
    if not isinstance(col, str):
        return None
    m = _QCOL_RE.match(col)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _answer_to_int(x) -> int:
    """
    Преобразует ответы вида '1 - никогда' -> 1.
    Также поддерживает уже числовые значения.
    """
    if pd.isna(x):
        return 0  # дальше решим, как обрабатывать пропуски
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        # если вдруг уже float
        return int(x)
    s = str(x).strip()
    # Берем первую группу цифр
    m = re.match(r"^\s*(\d+)", s)
    if m:
        return int(m.group(1))
    return 0


def _interpret_sum(scale_key: str, total: float, scales_config: dict = None, level_ru: dict = None) -> Tuple[str, str]:
    """
    Возвращает (level_code, level_text_ru_with_scale)
    Границы читаем так:
      low: <= low_max
      mid_low: (low_max, mid_high_min)
      mid_high: [mid_high_min, high_min)
      high: >= high_min
    """
    if scales_config is None:
        scales_config = SCALES
    if level_ru is None:
        level_ru = LEVEL_RU
        
    b = scales_config[scale_key]["bounds"]
    title_ru = scales_config[scale_key]["title_ru"]

    if pd.isna(total):
        return ("", "")

    total = float(total)
    if total >= b["high_min"]:
        code = "high"
    elif total >= b["mid_high_min"]:
        code = "mid_high"
    elif total > b["low_max"]:
        code = "mid_low"
    else:
        code = "low"

    text = f"{level_ru[code]} {title_ru}"
    return code, text


def _mk_year(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")  # все нераспарсенное -> NaT
    year = dt.dt.year.astype("Int64")

    # где распарсилось — берем год, где нет — пробуем старый split
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
    scale_key: str,
    group_cols: List[str],
    level_code_col: str,
    scope_type: str,
    scope_value_col: str,
) -> pd.DataFrame:
    """
    Делает tidy/long распределение по уровню:
    scope_type/scope_value/scale/level_code/count/percent/n
    """
    rows = []
    for scope_value, sub in df.groupby(scope_value_col, dropna=False):
        n = len(sub)
        vc = sub[level_code_col].value_counts(dropna=False).to_dict()
        for code in LEVEL_ORDER:
            c = int(vc.get(code, 0))
            pct = 0.0 if n == 0 else (c / n * 100.0)
            rows.append(
                {
                    "scope_type": scope_type,
                    "scope_value": str(scope_value),
                    "scale": scale_key,
                    "level_code": code,
                    "count": c,
                    "percent": pct,
                    "n": n,
                }
            )
    return pd.DataFrame(rows)


def _distribution_wide(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot в широкую таблицу: колонки = уровни, значения = 'count (pct%)'
    """
    tmp = df_long.copy()
    tmp["cell"] = tmp.apply(lambda r: _format_count_pct(int(r["count"]), int(r["n"])), axis=1)

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
    # гарантируем порядок колонок уровней
    for code in LEVEL_ORDER:
        if code not in wide.columns:
            wide[code] = "0 (0%)"
    wide = wide[["scope_type", "scope_value", "scale", "n"] + LEVEL_ORDER]
    return wide


# --- Основная функция ---

def process_data(df: pd.DataFrame, config: dict = None) -> pd.DataFrame:
    """
    Вход: датафрейм с колонками:
      - 'Время создания' (str/datetime)
      - 'Группа'
      - вопросы вида '1. ...' или '1) ...' с ответами '1 - никогда'..'6 - обычно'
      - config (optional): конфигурация с шкалами, уровнями и весами

    Выход: df_out (персональный уровень) + сводки в df_out.attrs["summaries"].
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("process_data ожидает pandas DataFrame (df).")

    # Используем конфигурацию из параметра или дефолтную
    if config:
        scales_config = config.get("scales", config.get("scales_config", {}))
        level_order = config.get("level_order", LEVEL_ORDER)
        level_ru = config.get("level_ru", LEVEL_RU)
        answer_weights = config.get("answer_weights", {})
    else:
        scales_config = SCALES
        level_order = LEVEL_ORDER
        level_ru = LEVEL_RU
        answer_weights = {}

    df0 = df.copy()

    # 1) Находим колонки вопросов и строим qnum -> colname
    qnum_to_col: Dict[int, str] = {}
    for col in df0.columns:
        qn = _extract_qnum(col)
        if qn is not None:
            qnum_to_col[qn] = col

    # 2) Базовые колонки
    if "Группа" not in df0.columns:
        raise KeyError("В df нет обязательной колонки 'Группа'.")
    if "Время создания" not in df0.columns:
        raise KeyError("В df нет обязательной колонки 'Время создания'.")

    df0["year"] = _mk_year(df0["Время создания"])

    # 3) Приводим ответы к int (только для нужных вопросов)
    #    (делаем отдельные числовые колонки, чтобы не портить исходные ответы)
    for qn, col in qnum_to_col.items():
        df0[f"q{qn:02d}"] = df0[col].map(_answer_to_int).astype("Float64")  # allow NaN

    # 4) Считаем суммы и интерпретации по шкалам
    for scale_key, cfg in scales_config.items():
        qcols = [f"q{qn:02d}" for qn in cfg["qnums"] if f"q{qn:02d}" in df0.columns]
        if len(qcols) != len(cfg["qnums"]):
            missing = sorted(set(cfg["qnums"]) - {int(c[1:]) for c in qcols})
            raise KeyError(
                f"Не найдены колонки для вопросов шкалы {scale_key}: {missing}. "
                f"Проверьте названия вопросов в Excel."
            )

        sum_col = f"{scale_key}_sum"
        level_code_col = f"{scale_key}_level_code"
        level_text_col = f"{scale_key}_level"

        # Если пропуски — можно либо запрещать, либо игнорировать.
        # Здесь: считаем сумму только если нет NaN; иначе оставляем NaN.
        df0[sum_col] = df0[qcols].sum(axis=1, min_count=len(qcols))

        interpreted = df0[sum_col].map(lambda x: _interpret_sum(scale_key, x, scales_config, level_ru))
        df0[level_code_col] = interpreted.map(lambda t: t[0])
        df0[level_text_col] = interpreted.map(lambda t: t[1])

    # 5) Средние "справа" по группе/году/колледжу (для каждой шкалы)
    for scale_key in scales_config.keys():
        sum_col = f"{scale_key}_sum"
        df0[f"{scale_key}_sum_group_mean"] = df0.groupby("Группа")[sum_col].transform("mean")
        df0[f"{scale_key}_sum_year_mean"] = df0.groupby("year")[sum_col].transform("mean")
        df0[f"{scale_key}_sum_college_mean"] = df0[sum_col].mean()

    # 6) Сводки распределений: group/year/college
    long_parts: List[pd.DataFrame] = []

    for scale_key in scales_config.keys():
        level_code_col = f"{scale_key}_level_code"

        # По группам
        long_parts.append(
            _distribution_long(
                df=df0,
                scale_key=scale_key,
                group_cols=["Группа"],
                level_code_col=level_code_col,
                scope_type="group",
                scope_value_col="Группа",
            )
        )
        # По годам
        long_parts.append(
            _distribution_long(
                df=df0,
                scale_key=scale_key,
                group_cols=["year"],
                level_code_col=level_code_col,
                scope_type="year",
                scope_value_col="year",
            )
        )
        # По колледжу (единая группа "college")
        tmp = df0.copy()
        tmp["_college"] = "college"
        long_parts.append(
            _distribution_long(
                df=tmp,
                scale_key=scale_key,
                group_cols=["_college"],
                level_code_col=level_code_col,
                scope_type="college",
                scope_value_col="_college",
            )
        )

    df_long = pd.concat(long_parts, ignore_index=True)
    df_wide = _distribution_wide(df_long)

    # 7) Складываем сводки в attrs (для экспорта в Excel/графиков)
    df0.attrs["summaries"] = {
        "long": df_long,
        "wide": df_wide,
        "level_order": level_order,
        "level_ru": level_ru,
        "scales": {k: {"title_ru": v["title_ru"], "qnums": v["qnums"], "bounds": v["bounds"]} for k, v in scales_config.items()},
    }

    return df0