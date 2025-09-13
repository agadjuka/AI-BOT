#!/usr/bin/env python3
"""
Тест Google Sheets доступа для облачной версии
"""
import os
import json
from services.google_sheets_service import GoogleSheetsService

def test_google_sheets_access():
    """Тестирует доступ к Google Sheets с различными методами аутентификации"""
    
    print("🔍 Тестирование Google Sheets доступа...")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("📋 Переменные окружения:")
    print(f"  - GOOGLE_SHEETS_CREDENTIALS_JSON: {'✅ Установлена' if os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON') else '❌ Не установлена'}")
    print(f"  - GOOGLE_APPLICATION_CREDENTIALS_JSON: {'✅ Установлена' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON') else '❌ Не установлена'}")
    print(f"  - GOOGLE_APPLICATION_CREDENTIALS: {'✅ Установлена' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') else '❌ Не установлена'}")
    
    # Тестируем с разными конфигурациями
    test_configs = [
        {
            "name": "С переменной GOOGLE_SHEETS_CREDENTIALS_JSON",
            "credentials_path": None,
            "spreadsheet_id": "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"
        },
        {
            "name": "С файлом credentials",
            "credentials_path": "google_sheets_credentials_fixed.json",
            "spreadsheet_id": "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"
        }
    ]
    
    for config in test_configs:
        print(f"\n🧪 Тест: {config['name']}")
        print("-" * 30)
        
        try:
            service = GoogleSheetsService(
                credentials_path=config['credentials_path'],
                spreadsheet_id=config['spreadsheet_id']
            )
            
            if service.is_available():
                print("✅ Сервис инициализирован успешно")
                
                # Пытаемся получить информацию о таблице
                try:
                    spreadsheet = service.service.spreadsheets().get(spreadsheetId=config['spreadsheet_id']).execute()
                    print(f"✅ Доступ к таблице успешен")
                    print(f"   - Название: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
                    print(f"   - ID: {spreadsheet.get('spreadsheetId', 'Unknown')}")
                    
                    # Пытаемся получить список листов
                    sheets = spreadsheet.get('sheets', [])
                    print(f"   - Количество листов: {len(sheets)}")
                    for sheet in sheets:
                        sheet_title = sheet.get('properties', {}).get('title', 'Unknown')
                        print(f"     * {sheet_title}")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ Ошибка доступа к таблице: {e}")
                    print(f"   Тип ошибки: {type(e).__name__}")
                    
                    # Анализируем ошибку
                    error_str = str(e)
                    if "403" in error_str:
                        print("💡 Возможные причины:")
                        print("   - Недостаточно прав доступа")
                        print("   - Неправильный service account")
                        print("   - Таблица не доступна для этого аккаунта")
                    elif "404" in error_str:
                        print("💡 Возможные причины:")
                        print("   - Неправильный ID таблицы")
                        print("   - Таблица не существует")
                    elif "401" in error_str:
                        print("💡 Возможные причины:")
                        print("   - Неправильные credentials")
                        print("   - Истек срок действия токена")
                    
            else:
                print("❌ Сервис не инициализирован")
                
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            import traceback
            traceback.print_exc()
    
    return False

def test_credentials_parsing():
    """Тестирует парсинг credentials из переменных окружения"""
    print("\n🔍 Тестирование парсинга credentials...")
    print("=" * 50)
    
    # Тестируем GOOGLE_SHEETS_CREDENTIALS_JSON
    google_sheets_credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
    if google_sheets_credentials_json:
        try:
            credentials_info = json.loads(google_sheets_credentials_json)
            print("✅ GOOGLE_SHEETS_CREDENTIALS_JSON парсится успешно")
            print(f"   - Project ID: {credentials_info.get('project_id', 'Не найден')}")
            print(f"   - Client Email: {credentials_info.get('client_email', 'Не найден')}")
            print(f"   - Type: {credentials_info.get('type', 'Не найден')}")
            print(f"   - Private Key ID: {credentials_info.get('private_key_id', 'Не найден')}")
        except Exception as e:
            print(f"❌ Ошибка парсинга GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
    else:
        print("❌ GOOGLE_SHEETS_CREDENTIALS_JSON не установлена")
    
    # Тестируем GOOGLE_APPLICATION_CREDENTIALS_JSON
    google_credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if google_credentials_json:
        try:
            credentials_info = json.loads(google_credentials_json)
            print("✅ GOOGLE_APPLICATION_CREDENTIALS_JSON парсится успешно")
            print(f"   - Project ID: {credentials_info.get('project_id', 'Не найден')}")
            print(f"   - Client Email: {credentials_info.get('client_email', 'Не найден')}")
            print(f"   - Type: {credentials_info.get('type', 'Не найден')}")
            print(f"   - Private Key ID: {credentials_info.get('private_key_id', 'Не найден')}")
        except Exception as e:
            print(f"❌ Ошибка парсинга GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
    else:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON не установлена")

if __name__ == "__main__":
    print("🚀 Запуск тестирования Google Sheets доступа")
    print("=" * 60)
    
    # Тестируем парсинг credentials
    test_credentials_parsing()
    
    # Тестируем доступ к Google Sheets
    success = test_google_sheets_access()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Тест завершен успешно!")
    else:
        print("❌ Тест завершен с ошибками")
        print("\n💡 Рекомендации:")
        print("1. Убедитесь, что GOOGLE_SHEETS_CREDENTIALS_JSON установлена в GitHub Secrets")
        print("2. Проверьте, что service account имеет права доступа к Google Sheets")
        print("3. Убедитесь, что ID таблицы правильный")
        print("4. Проверьте, что таблица доступна для service account")