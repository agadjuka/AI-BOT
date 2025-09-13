#!/usr/bin/env python3
"""
Скрипт для тестирования credentials в облачной среде
"""
import os
import json
from services.google_sheets_service import GoogleSheetsService
from config.settings import BotConfig

def test_cloud_credentials():
    """Тестирует credentials в облачной среде"""
    print("🧪 Тестирование credentials в облачной среде...")
    print("=" * 60)
    
    # Проверяем переменные окружения
    print("🔍 Проверка переменных окружения:")
    print(f"  - GOOGLE_SHEETS_CREDENTIALS_JSON: {'✅ Установлена' if os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON') else '❌ Не установлена'}")
    print(f"  - GOOGLE_APPLICATION_CREDENTIALS_JSON: {'✅ Установлена' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON') else '❌ Не установлена'}")
    print(f"  - BOT_TOKEN: {'✅ Установлен' if os.getenv('BOT_TOKEN') else '❌ Не установлен'}")
    print(f"  - PROJECT_ID: {'✅ Установлен' if os.getenv('PROJECT_ID') else '❌ Не установлен'}")
    
    # Проверяем новый секрет
    if os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON'):
        try:
            credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
            credentials_info = json.loads(credentials_json)
            print(f"  - NEW JSON валиден: ✅")
            print(f"  - NEW Project ID: {credentials_info.get('project_id', 'Не найден')}")
            print(f"  - NEW Client Email: {credentials_info.get('client_email', 'Не найден')}")
            print(f"  - NEW Type: {credentials_info.get('type', 'Не найден')}")
        except Exception as e:
            print(f"  - NEW JSON невалиден: ❌ {e}")
    
    # Проверяем старый секрет
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
        try:
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            credentials_info = json.loads(credentials_json)
            print(f"  - OLD JSON валиден: ✅")
            print(f"  - OLD Project ID: {credentials_info.get('project_id', 'Не найден')}")
            print(f"  - OLD Client Email: {credentials_info.get('client_email', 'Не найден')}")
            print(f"  - OLD Type: {credentials_info.get('type', 'Не найден')}")
        except Exception as e:
            print(f"  - OLD JSON невалиден: ❌ {e}")
    
    print()
    
    # Проверяем файлы credentials
    print("🔍 Проверка файлов credentials:")
    credentials_files = [
        "google_sheets_credentials_fixed.json",
        "google_sheets_credentials.json",
        "just-advice-470905-a3-32c0b9960b41.json"
    ]
    
    for file_path in credentials_files:
        if os.path.exists(file_path):
            print(f"  - {file_path}: ✅ Существует")
            try:
                with open(file_path, 'r') as f:
                    file_content = f.read()
                    if file_content.strip():
                        print(f"    - Размер: {len(file_content)} символов")
                        # Проверяем, что это валидный JSON
                        try:
                            json.loads(file_content)
                            print(f"    - JSON валиден: ✅")
                        except:
                            print(f"    - JSON невалиден: ❌")
                    else:
                        print(f"    - Файл пустой: ❌")
            except Exception as e:
                print(f"    - Ошибка чтения: ❌ {e}")
        else:
            print(f"  - {file_path}: ❌ Не существует")
    
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
        
        print(f"  - Service created: ✅")
        print(f"  - Service available: {'✅' if service.is_available() else '❌'}")
        print(f"  - Service object: {service.service}")
        
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
                print(f"  4. Сервисный аккаунт: {credentials_info.get('client_email', 'Неизвестно')}")
                
        else:
            print("❌ GoogleSheetsService недоступен")
            print("💡 Проверьте credentials и конфигурацию")
            
    except Exception as e:
        print(f"❌ Ошибка создания GoogleSheetsService: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("🏁 Тест завершен")

if __name__ == "__main__":
    test_cloud_credentials()
