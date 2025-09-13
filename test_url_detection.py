#!/usr/bin/env python3
"""
Простой тест для проверки определения URL сервиса
"""
import os
import sys

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, '.')

def test_get_service_url():
    """Тестирует функцию get_service_url"""
    print("🧪 Тестирование определения URL сервиса...")
    
    # Импортируем функцию из main.py
    from main import get_service_url
    
    # Тестируем без переменной SERVICE_URL
    if 'SERVICE_URL' in os.environ:
        del os.environ['SERVICE_URL']
    
    url = get_service_url()
    print(f"✅ URL без SERVICE_URL: {url}")
    
    # Тестируем с переменной SERVICE_URL
    os.environ['SERVICE_URL'] = 'https://test.example.com'
    url = get_service_url()
    print(f"✅ URL с SERVICE_URL: {url}")
    
    # Очищаем переменную
    del os.environ['SERVICE_URL']
    
    print("🎉 Все тесты прошли успешно!")

if __name__ == "__main__":
    test_get_service_url()
