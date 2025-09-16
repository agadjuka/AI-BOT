#!/usr/bin/env python3
"""
Тестовый скрипт для проверки режима отладки анализа выбора модели
"""
import os
import asyncio
from pathlib import Path

def load_env_file():
    """Загружает переменные окружения из .env файла"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("💡 Создайте файл .env на основе env.example:")
        print("   cp env.example .env")
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

async def test_debug_mode():
    """Тестирует режим отладки"""
    print("🧪 Тестирование режима отладки анализа выбора модели")
    print("=" * 60)
    
    # Загружаем переменные окружения
    if not load_env_file():
        return
    
    # Проверяем настройки
    from config.settings import BotConfig
    config = BotConfig()
    
    print(f"🔧 Текущий режим анализа: {config.GEMINI_ANALYSIS_MODE}")
    print(f"🔧 Модель PRO: {config.MODEL_PRO}")
    print(f"🔧 Модель FLASH: {config.MODEL_FLASH}")
    print()
    
    # Тестируем функцию анализа
    try:
        from utils.receipt_analyzer import analyze_receipt_and_choose_model
        
        # Проверяем, есть ли тестовое изображение
        test_image_path = "last_photo.jpg"
        if not os.path.exists(test_image_path):
            print(f"❌ Тестовое изображение не найдено: {test_image_path}")
            print("💡 Отправьте фото в бота, чтобы создать тестовое изображение")
            return
        
        print(f"🔍 Анализируем изображение: {test_image_path}")
        
        with open(test_image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Анализируем изображение
        chosen_model = await analyze_receipt_and_choose_model(image_bytes)
        
        print(f"🎯 Результат анализа: выбрана модель {chosen_model.upper()}")
        
        if config.GEMINI_ANALYSIS_MODE == "debug":
            print("🔍 Режим отладки активен - полный анализ не выполняется")
        else:
            print("🔍 Режим production - будет выполнен полный анализ")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_debug_mode())
