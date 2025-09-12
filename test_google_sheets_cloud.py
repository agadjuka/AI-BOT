#!/usr/bin/env python3
"""
Скрипт для тестирования Google Sheets подключения в облачной среде
"""
import os
import json
from services.google_sheets_service import GoogleSheetsService
from config.settings import BotConfig

def test_google_sheets_connection():
    """Тестирует подключение к Google Sheets"""
    print("🧪 Тестирование Google Sheets подключения...")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("🔍 Проверка переменных окружения:")
    print(f"  - GOOGLE_APPLICATION_CREDENTIALS_JSON: {'✅ Установлена' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON') else '❌ Не установлена'}")
    
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
        try:
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            credentials_info = json.loads(credentials_json)
            print(f"  - JSON валиден: ✅")
            print(f"  - Project ID: {credentials_info.get('project_id', 'Не найден')}")
            print(f"  - Client Email: {credentials_info.get('client_email', 'Не найден')}")
        except Exception as e:
            print(f"  - JSON невалиден: ❌ {e}")
    
    print()
    
    # Инициализируем конфигурацию
    config = BotConfig()
    print("🔍 Конфигурация Google Sheets:")
    print(f"  - Credentials path: {config.GOOGLE_SHEETS_CREDENTIALS}")
    print(f"  - Spreadsheet ID: {config.GOOGLE_SHEETS_SPREADSHEET_ID}")
    print(f"  - Worksheet name: {config.GOOGLE_SHEETS_WORKSHEET_NAME}")
    print()
    
    # Создаем сервис
    print("🔧 Создание GoogleSheetsService...")
    try:
        service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        if service.is_available():
            print("✅ GoogleSheetsService создан и доступен")
            
            # Тестируем доступ к таблице
            print("🔍 Тестирование доступа к таблице...")
            try:
                # Пытаемся получить информацию о таблице
                spreadsheet = service.service.spreadsheets().get(
                    spreadsheetId=config.GOOGLE_SHEETS_SPREADSHEET_ID
                ).execute()
                
                print("✅ Доступ к таблице успешен")
                print(f"  - Название таблицы: {spreadsheet.get('properties', {}).get('title', 'Неизвестно')}")
                print(f"  - Количество листов: {len(spreadsheet.get('sheets', []))}")
                
                # Показываем листы
                sheets = spreadsheet.get('sheets', [])
                if sheets:
                    print("  - Листы:")
                    for sheet in sheets:
                        sheet_props = sheet.get('properties', {})
                        print(f"    * {sheet_props.get('title', 'Без названия')} (ID: {sheet_props.get('sheetId', 'N/A')})")
                
            except Exception as e:
                print(f"❌ Ошибка доступа к таблице: {e}")
                print("💡 Проверьте:")
                print("  1. Правильность Spreadsheet ID")
                print("  2. Права доступа сервисного аккаунта к таблице")
                print("  3. Включен ли Google Sheets API")
                
        else:
            print("❌ GoogleSheetsService недоступен")
            print("💡 Проверьте настройки credentials")
            
    except Exception as e:
        print(f"❌ Ошибка создания GoogleSheetsService: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 50)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    test_google_sheets_connection()
