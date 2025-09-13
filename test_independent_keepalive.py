#!/usr/bin/env python3
"""
Тестовый скрипт для проверки независимой keep-alive функциональности
"""
import asyncio
import httpx
from datetime import datetime

async def test_independent_keep_alive():
    """Тестирует независимую keep-alive функцию"""
    print("🧪 Тестирование независимой keep-alive функциональности")
    print("=" * 60)
    
    # Импортируем функцию из main.py
    try:
        from main import send_keep_alive_request, keep_alive_task
        print("✅ Функции keep-alive импортированы успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return
    
    # Тестируем send_keep_alive_request
    print("\n🔍 Тестируем send_keep_alive_request...")
    try:
        await send_keep_alive_request()
        print("✅ send_keep_alive_request выполнилась без ошибок")
    except Exception as e:
        print(f"❌ Ошибка в send_keep_alive_request: {e}")
    
    # Тестируем keep_alive_task (короткий цикл)
    print("\n🔍 Тестируем keep_alive_task (короткий цикл)...")
    try:
        # Создаем задачу и отменяем её через 15 секунд
        task = asyncio.create_task(keep_alive_task())
        await asyncio.sleep(15)  # Ждем 15 секунд
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("✅ keep_alive_task отменена успешно")
    except Exception as e:
        print(f"❌ Ошибка в keep_alive_task: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено")

async def test_service_endpoints():
    """Тестирует доступность endpoints сервиса"""
    print("\n🌐 Тестируем доступность endpoints сервиса...")
    
    service_url = "https://ai-bot-apmtihe4ga-as.a.run.app"
    endpoints = ["/", "/keepalive", "/debug"]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints:
            url = f"{service_url}{endpoint}"
            try:
                print(f"🔍 Тестируем {url}...", end=" ")
                response = await client.get(url)
                print(f"✅ HTTP {response.status_code}")
                
                if endpoint == "/keepalive":
                    try:
                        data = response.json()
                        print(f"   Ответ: {data}")
                    except:
                        print(f"   Ответ: {response.text[:100]}...")
                        
            except Exception as e:
                print(f"❌ Ошибка: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование независимой keep-alive системы")
    print("=" * 60)
    print("💡 Keep-alive теперь:")
    print("   - Не зависит от переменных окружения")
    print("   - Хардкодит URL сервиса")
    print("   - Не блокирует запуск бота")
    print("   - Работает независимо в фоне")
    print("=" * 60)
    
    # Запускаем тесты
    asyncio.run(test_independent_keep_alive())
    asyncio.run(test_service_endpoints())
    
    print("\n" + "=" * 60)
    print("✅ Все тесты завершены")
    print("\n💡 Теперь keep-alive полностью независим и не влияет на работу бота!")

if __name__ == "__main__":
    main()
