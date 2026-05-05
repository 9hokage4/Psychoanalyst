# generate_test_data.py
import pandas as pd
import numpy as np
from datetime import datetime

np.random.seed(42)

NUM_RESPONDENTS = 200
QUESTIONS = 20
DATE = datetime.now().strftime("%d.%m.%Y")

WEIGHTS = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
SCALES = {
    "Шкала А": [1, 2, 3, 4, 5],
    "Шкала Б": [6, 7, 8, 9, 10],
    "Шкала В": [11, 12, 13, 14, 15],
    "Шкала Г": [16, 17, 18, 19, 20],
}

data_rows = []

for person_id in range(1, NUM_RESPONDENTS + 1):
    group_num = ((person_id - 1) // 20) + 1
    course_num = ((person_id - 1) % 5) + 1

    row = {
        "ФИО": f"Респондент {person_id}",
        "Дата": DATE,
        "Группа": f"Группа {group_num}",
        "Курс": f"Курс {course_num}",
    }

    if group_num <= 3:
        target_level = "low"
    elif group_num <= 6:
        target_level = "mid_low"
    else:
        target_level = "high"

    for q in range(1, QUESTIONS + 1):
        if target_level == "low":
            prob = [0.5, 0.3, 0.1, 0.05, 0.05]
        elif target_level == "mid_low":
            prob = [0.05, 0.2, 0.5, 0.2, 0.05]
        else:
            prob = [0.05, 0.05, 0.1, 0.3, 0.5]

        answer = np.random.choice([1, 2, 3, 4, 5], p=prob)
        row[f"{q}) Вопрос {q}"] = answer

    data_rows.append(row)

df = pd.DataFrame(data_rows)
df.to_excel("test_data.xlsx", index=False, engine="openpyxl")
print("✅ test_data.xlsx создан.")