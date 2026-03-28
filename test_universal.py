# -*- coding: utf-8 -*-
"""
Тест для проверки универсальности процессора.
Проверяет 4 комбинации:
1. Есть и Группа, и Курс
2. Только Группа
3. Только Курс
4. Нет ни Группы, ни Курса
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
        "qnums": [1, 2, 3, 4, 5],
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
        "qnums": [6, 7, 8, 9, 10],
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


def generate_data(num_respondents=20, has_group=True, has_course=True):
    """Генерирует тестовые данные с указанными колонками"""
    groups = ["ИНБ-101", "МКН-201", "ПИЖ-301"]
    courses = [1, 2, 3]
    
    data = []
    start_date = datetime(2025, 9, 1)
    
    for i in range(num_respondents):
        date = start_date + timedelta(days=random.randint(0, 150))
        fio = f"Респондент {i+1}"
        
        row = {
            "Дата": date.strftime("%Y-%m-%d"),
            "ФИО": fio,
        }
        
        if has_group:
            row["Группа"] = random.choice(groups)
        
        if has_course:
            row["Курс"] = random.choice(courses)
        
        # Генерируем ответы на 10 вопросов
        for q in range(1, 11):
            row[f"{q}) Вопрос {q}"] = random.randint(1, 6)
        
        data.append(row)
    
    return pd.DataFrame(data)


def test_case(name, df, has_group, has_course):
    """Тестирует одну комбинацию"""
    print(f"\n{'='*60}")
    print(f"ТЕСТ: {name}")
    print(f"{'='*60}")
    print(f"Колонки: {list(df.columns)}")
    print(f"has_group={has_group}, has_course={has_course}")
    
    try:
        table_df, charts_data, summary_data = process_data(
            df,
            SCALES_CONFIG,
            LEVEL_ORDER,
            LEVEL_RU,
            ANSWER_WEIGHTS
        )
        
        print(f"✅ Обработка успешна!")
        print(f"   table_df: {table_df.shape}")
        print(f"   has_group в summary: {summary_data.get('has_group')}")
        print(f"   has_course в summary: {summary_data.get('has_course')}")
        
        # Проверка экспорта
        from ui.components.results_widget import export_to_excel_with_summary
        
        output_path = f"test_output_{name.replace(' ', '_').lower()}.xlsx"
        export_to_excel_with_summary(
            table_df=table_df,
            summary_data=summary_data,
            charts_data=charts_data,
            output_path=output_path
        )
        
        # Проверка листов
        xl = pd.ExcelFile(output_path)
        print(f"   Листы в Excel: {xl.sheet_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


# === Запуск тестов ===
print("="*60)
print("ТЕСТИРОВАНИЕ УНИВЕРСАЛЬНОСТИ ПРОЦЕССОРА")
print("="*60)

results = []

# Тест 1: Есть и Группа, и Курс
df1 = generate_data(20, has_group=True, has_course=True)
results.append(("Группа + Курс", test_case("Группа + Курс", df1, True, True)))

# Тест 2: Только Группа
df2 = generate_data(20, has_group=True, has_course=False)
results.append(("Только Группа", test_case("Только Группа", df2, True, False)))

# Тест 3: Только Курс
df3 = generate_data(20, has_group=False, has_course=True)
results.append(("Только Курс", test_case("Только Курс", df3, False, True)))

# Тест 4: Нет ни Группы, ни Курса
df4 = generate_data(20, has_group=False, has_course=False)
results.append(("Без групп и курсов", test_case("Без групп и курсов", df4, False, False)))

# === Итоги ===
print(f"\n{'='*60}")
print("ИТОГИ ТЕСТИРОВАНИЯ")
print(f"{'='*60}")

for name, passed in results:
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {name}")

all_passed = all(passed for _, passed in results)
print(f"\n{'='*60}")
if all_passed:
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
else:
    print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
print(f"{'='*60}")
