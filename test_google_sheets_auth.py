#!/usr/bin/env python3
"""
Тест аутентификации Google Sheets
"""
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.google_sheets_service import GoogleSheetsService
from config.settings import BotConfig

def test_google_sheets_auth():
    """Тестирует аутентификацию Google Sheets"""
    print("🔍 Тестирование аутентификации Google Sheets...")
    
    # Создаем конфигурацию
    config = BotConfig()
    
    # Тестируем с ID таблицы из конфигурации
    test_sheet_id = config.GOOGLE_SHEETS_SPREADSHEET_ID
    print(f"🔍 Тестируем с ID таблицы: {test_sheet_id}")
    
    # Создаем сервис
    service = GoogleSheetsService(
        credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
        spreadsheet_id=test_sheet_id
    )
    
    # Проверяем, что сервис инициализирован
    if not service.is_available():
        print("❌ Сервис Google Sheets недоступен")
        return False
    
    print("✅ Сервис Google Sheets инициализирован успешно")
    
    # Пытаемся получить информацию о таблице
    try:
        result = service.service.spreadsheets().get(spreadsheetId=test_sheet_id).execute()
        sheet_title = result.get('properties', {}).get('title', 'Unknown')
        print(f"✅ Успешно получена информация о таблице: {sheet_title}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при получении информации о таблице: {e}")
        return False

if __name__ == "__main__":
    success = test_google_sheets_auth()
    if success:
        print("\n✅ Тест аутентификации прошел успешно!")
    else:
        print("\n❌ Тест аутентификации не прошел!")
        sys.exit(1)
