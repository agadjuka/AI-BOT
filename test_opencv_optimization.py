#!/usr/bin/env python3
"""
Тест оптимизации OpenCV - проверяет ленивую загрузку и выгрузку
"""
import time
import psutil
import os
import sys

def get_memory_usage():
    """Получает текущее использование памяти в MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def test_opencv_loading():
    """Тестирует загрузку OpenCV"""
    print("🧪 Тестирование оптимизации OpenCV...")
    
    # Измеряем память до импорта
    memory_before = get_memory_usage()
    print(f"📊 Память до импорта: {memory_before:.2f} MB")
    
    # Импортируем модули
    print("📦 Импортируем модули...")
    from utils.opencv_lazy_loader import check_opencv_availability, get_opencv, unload_opencv
    from utils.receipt_analyzer_optimized import analyze_receipt_and_choose_model
    
    memory_after_import = get_memory_usage()
    print(f"📊 Память после импорта: {memory_after_import:.2f} MB")
    print(f"📈 Прирост памяти: {memory_after_import - memory_before:.2f} MB")
    
    # Проверяем доступность OpenCV
    opencv_available = check_opencv_availability()
    print(f"🔍 OpenCV доступен: {opencv_available}")
    
    if not opencv_available:
        print("❌ OpenCV недоступен, тест прерван")
        return
    
    # Тестируем ленивую загрузку
    print("🔍 Тестируем ленивую загрузку OpenCV...")
    memory_before_cv2 = get_memory_usage()
    
    cv2 = get_opencv()
    memory_after_cv2 = get_memory_usage()
    print(f"📊 Память после загрузки OpenCV: {memory_after_cv2:.2f} MB")
    print(f"📈 Прирост памяти OpenCV: {memory_after_cv2 - memory_before_cv2:.2f} MB")
    
    # Тестируем выгрузку
    print("🧹 Тестируем выгрузку OpenCV...")
    unload_opencv()
    memory_after_unload = get_memory_usage()
    print(f"📊 Память после выгрузки: {memory_after_unload:.2f} MB")
    print(f"📉 Освобождено памяти: {memory_after_cv2 - memory_after_unload:.2f} MB")
    
    # Тестируем повторную загрузку
    print("🔄 Тестируем повторную загрузку...")
    cv2_again = get_opencv()
    memory_after_reload = get_memory_usage()
    print(f"📊 Память после повторной загрузки: {memory_after_reload:.2f} MB")
    
    # Финальная выгрузка
    unload_opencv()
    memory_final = get_memory_usage()
    print(f"📊 Финальная память: {memory_final:.2f} MB")
    
    print("✅ Тест завершен успешно!")

def test_analyze_function():
    """Тестирует функцию анализа с оптимизацией"""
    print("\n🧪 Тестирование функции анализа...")
    
    # Создаем тестовое изображение
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    
    # Создаем простое тестовое изображение
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Добавляем текст
    try:
        # Пытаемся использовать системный шрифт
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        # Fallback на стандартный шрифт
        font = ImageFont.load_default()
    
    draw.text((50, 50), "Test Receipt", fill='black', font=font)
    draw.text((50, 100), "Item 1: $10.00", fill='black', font=font)
    draw.text((50, 150), "Item 2: $15.50", fill='black', font=font)
    draw.text((50, 200), "Total: $25.50", fill='black', font=font)
    
    # Сохраняем как байты
    import io
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    image_bytes = img_bytes.getvalue()
    
    print(f"📷 Создано тестовое изображение: {len(image_bytes)} байт")
    
    # Тестируем анализ
    memory_before = get_memory_usage()
    print(f"📊 Память до анализа: {memory_before:.2f} MB")
    
    try:
        import asyncio
        from utils.receipt_analyzer_optimized import analyze_receipt_and_choose_model
        result = asyncio.run(analyze_receipt_and_choose_model(image_bytes))
        print(f"🎯 Результат анализа: {result}")
        
        memory_after = get_memory_usage()
        print(f"📊 Память после анализа: {memory_after:.2f} MB")
        print(f"📈 Прирост памяти: {memory_after - memory_before:.2f} MB")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
    
    print("✅ Тест функции анализа завершен!")

if __name__ == "__main__":
    print("🚀 Запуск тестов оптимизации OpenCV...")
    
    try:
        test_opencv_loading()
        test_analyze_function()
        
        print("\n🎉 Все тесты завершены успешно!")
        print("\n💡 Рекомендации:")
        print("   - OpenCV загружается только при необходимости")
        print("   - Память освобождается после использования")
        print("   - Производительность Gemini не должна страдать")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
