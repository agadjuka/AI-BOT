# google_sheets_handler.py

import json
from config.settings import BotConfig

def get_google_sheets_ingredients() -> dict:
    """
    Загружает список ингредиентов для сопоставления с Google Sheets.
    Возвращает словарь: {id: {'name': name}}
    """
    config = BotConfig()
    
    # Получаем список ингредиентов из конфигурации
    ingredient_list = config.ingredient_config.get_ingredient_list() or {}
    
    if not ingredient_list:
        print("⚠️ Список ингредиентов для Google Sheets не настроен.")
        print("💡 Добавьте готовый список ингредиентов в конфигурацию.")
        return {}
    
    # Преобразуем формат из {name: id} в {id: {'name': name}}
    ingredient_dictionary = {}
    for name, ingredient_id in ingredient_list.items():
        ingredient_dictionary[ingredient_id] = {'name': name}
    
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
    
    if not config.ingredient_config.get_ingredient_list():
        return False, "Не настроен список ингредиентов для сопоставления"
    
    return True, "Конфигурация Google Sheets корректна"
