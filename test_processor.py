# -*- coding: utf-8 -*-
"""
Тест для проверки новой логики процессора.
Генерирует тестовые данные и проверяет обработку.
"""
import pandas as pd
import random
from datetime import datetime, timedelta
from core.processor import process_data

# === Конфигурация теста ===
ANSWER_WEIGHTS = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}

SCALES_CONFIG = {
    "Цинизм": {
        "title_ru": "Цинизм",
        "qnums": [1, 2, 3, 4, 5, 6, 7],
        "bounds": {
            "low_max": 25,
            "mid_low_min": 26,
            "mid_low_max": 40,
            "mid_high_min": 41,
            "mid_high_max": 65,
            "high_min": 66,
            "high_max": 200
        }
    },
    "Агрессивность": {
        "title_ru": "Агрессивность",
        "qnums": [8, 9, 10, 11, 12],
        "bounds": {
            "low_max": 25,
            "mid_low_min": 26,
            "mid_low_max": 40,
            "mid_high_min": 41,
            "mid_high_max": 65,
            "high_min": 66,
            "high_max": 200
        }
    },
    "Враждебность": {
        "title_ru": "Враждебность",
        "qnums": [13, 14, 15, 16, 17],
        "bounds": {
            "low_max": 25,
            "mid_low_min": 26,
            "mid_low_max": 40,
            "mid_high_min": 41,
            "mid_high_max": 65,
            "high_min": 66,
            "high_max": 200
        }
    }
}

LEVEL_ORDER = ["low", "mid_low", "mid_high", "high"]
LEVEL_RU = {
    "low": "Низкий",
    "mid_low": "Средний с тенденцией к низкому",
    "mid_high": "Средний с тенденцией к высокому",
    "high": "Высокий"
}

# === Генерация тестовых данных ===
num_respondents = 50
courses = [1, 2, 3, 4]
groups = ["ИНБ-101", "ИНБ-102", "МКН-201", "ПИЖ-301", "ЮРБ-401"]

data = []
start_date = datetime(2025, 9, 1)

for i in range(num_respondents):
    date = start_date + timedelta(days=random.randint(0, 150))
    fio = f"Респондент {i+1}"
    course = random.choice(courses)
    group = random.choice(groups)
    
    # Генерируем ответы на 17 вопросов (формат: "1) Вопрос" как в ТЗ)
    answers = {}
    for q in range(1, 18):
        answers[f"{q}) Вопрос {q}"] = random.randint(1, 6)
    
    row = {
        "Дата": date.strftime("%Y-%m-%d"),
        "ФИО": fio,
        "Группа": group,
        "Курс": course,
        **answers
    }
    data.append(row)

df = pd.DataFrame(data)

print("=" * 60)
print("ТЕСТОВЫЕ ДАННЫЕ")
print("=" * 60)
print(f"Количество респондентов: {len(df)}")
print(f"Колонки: {list(df.columns)}")
print(f"\nПервые 3 строки:")
print(df.head(3))
print()

# === Запуск процессора ===
print("=" * 60)
print("ЗАПУСК ПРОЦЕССОРА")
print("=" * 60)

try:
    table_df, charts_data, summary_data = process_data(
        df,
        SCALES_CONFIG,
        LEVEL_ORDER,
        LEVEL_RU,
        ANSWER_WEIGHTS
    )
    
    print("\n✅ Обработка успешна!")
    
    # === Проверка table_df ===
    print("\n" + "=" * 60)
    print("TABLE_DF (данные для таблицы)")
    print("=" * 60)
    print(f"Размер: {table_df.shape}")
    print(f"Колонки: {list(table_df.columns)}")
    print(f"\nПервые 3 строки:")
    print(table_df.head(3))
    
    # === Проверка charts_data ===
    print("\n" + "=" * 60)
    print("CHARTS_DATA (данные для графиков)")
    print("=" * 60)
    for key, value in charts_data.items():
        if isinstance(value, pd.DataFrame):
            print(f"\n{key}: {value.shape}")
            if not value.empty:
                print(f"Колонки: {list(value.columns)}")
        else:
            print(f"\n{key}: {type(value)}")
    
    # === Проверка summary_data ===
    print("\n" + "=" * 60)
    print("SUMMARY_DATA (сводные таблицы)")
    print("=" * 60)
    for key, value in summary_data.items():
        if isinstance(value, dict):
            print(f"\n{key}: {len(value)} групп/курсов")
            for name, data in list(value.items())[:2]:  # Первые 2
                if isinstance(data, dict) and "table" in data:
                    print(f"  - {name}: {data['table'].shape}, респондентов: {data['total_respondents']}")
        elif isinstance(value, list):
            print(f"\n{key}: {len(value)} элементов")
        else:
            print(f"\n{key}: {type(value)}")
    
    # === Проверка экспорта Excel ===
    print("\n" + "=" * 60)
    print("ЭКСПОРТ В EXCEL")
    print("=" * 60)
    
    from ui.components.results_widget import export_to_excel_with_summary
    
    output_path = "test_output.xlsx"
    export_to_excel_with_summary(
        table_df=table_df,
        summary_data=summary_data,
        charts_data=charts_data,
        output_path=output_path
    )
    
    print(f"✅ Файл '{output_path}' успешно создан!")
    
    # Проверка созданных листов
    xl = pd.ExcelFile(output_path)
    print(f"Листы в файле: {xl.sheet_names}")
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЁН УСПЕШНО!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
