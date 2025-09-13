#!/usr/bin/env python3
"""
Тестовый скрипт для проверки keep-alive механизма
Можно запустить локально для тестирования логики
"""
import os
import asyncio
import httpx
from datetime import datetime

async def test_keep_alive_ping(service_url: str, test_duration: int = 30):
    """Тестирует keep-alive ping в течение указанного времени"""
    print(f"🧪 Тестирование keep-alive ping для {service_url}")
    print(f"⏱️ Длительность теста: {test_duration} секунд")
    print("=" * 50)
    
    start_time = datetime.now()
    ping_count = 0
    success_count = 0
    error_count = 0
    
    while (datetime.now() - start_time).total_seconds() < test_duration:
        try:
            ping_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"[{current_time}] Ping #{ping_count}...", end=" ")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{service_url}/health")
                
                if response.status_code == 200:
                    success_count += 1
                    print("✅ Success")
                else:
                    error_count += 1
                    print(f"❌ HTTP {response.status_code}")
                    
        except Exception as e:
            error_count += 1
            print(f"❌ Error: {e}")
        
        # Ждем 10 секунд между пингами для тестирования
        await asyncio.sleep(10)
    
    # Статистика
    print("=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   Всего пингов: {ping_count}")
    print(f"   Успешных: {success_count}")
    print(f"   Ошибок: {error_count}")
    print(f"   Успешность: {(success_count/ping_count*100):.1f}%")

async def test_local_health_endpoint():
    """Тестирует локальный health endpoint"""
    print("🧪 Тестирование локального health endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8080/health")
            print(f"✅ Локальный health endpoint: HTTP {response.status_code}")
            print(f"   Ответ: {response.json()}")
    except Exception as e:
        print(f"❌ Ошибка подключения к локальному серверу: {e}")
        print("💡 Убедитесь, что сервер запущен на localhost:8080")

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование keep-alive механизма")
    print("=" * 50)
    
    # Проверяем переменную SERVICE_URL
    service_url = os.getenv("SERVICE_URL")
    
    if service_url:
        print(f"✅ SERVICE_URL найден: {service_url}")
        print("🧪 Запускаем тест keep-alive ping...")
        asyncio.run(test_keep_alive_ping(service_url, test_duration=60))
    else:
        print("⚠️ SERVICE_URL не установлен")
        print("💡 Для тестирования в Cloud Run установите переменную SERVICE_URL")
        print("💡 Для локального тестирования запустите сервер и используйте localhost")
        
        # Тестируем локальный сервер
        print("\n🧪 Тестируем локальный сервер...")
        asyncio.run(test_local_health_endpoint())

if __name__ == "__main__":
    main()