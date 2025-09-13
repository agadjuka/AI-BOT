#!/usr/bin/env python3
"""
Тест различных методов аутентификации Google Sheets
"""
import sys
import os
import json

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_auth():
    """Тестирует прямую аутентификацию"""
    print("🔍 Тестирование прямой аутентификации...")
    
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        # Загружаем credentials
        with open('google_sheets_credentials_fixed.json', 'r') as f:
            credentials_info = json.load(f)
        
        print(f"🔍 Загружен client_email: {credentials_info.get('client_email')}")
        print(f"🔍 Загружен project_id: {credentials_info.get('project_id')}")
        
        # Создаем credentials
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        print("✅ Credentials созданы успешно")
        
        # Создаем сервис
        service = build('sheets', 'v4', credentials=credentials)
        print("✅ Сервис создан успешно")
        
        # Тестируем доступ к таблице
        sheet_id = "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"
        result = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_title = result.get('properties', {}).get('title', 'Unknown')
        print(f"✅ Успешно получена информация о таблице: {sheet_title}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при прямой аутентификации: {e}")
        return False

def test_file_auth():
    """Тестирует аутентификацию через файл"""
    print("\n🔍 Тестирование аутентификации через файл...")
    
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        # Создаем credentials из файла
        credentials = Credentials.from_service_account_file(
            'google_sheets_credentials_fixed.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        print("✅ Credentials созданы из файла успешно")
        
        # Создаем сервис
        service = build('sheets', 'v4', credentials=credentials)
        print("✅ Сервис создан успешно")
        
        # Тестируем доступ к таблице
        sheet_id = "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"
        result = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_title = result.get('properties', {}).get('title', 'Unknown')
        print(f"✅ Успешно получена информация о таблице: {sheet_title}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при аутентификации через файл: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Тестирование различных методов аутентификации Google Sheets...")
    
    success1 = test_direct_auth()
    success2 = test_file_auth()
    
    if success1 or success2:
        print("\n✅ Хотя бы один метод аутентификации работает!")
    else:
        print("\n❌ Ни один метод аутентификации не работает!")
        sys.exit(1)
