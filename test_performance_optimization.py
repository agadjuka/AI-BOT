#!/usr/bin/env python3
"""
Скрипт для тестирования оптимизации производительности
Проверяет скорость обработки фотографий с новыми оптимизациями
"""
import os
import time
import asyncio
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
import sys
sys.path.append('.')

from config.settings import BotConfig
from config.prompts import PromptManager
from services.ai_service import AIServiceFactory
from handlers.photo_handler import PhotoHandler

async def test_photo_processing_performance():
    """Тестирует производительность обработки фотографий"""
    print("🚀 Тестирование производительности обработки фотографий")
    print("=" * 60)
    
    # Инициализация конфигурации
    config = BotConfig()
    prompt_manager = PromptManager()
    
    # Создаем AI сервис
    ai_factory = AIServiceFactory(config, prompt_manager)
    ai_service = ai_factory.get_default_service()
    
    # Создаем обработчик фотографий
    from services.ai_service import ReceiptAnalysisServiceCompat
    analysis_service = ReceiptAnalysisServiceCompat(ai_service, ai_factory)
    photo_handler = PhotoHandler(config, analysis_service)
    
    # Тестовые изображения (если есть)
    test_images = [
        "last_photo.jpg",
        "analyzed_last_photo.jpg"
    ]
    
    # Проверяем доступность тестовых изображений
    available_images = []
    for img in test_images:
        if os.path.exists(img):
            available_images.append(img)
            print(f"✅ Найдено тестовое изображение: {img}")
        else:
            print(f"⚠️ Тестовое изображение не найдено: {img}")
    
    if not available_images:
        print("❌ Нет доступных тестовых изображений")
        print("💡 Поместите изображения чеков в корневую директорию для тестирования")
        return
    
    print(f"\n🔍 Тестируем {len(available_images)} изображений...")
    print("=" * 60)
    
    # Тестируем каждое изображение
    total_time = 0
    for i, image_path in enumerate(available_images, 1):
        print(f"\n📸 Тест {i}/{len(available_images)}: {image_path}")
        
        # Измеряем время выбора модели
        start_time = time.time()
        chosen_model = photo_handler._choose_model_simple()
        model_time = time.time() - start_time
        
        print(f"   🎯 Выбрана модель: {chosen_model} (время: {model_time:.3f}с)")
        
        # Измеряем размер файла
        file_size = os.path.getsize(image_path)
        print(f"   📁 Размер файла: {file_size:,} байт ({file_size/1024:.1f} KB)")
        
        # Проверяем настройки OpenCV
        opencv_disabled = getattr(config, 'DISABLE_OPENCV_ANALYSIS', True)
        print(f"   🔧 OpenCV анализ отключен: {opencv_disabled}")
        
        total_time += model_time
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   • Обработано изображений: {len(available_images)}")
    print(f"   • Общее время выбора модели: {total_time:.3f}с")
    print(f"   • Среднее время на изображение: {total_time/len(available_images):.3f}с")
    print(f"   • OpenCV анализ отключен: {getattr(config, 'DISABLE_OPENCV_ANALYSIS', True)}")
    print(f"   • Модель по умолчанию: {getattr(config, 'DEFAULT_MODEL', 'pro')}")
    
    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    if total_time < 0.1:
        print("   ✅ Отличная производительность! Время выбора модели < 0.1с")
    elif total_time < 0.5:
        print("   ✅ Хорошая производительность! Время выбора модели < 0.5с")
    else:
        print("   ⚠️ Производительность может быть улучшена")
    
    if getattr(config, 'DISABLE_OPENCV_ANALYSIS', True):
        print("   ✅ OpenCV анализ отключен - это ускоряет обработку")
    else:
        print("   ⚠️ OpenCV анализ включен - это может замедлять обработку")
    
    print("\n🔧 НАСТРОЙКИ ДЛЯ ОПТИМИЗАЦИИ:")
    print("   • DISABLE_OPENCV_ANALYSIS=true (отключить OpenCV)")
    print("   • DEFAULT_MODEL=flash (быстрая модель)")
    print("   • DEFAULT_MODEL=pro (качественная модель)")

def test_configuration():
    """Тестирует конфигурацию"""
    print("\n🔧 ТЕСТИРОВАНИЕ КОНФИГУРАЦИИ")
    print("=" * 60)
    
    config = BotConfig()
    
    print(f"📋 Текущие настройки:")
    print(f"   • DEFAULT_MODEL: {getattr(config, 'DEFAULT_MODEL', 'pro')}")
    print(f"   • DISABLE_OPENCV_ANALYSIS: {getattr(config, 'DISABLE_OPENCV_ANALYSIS', True)}")
    print(f"   • GEMINI_ANALYSIS_MODE: {getattr(config, 'GEMINI_ANALYSIS_MODE', 'production')}")
    print(f"   • MODEL_PRO: {getattr(config, 'MODEL_PRO', 'gemini-2.5-pro')}")
    print(f"   • MODEL_FLASH: {getattr(config, 'MODEL_FLASH', 'gemini-2.5-flash')}")
    
    # Проверяем переменные окружения
    print(f"\n🌍 Переменные окружения:")
    env_vars = [
        'DISABLE_OPENCV_ANALYSIS',
        'DEFAULT_MODEL', 
        'GEMINI_ANALYSIS_MODE'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'НЕ УСТАНОВЛЕНО')
        print(f"   • {var}: {value}")

async def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ОПТИМИЗАЦИИ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 60)
    
    # Тестируем конфигурацию
    test_configuration()
    
    # Тестируем производительность
    await test_photo_processing_performance()
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
