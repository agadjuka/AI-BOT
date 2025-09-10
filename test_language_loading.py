#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки языка из Firestore
"""
import os
import sys
from pathlib import Path

def load_env_file():
    """Загружает переменные окружения из .env файла"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        return False
    
    print("📁 Загружаем переменные окружения из .env...")
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"✅ {key} = {'*' * len(value) if value else 'NOT SET'}")
    
    return True

def test_language_loading():
    """Тестирует загрузку языка из Firestore"""
    print("\n🧪 Тестируем загрузку языка из Firestore...")
    
    from services.language_service import LanguageService
    from config.locales.locale_manager import LocaleManager
    
    # Создаем экземпляры сервисов
    language_service = LanguageService()
    locale_manager = LocaleManager()
    
    # Тестовый user_id (тот же, что использовался ранее)
    test_user_id = 261617302
    
    print(f"📖 Загружаем язык для пользователя {test_user_id}...")
    
    # Загружаем язык напрямую из LanguageService
    stored_language = language_service.get_user_language(test_user_id)
    print(f"📋 Язык из LanguageService: '{stored_language}'")
    
    # Загружаем язык через LocaleManager
    loaded_language = locale_manager.get_user_language_from_storage(test_user_id)
    print(f"📋 Язык из LocaleManager: '{loaded_language}'")
    
    if stored_language and stored_language == loaded_language:
        print(f"✅ Язык успешно загружен: '{stored_language}'")
        return True
    else:
        print(f"❌ Ошибка: LanguageService='{stored_language}', LocaleManager='{loaded_language}'")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование загрузки языка из Firestore...")
    print("=" * 50)
    
    # Загружаем переменные окружения
    if not load_env_file():
        sys.exit(1)
    
    # Тестируем загрузку языка
    if not test_language_loading():
        print("\n❌ Тест загрузки языка не прошел")
        sys.exit(1)
    
    print("\n🎉 Тест загрузки языка прошел успешно!")

if __name__ == "__main__":
    main()

