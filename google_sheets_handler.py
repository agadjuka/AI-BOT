# google_sheets_handler.py

import json
from config.settings import BotConfig

def get_google_sheets_ingredients() -> dict:
    """
    DEPRECATED: Эта функция больше не используется.
    Ингредиенты теперь загружаются персонально для каждого пользователя из Firestore.
    Возвращает пустой словарь для обратной совместимости.
    """
    print("⚠️ get_google_sheets_ingredients() устарела - используйте персональные ингредиенты из Firestore")
    return {}

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
    
    # Ингредиенты теперь загружаются персонально из Firestore, поэтому эта проверка больше не нужна
    return True, "Конфигурация Google Sheets корректна"
