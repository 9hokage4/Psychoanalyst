import pandas as pd
import random
from datetime import datetime, timedelta

# === Генерация данных ===
num_students = 100
courses = [1, 2, 3, 4]
directions = ["ПМИ", "МКН", "ПИЖ", "ФИТ", "БИО"]
questions = [f"Вопрос {i}" for i in range(1, 11)]

data = []
start_date = datetime(2025, 9, 1)

for i in range(num_students):
    date = start_date + timedelta(days=random.randint(0, 150))
    fio = f"Студент{i+1} Фамилия{i+1}"
    course = random.choice(courses)
    direction = random.choice(directions)
    group = f"{direction}-24-{course}"
    answers = [random.randint(1, 5) for _ in range(10)]
    
    # Расчёт риска
    total_score = sum(answers)
    risk_percent = round((total_score / 50) * 100, 1)
    if risk_percent < 50:
        risk_level = "Низкий риск"
    elif risk_percent < 70:
        risk_level = "Средний риск"
    else:
        risk_level = "Высокий риск"
    
    row = [date.strftime("%Y-%m-%d"), fio, course, direction, group, risk_percent, risk_level] + answers
    data.append(row)

columns = ["Дата", "ФИО", "Курс", "Направление", "Группа", "% риска", "Risk Level"] + questions
df_all = pd.DataFrame(data, columns=columns)

# === Листы ===
rows_course = []
for course in sorted(df_all["Курс"].unique()):
    rows_course.append([f"{course} курс"] + [""] * (len(columns) - 1))
    for _, row in df_all[df_all["Курс"] == course].iterrows():
        rows_course.append(row.tolist())
    rows_course.append([""] * len(columns))

df_by_course = pd.DataFrame(rows_course, columns=columns)

rows_dir = []
for direction in sorted(df_all["Направление"].unique()):
    rows_dir.append([direction] + [""] * (len(columns) - 1))
    for _, row in df_all[df_all["Направление"] == direction].iterrows():
        rows_dir.append(row.tolist())
    rows_dir.append([""] * len(columns))

df_by_dir = pd.DataFrame(rows_dir, columns=columns)

# === Сохранение ===
with pd.ExcelWriter("processed_data.xlsx", engine="openpyxl") as writer:
    df_all.to_excel(writer, sheet_name="Все", index=False)
    df_by_course.to_excel(writer, sheet_name="По курсу", index=False)
    df_by_dir.to_excel(writer, sheet_name="По направлению", index=False)

print("✅ Файл 'processed_data.xlsx' создан!")