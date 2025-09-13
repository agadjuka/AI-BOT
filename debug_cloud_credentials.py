#!/usr/bin/env python3
"""
Скрипт для отладки credentials в облачной среде
"""
import os
import json
from services.google_sheets_service import GoogleSheetsService
from config.settings import BotConfig

def debug_cloud_credentials():
    """Отладка credentials в облачной среде"""
    print("🔍 Отладка credentials в облачной среде...")
    print("=" * 80)
    
    # Проверяем все переменные окружения
    print("🔍 Все переменные окружения:")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ['GOOGLE', 'BOT', 'PROJECT', 'CREDENTIALS']):
            if 'JSON' in key.upper():
                print(f"  - {key}: {'✅ Установлена' if value else '❌ Пустая'}")
                if value:
                    try:
                        json_data = json.loads(value)
                        print(f"    - JSON валиден: ✅")
                        print(f"    - Project ID: {json_data.get('project_id', 'Не найден')}")
                        print(f"    - Client Email: {json_data.get('client_email', 'Не найден')}")
                    except:
                        print(f"    - JSON невалиден: ❌")
            else:
                print(f"  - {key}: {'✅ Установлена' if value else '❌ Пустая'}")
    
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
                        try:
                            json_data = json.loads(file_content)
                            print(f"    - JSON валиден: ✅")
                            print(f"    - Project ID: {json_data.get('project_id', 'Не найден')}")
                            print(f"    - Client Email: {json_data.get('client_email', 'Не найден')}")
                        except Exception as e:
                            print(f"    - JSON невалиден: ❌ {e}")
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
    
    # Создаем сервис с подробной отладкой
    print("🔧 Создание GoogleSheetsService с отладкой...")
    try:
        service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        print(f"  - Service created: ✅")
        print(f"  - Service available: {'✅' if service.is_available() else '❌'}")
        print(f"  - Service object: {service.service}")
        print(f"  - Credentials path: {service.credentials_path}")
        print(f"  - Spreadsheet ID: {service.spreadsheet_id}")
        
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
                print("💡 Детали ошибки:")
                print(f"  - Тип ошибки: {type(e).__name__}")
                print(f"  - Сообщение: {str(e)}")
                
                # Проверяем тип ошибки
                if "PERMISSION_DENIED" in str(e):
                    print("  - Это ошибка прав доступа")
                    print("  - Проверьте, что сервисный аккаунт имеет права Editor на таблицу")
                elif "invalid_grant" in str(e).lower():
                    print("  - Это ошибка аутентификации")
                    print("  - Проверьте правильность credentials")
                elif "not found" in str(e).lower():
                    print("  - Таблица не найдена")
                    print("  - Проверьте правильность Spreadsheet ID")
                
                print("💡 Проверьте:")
                print("  1. Правильность Spreadsheet ID")
                print("  2. Права доступа сервисного аккаунта к таблице")
                print("  3. Включен ли Google Sheets API")
                
                # Показываем информацию о сервисном аккаунте
                google_credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
                if google_credentials_json:
                    try:
                        credentials_info = json.loads(google_credentials_json)
                        print(f"  4. Сервисный аккаунт: {credentials_info.get('client_email', 'Неизвестно')}")
                        print(f"  5. Project ID: {credentials_info.get('project_id', 'Неизвестно')}")
                    except:
                        pass
                
        else:
            print("❌ GoogleSheetsService недоступен")
            print("💡 Проверьте credentials и конфигурацию")
            
    except Exception as e:
        print(f"❌ Ошибка создания GoogleSheetsService: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("🏁 Отладка завершена")

if __name__ == "__main__":
    debug_cloud_credentials()
