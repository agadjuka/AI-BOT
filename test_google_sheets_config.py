#!/usr/bin/env python3
"""
Тестовый скрипт для проверки конфигурации Google Sheets
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import BotConfig
from google_sheets_handler import validate_google_sheets_config, get_google_sheets_ingredients
from services.google_sheets_service import GoogleSheetsService

def test_configuration():
    """Тестирует конфигурацию Google Sheets"""
    print("🔍 Проверка конфигурации Google Sheets...")
    print("=" * 50)
    
    # Проверяем настройки
    config = BotConfig()
    print(f"📁 Credentials path: {config.GOOGLE_SHEETS_CREDENTIALS}")
    print(f"📊 Spreadsheet ID: {config.GOOGLE_SHEETS_SPREADSHEET_ID}")
    print(f"📋 Worksheet name: {config.GOOGLE_SHEETS_WORKSHEET_NAME}")
    print(f"🥬 Ingredient list: {'Настроен' if config.INGREDIENT_LIST else 'Не настроен'}")
    
    print("\n" + "=" * 50)
    
    # Проверяем валидность конфигурации
    is_valid, message = validate_google_sheets_config()
    print(f"✅ Конфигурация корректна: {is_valid}")
    print(f"💬 Сообщение: {message}")
    
    print("\n" + "=" * 50)
    
    # Проверяем загрузку ингредиентов
    print("🥬 Проверка загрузки ингредиентов...")
    ingredients = get_google_sheets_ingredients()
    print(f"📊 Загружено ингредиентов: {len(ingredients)}")
    
    if ingredients:
        print("🔍 Примеры ингредиентов:")
        for i, (name, id) in enumerate(list(ingredients.items())[:5]):
            print(f"  {i+1}. {name} -> {id}")
        if len(ingredients) > 5:
            print(f"  ... и еще {len(ingredients) - 5} ингредиентов")
    
    print("\n" + "=" * 50)
    
    # Проверяем Google Sheets сервис
    print("📊 Проверка Google Sheets сервиса...")
    service = GoogleSheetsService(
        credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
        spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
    )
    
    is_available = service.is_available()
    print(f"✅ Сервис доступен: {is_available}")
    
    if not is_available:
        print("💡 Для активации сервиса:")
        print("   1. Создайте файл credentials.json")
        print("   2. Установите ID таблицы в настройках")
        print("   3. Добавьте список ингредиентов")
    
    print("\n" + "=" * 50)
    print("🎉 Проверка завершена!")

if __name__ == "__main__":
    test_configuration()
