"""
Пример конфигурации для Google Sheets
Скопируйте эти настройки в config/settings.py
"""

# Google Sheets settings
GOOGLE_SHEETS_CREDENTIALS = "google_sheets_credentials.json"  # Путь к файлу credentials
GOOGLE_SHEETS_SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"  # ID таблицы Google Sheets
GOOGLE_SHEETS_WORKSHEET_NAME = "Receipts"  # Название листа

# Пример списка ингредиентов для сопоставления
INGREDIENT_LIST = {
    # Овощи
    "tomato": "tomato_001",
    "cucumber": "cucumber_002", 
    "carrot": "carrot_003",
    "onion": "onion_004",
    "potato": "potato_005",
    "cabbage": "cabbage_006",
    "lettuce": "lettuce_007",
    "pepper": "pepper_008",
    "eggplant": "eggplant_009",
    "zucchini": "zucchini_010",
    
    # Фрукты
    "apple": "apple_011",
    "banana": "banana_012",
    "orange": "orange_013",
    "lemon": "lemon_014",
    "grape": "grape_015",
    "strawberry": "strawberry_016",
    
    # Мясо и рыба
    "chicken": "chicken_017",
    "beef": "beef_018",
    "pork": "pork_019",
    "fish": "fish_020",
    "salmon": "salmon_021",
    "tuna": "tuna_022",
    
    # Молочные продукты
    "milk": "milk_023",
    "cheese": "cheese_024",
    "yogurt": "yogurt_025",
    "butter": "butter_026",
    "cream": "cream_027",
    
    # Хлеб и зерновые
    "bread": "bread_028",
    "rice": "rice_029",
    "pasta": "pasta_030",
    "flour": "flour_031",
    "oats": "oats_032",
    
    # Специи и приправы
    "salt": "salt_033",
    "pepper": "pepper_034",
    "garlic": "garlic_035",
    "ginger": "ginger_036",
    "basil": "basil_037",
    "oregano": "oregano_038",
    
    # Напитки
    "water": "water_039",
    "juice": "juice_040",
    "coffee": "coffee_041",
    "tea": "tea_042",
    "soda": "soda_043",
    
    # Добавьте больше ингредиентов по необходимости
}

# Инструкции по настройке:
"""
1. Создайте Google Cloud проект и включите Google Sheets API
2. Создайте Service Account и скачайте JSON файл credentials
3. Скопируйте файл в корень проекта как 'google_sheets_credentials.json'
4. Создайте Google Таблицу и скопируйте её ID
5. Предоставьте доступ Service Account к таблице
6. Обновите настройки в config/settings.py:
   - GOOGLE_SHEETS_CREDENTIALS = "google_sheets_credentials.json"
   - GOOGLE_SHEETS_SPREADSHEET_ID = "ваш_id_таблицы"
   - INGREDIENT_LIST = ваш_список_ингредиентов
"""
