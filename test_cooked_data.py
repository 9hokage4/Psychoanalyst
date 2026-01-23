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
    # Группа: МКН-24-1 → направление + год + курс
    group = f"{direction}-24-{course}"
    answers = [random.randint(1, 5) for _ in range(10)]
    risk_percent = round((sum(answers) / 50) * 100, 1)
    
    row = [date.strftime("%Y-%m-%d"), fio, course, direction, group, risk_percent] + answers
    data.append(row)

# Столбцы: добавлено "Направление"
columns = ["Дата", "ФИО", "Курс", "Направление", "Группа", "% риска"] + questions
df_all = pd.DataFrame(data, columns=columns)

# === Лист "По курсу" ===
rows_course = []
for course in sorted(df_all["Курс"].unique()):
    rows_course.append([f"{course} курс"] + [""] * (len(columns) - 1))
    for _, row in df_all[df_all["Курс"] == course].iterrows():
        rows_course.append(row.tolist())
    rows_course.append([""] * len(columns))

df_by_course = pd.DataFrame(rows_course, columns=columns)

# === Лист "По направлению" ===
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