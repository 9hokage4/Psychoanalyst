# compute_expected.py
import pandas as pd
from pathlib import Path

# ---------- те же настройки ----------
WEIGHTS = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
SCALES = {
    "Шкала А": [1, 2, 3, 4, 5],
    "Шкала Б": [6, 7, 8, 9, 10],
    "Шкала В": [11, 12, 13, 14, 15],
    "Шкала Г": [16, 17, 18, 19, 20],
}
LEVEL_ORDER = ["low", "mid_low", "mid_high"]
LEVEL_RU = {"low": "Низкий", "mid_low": "Средний", "mid_high": "Высокий"}
LEVEL_BOUNDARIES = {"low": 12, "mid_low": 19, "mid_high": 25}  # max значения

def interpret_sum(total):
    if total <= LEVEL_BOUNDARIES["low"]:
        return ("low", f"Низкий ({int(total)} баллов)")
    elif total <= LEVEL_BOUNDARIES["mid_low"]:
        return ("mid_low", f"Средний ({int(total)} баллов)")
    else:
        return ("mid_high", f"Высокий ({int(total)} баллов)")

# ---------- загрузка данных ----------
df = pd.read_excel("test_data.xlsx")

# Рассчитываем суммы и уровни
for scale_name, qnums in SCALES.items():
    col_names = [f"{q}) Вопрос {q}" for q in qnums]
    # Применяем веса
    weighted = df[col_names].replace(WEIGHTS)
    sum_col = f"Сумма_{scale_name}"
    df[sum_col] = weighted.sum(axis=1)
    
    level_col = f"Уровень_{scale_name}"
    interp_col = f"Интерпретация_{scale_name}"
    
    # Определяем уровень
    levels = df[sum_col].apply(interpret_sum)
    df[level_col] = levels.apply(lambda x: x[0])
    df[interp_col] = levels.apply(lambda x: x[1])

# ---------- формируем ожидаемые сводки ----------
writer = pd.ExcelWriter("expected_results.xlsx", engine="openpyxl")

# 1. Средние баллы по шкалам
mean_rows = []
for scale_name in SCALES:
    sum_col = f"Сумма_{scale_name}"
    mean_rows.append({
        "Шкала": scale_name,
        "Средний балл": round(df[sum_col].mean(), 1),
        "Мин": int(df[sum_col].min()),
        "Макс": int(df[sum_col].max()),
    })
pd.DataFrame(mean_rows).to_excel(writer, sheet_name="Средние баллы", index=False)

# 2. Общее распределение уровней по шкалам
dist_rows = []
for scale_name in SCALES:
    level_col = f"Уровень_{scale_name}"
    counts = df[level_col].value_counts()
    total = len(df)
    for level_key in LEVEL_ORDER:
        cnt = int(counts.get(level_key, 0))
        dist_rows.append({
            "Шкала": scale_name,
            "Уровень": LEVEL_RU[level_key],
            "Количество": cnt,
            "Процент": round(cnt / total * 100, 1),
        })
pd.DataFrame(dist_rows).to_excel(writer, sheet_name="Распределение (общее)", index=False)

# 3. Распределение по группам (для каждой шкалы)
group_dist_rows = []
for scale_name in SCALES:
    level_col = f"Уровень_{scale_name}"
    for group_name, sub_df in df.groupby("Группа"):
        counts = sub_df[level_col].value_counts()
        total = len(sub_df)
        for level_key in LEVEL_ORDER:
            cnt = int(counts.get(level_key, 0))
            group_dist_rows.append({
                "Шкала": scale_name,
                "Группа": group_name,
                "Уровень": LEVEL_RU[level_key],
                "Количество": cnt,
                "Процент": round(cnt / total * 100, 1),
            })
pd.DataFrame(group_dist_rows).to_excel(writer, sheet_name="Распределение по группам", index=False)

# 4. Распределение по курсам
course_dist_rows = []
for scale_name in SCALES:
    level_col = f"Уровень_{scale_name}"
    for course_name, sub_df in df.groupby("Курс"):
        counts = sub_df[level_col].value_counts()
        total = len(sub_df)
        for level_key in LEVEL_ORDER:
            cnt = int(counts.get(level_key, 0))
            course_dist_rows.append({
                "Шкала": scale_name,
                "Курс": course_name,
                "Уровень": LEVEL_RU[level_key],
                "Количество": cnt,
                "Процент": round(cnt / total * 100, 1),
            })
pd.DataFrame(course_dist_rows).to_excel(writer, sheet_name="Распределение по курсам", index=False)

writer.close()
print("✅ expected_results.xlsx создан.")