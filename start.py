#!/usr/bin/env python3
"""
Универсальный скрипт запуска AI Bot
Автоматически определяет режим и запускает соответствующую версию
"""
import os
import sys
import subprocess
from pathlib import Path

def detect_mode():
    """Автоматически определяет режим запуска"""
    # Проверяем переменные окружения
    if os.getenv("WEBHOOK_URL") or os.getenv("PORT"):
        return "production"
    
    # Проверяем наличие .env файла
    if Path(".env").exists():
        return "local"
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode in ["local", "dev", "development"]:
            return "local"
        elif mode in ["prod", "production", "deploy"]:
            return "production"
    
    # По умолчанию локальный режим
    return "local"

def run_local():
    """Запускает локальную версию"""
    print("🏠 Запуск локальной версии...")
    
    # Проверяем наличие .env файла
    if not Path(".env").exists():
        print("❌ Файл .env не найден")
        print("💡 Запустите: python dev_setup.py")
        return False
    
    # Запускаем run_local.py
    try:
        subprocess.run([sys.executable, "run_local.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при запуске локальной версии: {e}")
        return False
    except FileNotFoundError:
        print("❌ Файл run_local.py не найден")
        return False

def run_production():
    """Запускает production версию"""
    print("☁️ Запуск production версии...")
    
    # Проверяем переменные окружения
    required_vars = ["BOT_TOKEN", "PROJECT_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("💡 Установите переменные окружения или используйте локальный режим")
        return False
    
    # Запускаем main.py
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при запуске production версии: {e}")
        return False
    except FileNotFoundError:
        print("❌ Файл main.py не найден")
        return False

def show_help():
    """Показывает справку"""
    print("🚀 AI Bot - Универсальный запуск")
    print("=" * 40)
    print("Использование:")
    print("  python start.py              # Автоматический выбор режима")
    print("  python start.py local        # Принудительно локальный режим")
    print("  python start.py production   # Принудительно production режим")
    print("  python start.py help         # Показать эту справку")
    print()
    print("Режимы:")
    print("  local      - Локальная разработка (polling)")
    print("  production - Production деплой (webhook)")
    print()
    print("Дополнительные команды:")
    print("  python dev_setup.py          # Настройка среды разработки")
    print("  python switch_mode.py        # Переключение между версиями")

def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["help", "-h", "--help"]:
        show_help()
        return
    
    # Определяем режим
    mode = detect_mode()
    print(f"🔍 Определен режим: {mode}")
    
    # Запускаем соответствующую версию
    if mode == "local":
        success = run_local()
    else:
        success = run_production()
    
    if not success:
        print("\n💡 Попробуйте:")
        print("  1. python dev_setup.py  # Настройка локальной среды")
        print("  2. python start.py local  # Принудительно локальный режим")
        print("  3. python start.py help  # Справка")
        sys.exit(1)

if __name__ == "__main__":
    main()
