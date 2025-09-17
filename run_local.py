#!/usr/bin/env python3
"""
Скрипт для запуска локальной версии бота 
Автоматически загружает переменные окружения из .env файла
"""
import os
import sys
import asyncio
from pathlib import Path

def load_env_file():
    """Загружает переменные окружения из .env файла"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("💡 Создайте файл .env на основе env.example:")
        print("   cp env.example .env")
        print("   # Затем отредактируйте .env и добавьте ваши токены")
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

def check_required_vars():
    """Проверяет наличие обязательных переменных окружения"""
    required_vars = ['BOT_TOKEN', 'PROJECT_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        print("💡 Проверьте файл .env")
        return False
    
    return True

def main():
    """Основная функция запуска"""
    print("🚀 Запуск локальной версии AI Bot...")
    print("=" * 50)
    
    # Загружаем переменные окружения
    if not load_env_file():
        sys.exit(1)
    
    # Проверяем обязательные перемеанные gjkyfz
    if not check_required_vars():
        sys.exit(1)
    
    print("✅ Все переменные окружения загружены")
    print("=" * 50)
    
    # Импортируем и запускаем main_localа
    try:
        from main_local import main
        main()  # main() уже асинхроннсая функция, не нужно asyncio.run()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Убедитесь, что все зависимости установлены:")
        print("   pip install -r requirements_local.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
