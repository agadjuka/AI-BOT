#!/usr/bin/env python3
"""
Скрипт для тестирования keep-alive функции
Можно запустить локально для проверки работы
"""
import asyncio
import httpx
import time
from datetime import datetime

async def test_keepalive_endpoint():
    """Тестирует /keepalive endpoint"""
    base_url = "http://localhost:8080"
    
    print("🧪 Тестирование keep-alive endpoint...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Тестируем /keepalive endpoint
            response = await client.get(f"{base_url}/keepalive")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Keep-alive endpoint работает")
                print(f"📊 Ответ: {data}")
                return True
            else:
                print(f"❌ Ошибка keep-alive endpoint: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("💡 Убедитесь, что сервер запущен на localhost:8080")
        return False

async def test_health_check():
    """Тестирует / endpoint (health check)"""
    base_url = "http://localhost:8080"
    
    print("🧪 Тестирование health check endpoint...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check работает")
                print(f"📊 Ответ: {data}")
                return True
            else:
                print(f"❌ Ошибка health check: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

async def simulate_keepalive_requests():
    """Симулирует периодические запросы для тестирования"""
    print("🔄 Симуляция периодических keep-alive запросов...")
    print("💡 Нажмите Ctrl+C для остановки")
    
    try:
        while True:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Отправка keep-alive запроса...")
            
            success = await test_keepalive_endpoint()
            if success:
                print("✅ Keep-alive запрос успешен")
            else:
                print("❌ Keep-alive запрос неудачен")
            
            # Ждем 30 секунд перед следующим запросом
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Тестирование остановлено пользователем")

async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование keep-alive функции")
    print("=" * 50)
    
    # Тестируем базовые endpoints
    health_ok = await test_health_check()
    keepalive_ok = await test_keepalive_endpoint()
    
    if health_ok and keepalive_ok:
        print("\n✅ Все базовые тесты прошли успешно!")
        print("🔄 Запускаем симуляцию периодических запросов...")
        await simulate_keepalive_requests()
    else:
        print("\n❌ Некоторые тесты не прошли. Проверьте настройки сервера.")

if __name__ == "__main__":
    asyncio.run(main())
