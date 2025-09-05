# google_sheets_handler.py

import json
from config.settings import BotConfig

def get_google_sheets_ingredients() -> dict:
    """
    Загружает список ингредиентов для сопоставления с Google Sheets.
    Возвращает словарь: {'название ингредиента в нижнем регистре': id}
    """
    config = BotConfig()
    
    # TODO: Загрузить готовый список ингредиентов из конфигурации
    # Пока возвращаем пустой словарь, который будет заполнен позже
    ingredient_dictionary = config.INGREDIENT_LIST or {}
    
    if not ingredient_dictionary:
        print("⚠️ Список ингредиентов для Google Sheets не настроен.")
        print("💡 Добавьте готовый список ингредиентов в конфигурацию.")
        return {}
    
    print(f"✅ Загружено {len(ingredient_dictionary)} ингредиентов для Google Sheets.")
    return ingredient_dictionary

def validate_google_sheets_config() -> tuple[bool, str]:
    """
    Проверяет конфигурацию Google Sheets
    
    Returns:
        (is_valid, error_message)
    """
    config = BotConfig()
    
    if not config.GOOGLE_SHEETS_CREDENTIALS:
        return False, "Не настроен путь к файлу credentials для Google Sheets"
    
    if not config.GOOGLE_SHEETS_SPREADSHEET_ID:
        return False, "Не настроен ID таблицы Google Sheets"
    
    if not config.INGREDIENT_LIST:
        return False, "Не настроен список ингредиентов для сопоставления"
    
    return True, "Конфигурация Google Sheets корректна"
