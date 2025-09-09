#!/usr/bin/env python3
"""
Скрипт для настройки локальной среды разработки
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Проверяет версию Python"""
    if sys.version_info < (3, 10):
        print("❌ Требуется Python 3.10 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False
    
    print(f"✅ Python версия: {sys.version}")
    return True

def create_env_file():
    """Создает .env файл если его нет"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ Файл .env уже существует")
        return True
    
    if not env_example.exists():
        print("❌ Файл env.example не найден")
        return False
    
    # Копируем env.example в .env
    with open(env_example, 'r', encoding='utf-8') as src:
        content = src.read()
    
    with open(env_file, 'w', encoding='utf-8') as dst:
        dst.write(content)
    
    print("✅ Создан файл .env на основе env.example")
    print("💡 Отредактируйте .env и добавьте ваши токены")
    return True

def install_dependencies():
    """Устанавливает зависимости для локальной разработки"""
    print("📦 Устанавливаем зависимости...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_local.txt"
        ], check=True)
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False

def check_credentials():
    """Проверяет наличие файлов credentials"""
    creds_file = Path("google_sheets_credentials.json")
    
    if creds_file.exists():
        print("✅ Файл google_sheets_credentials.json найден")
    else:
        print("⚠️ Файл google_sheets_credentials.json не найден")
        print("💡 Скопируйте файл credentials из Google Cloud Console")

def main():
    """Основная функция настройки"""
    print("🚀 Настройка локальной среды разработки AI Bot")
    print("=" * 60)
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    # Создаем .env файл
    if not create_env_file():
        sys.exit(1)
    
    # Устанавливаем зависимости
    if not install_dependencies():
        sys.exit(1)
    
    # Проверяем credentials
    check_credentials()
    
    print("=" * 60)
    print("✅ Настройка завершена!")
    print()
    print("📝 Следующие шаги:")
    print("1. Отредактируйте файл .env и добавьте ваши токены")
    print("2. Запустите локальную версию: python run_local.py")
    print("3. Для деплоя в production: git push origin main")
    print()
    print("📚 Документация: README_LOCAL.md")

if __name__ == "__main__":
    main()
