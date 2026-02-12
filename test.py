import pandas as pd
import random
from datetime import datetime, timedelta

data = []
start_date = datetime(2025, 9, 1)
groups = ["ПМИ", "МКН", "ПИЖ", "ФИТ", "БИО"]

for i in range(100):
    date = start_date + timedelta(days=random.randint(0, 150))
    fio = f"Студент{i+1} Фамилия{i+1}"
    course = random.randint(1, 4)
    group = random.choice(groups)
    answers = [random.randint(1, 5) for _ in range(10)]
    row = [date.strftime("%Y-%m-%d"), fio, course, group] + answers
    data.append(row)

df = pd.DataFrame(data, columns=["Дата", "ФИО", "Курс", "Группа"] + [f"Вопрос {i}" for i in range(1, 11)])
df.to_excel("test_data_100.xlsx", index=False)
print("✅ Файл 'test_data_100.xlsx' создан!")