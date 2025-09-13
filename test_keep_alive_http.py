#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новой keep-alive функциональности с HTTP запросами
"""
import os
import asyncio
import httpx
from datetime import datetime

async def test_keep_alive_http_function():
    """Тестирует функцию send_keep_alive_request напрямую"""
    print("🧪 Тестирование функции send_keep_alive_request...")
    
    # Импортируем функцию из main.py
    import sys
    sys.path.append('.')
    
    try:
        from main import send_keep_alive_request
        
        # Тестируем с разными URL
        test_urls = [
            "https://ai-bot-366461711404.asia-southeast1.run.app",
            "http://localhost:8080",
            "https://httpbin.org/status/200"  # Тестовый URL для проверки
        ]
        
        for url in test_urls:
            print(f"\n🔍 Тестируем URL: {url}")
            try:
                await send_keep_alive_request(url)
            except Exception as e:
                print(f"❌ Ошибка при тестировании {url}: {e}")
                
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Убедитесь, что main.py находится в той же директории")

async def test_service_endpoints(service_url: str):
    """Тестирует доступность endpoints сервиса"""
    print(f"🧪 Тестирование endpoints сервиса: {service_url}")
    
    endpoints = [
        "/",
        "/keepalive", 
        "/health",
        "/debug"
    ]
    
    base_url = service_url.rstrip('/')
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                print(f"🔍 Тестируем {url}...", end=" ")
                response = await client.get(url)
                print(f"✅ HTTP {response.status_code}")
                
                # Показываем часть ответа для keepalive
                if endpoint == "/keepalive":
                    try:
                        data = response.json()
                        print(f"   Ответ: {data}")
                    except:
                        print(f"   Ответ: {response.text[:100]}...")
                        
            except Exception as e:
                print(f"❌ Ошибка: {e}")

async def simulate_keep_alive_cycle(service_url: str, cycles: int = 3):
    """Симулирует несколько циклов keep-alive"""
    print(f"🧪 Симуляция {cycles} циклов keep-alive для {service_url}")
    
    for i in range(cycles):
        print(f"\n🔄 Цикл {i+1}/{cycles}")
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"⏰ Время: {current_time}")
        
        try:
            from main import send_keep_alive_request
            await send_keep_alive_request(service_url)
        except Exception as e:
            print(f"❌ Ошибка в цикле {i+1}: {e}")
        
        # Ждем 5 секунд между циклами для демонстрации
        if i < cycles - 1:
            print("⏳ Ждем 5 секунд до следующего цикла...")
            await asyncio.sleep(5)

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование новой keep-alive функциональности с HTTP запросами")
    print("=" * 70)
    
    # Получаем URL сервиса
    service_url = os.getenv("SERVICE_URL") or os.getenv("WEBHOOK_URL")
    
    if not service_url:
        print("⚠️ SERVICE_URL или WEBHOOK_URL не установлен")
        print("💡 Установите переменную окружения для тестирования:")
        print("   export SERVICE_URL=https://your-service-url")
        print("   или")
        print("   export WEBHOOK_URL=https://your-service-url")
        
        # Используем известный URL для демонстрации
        service_url = "https://ai-bot-366461711404.asia-southeast1.run.app"
        print(f"\n🧪 Используем известный URL для демонстрации: {service_url}")
    else:
        print(f"✅ URL сервиса: {service_url}")
    
    print("\n" + "=" * 70)
    
    # Запускаем тесты
    asyncio.run(test_keep_alive_http_function())
    
    if service_url:
        print("\n" + "=" * 70)
        asyncio.run(test_service_endpoints(service_url))
        
        print("\n" + "=" * 70)
        asyncio.run(simulate_keep_alive_cycle(service_url, cycles=2))
    
    print("\n" + "=" * 70)
    print("✅ Тестирование завершено")
    print("\n💡 Для полного тестирования:")
    print("   1. Запустите сервер: python main.py")
    print("   2. Установите SERVICE_URL: export SERVICE_URL=http://localhost:8080")
    print("   3. Запустите тест: python test_keep_alive_http.py")

if __name__ == "__main__":
    main()
