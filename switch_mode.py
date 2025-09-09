#!/usr/bin/env python3
"""
Скрипт для переключения между локальной и production версиями
"""
import os
import sys
import shutil
from pathlib import Path

def show_help():
    """Показывает справку по использованию"""
    print("🔄 Переключение режимов AI Bot")
    print("=" * 40)
    print("Использование:")
    print("  python switch_mode.py local    - Переключиться на локальную версию")
    print("  python switch_mode.py prod     - Переключиться на production версию")
    print("  python switch_mode.py status   - Показать текущий режим")
    print()

def get_current_mode():
    """Определяет текущий режим"""
    main_file = Path("main.py")
    main_local_file = Path("main_local.py")
    
    if not main_file.exists():
        return "unknown"
    
    # Читаем первые строки main.py для определения режима
    with open(main_file, 'r', encoding='utf-8') as f:
        first_lines = f.read(200)
    
    if "FastAPI" in first_lines and "webhook" in first_lines:
        return "production"
    elif "polling" in first_lines and "LOCAL" in first_lines:
        return "local"
    else:
        return "unknown"

def switch_to_local():
    """Переключается на локальную версию"""
    print("🔄 Переключение на локальную версию...")
    
    # Проверяем наличие файлов
    if not Path("main_local.py").exists():
        print("❌ Файл main_local.py не найден")
        return False
    
    # Создаем резервную копию текущего main.py
    if Path("main.py").exists():
        shutil.copy("main.py", "main_production_backup.py")
        print("✅ Создана резервная копия main.py")
    
    # Копируем локальную версию в main.py
    shutil.copy("main_local.py", "main.py")
    print("✅ Переключено на локальную версию")
    
    # Проверяем наличие .env файла
    if not Path(".env").exists():
        print("⚠️ Файл .env не найден")
        print("💡 Запустите: python dev_setup.py")
    
    return True

def switch_to_production():
    """Переключается на production версию"""
    print("🔄 Переключение на production версию...")
    
    # Восстанавливаем из резервной копии
    if Path("main_production_backup.py").exists():
        shutil.copy("main_production_backup.py", "main.py")
        print("✅ Переключено на production версию")
        return True
    
    # Если резервной копии нет, проверяем git
    try:
        import subprocess
        result = subprocess.run([
            "git", "show", "HEAD:main.py"
        ], capture_output=True, text=True, check=True)
        
        with open("main.py", 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        print("✅ Восстановлена production версия из git")
        return True
        
    except Exception as e:
        print(f"❌ Не удалось восстановить production версию: {e}")
        print("💡 Убедитесь, что main.py в git содержит production версию")
        return False

def show_status():
    """Показывает текущий статус"""
    mode = get_current_mode()
    
    print("📊 Текущий статус:")
    print(f"  Режим: {mode}")
    
    if mode == "local":
        print("  ✅ Готов для локальной разработки")
        print("  💡 Запуск: python run_local.py")
    elif mode == "production":
        print("  ✅ Готов для production деплоя")
        print("  💡 Запуск: python main.py")
    else:
        print("  ❓ Неизвестный режим")
    
    # Проверяем файлы
    files_status = {
        "main.py": Path("main.py").exists(),
        "main_local.py": Path("main_local.py").exists(),
        ".env": Path(".env").exists(),
        "requirements_local.txt": Path("requirements_local.txt").exists(),
    }
    
    print("\n📁 Файлы:")
    for file, exists in files_status.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "local":
        switch_to_local()
    elif command == "prod":
        switch_to_production()
    elif command == "status":
        show_status()
    elif command in ["help", "-h", "--help"]:
        show_help()
    else:
        print(f"❌ Неизвестная команда: {command}")
        show_help()

if __name__ == "__main__":
    main()
