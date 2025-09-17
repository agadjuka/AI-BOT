#!/usr/bin/env python3
"""
Тест для проверки параллельной обработки вебхуков
Проверяет, могут ли вебхуки параллельно принимать и обрабатывать фото
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# Тестовые данные для webhook
def create_photo_update(user_id: int, message_id: int) -> Dict[str, Any]:
    """Создает тестовый update с фото"""
    return {
        "update_id": message_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": f"TestUser{user_id}",
                "username": f"testuser{user_id}"
            },
            "chat": {
                "id": user_id,
                "first_name": f"TestUser{user_id}",
                "username": f"testuser{user_id}",
                "type": "private"
            },
            "date": int(time.time()),
            "photo": [
                {
                    "file_id": f"test_photo_{message_id}_small",
                    "file_unique_id": f"test_unique_{message_id}_small",
                    "width": 90,
                    "height": 90,
                    "file_size": 1000
                },
                {
                    "file_id": f"test_photo_{message_id}_medium",
                    "file_unique_id": f"test_unique_{message_id}_medium",
                    "width": 320,
                    "height": 320,
                    "file_size": 5000
                },
                {
                    "file_id": f"test_photo_{message_id}_large",
                    "file_unique_id": f"test_unique_{message_id}_large",
                    "width": 800,
                    "height": 800,
                    "file_size": 20000
                }
            ]
        }
    }

async def send_webhook_request(session: aiohttp.ClientSession, webhook_url: str, 
                             update_data: Dict[str, Any], request_id: int) -> Dict[str, Any]:
    """Отправляет webhook запрос"""
    try:
        print(f"📤 Запрос {request_id}: Отправляем webhook...")
        start_time = time.time()
        
        async with session.post(
            webhook_url,
            json=update_data,
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response_data = await response.json()
            end_time = time.time()
            
            print(f"✅ Запрос {request_id}: Ответ получен за {end_time - start_time:.2f} сек")
            print(f"   Статус: {response.status}, Ответ: {response_data}")
            
            return {
                'request_id': request_id,
                'status': response.status,
                'response': response_data,
                'duration': end_time - start_time,
                'success': response.status == 200
            }
            
    except asyncio.TimeoutError:
        print(f"⏰ Запрос {request_id}: Таймаут")
        return {
            'request_id': request_id,
            'status': 408,
            'response': {'error': 'timeout'},
            'duration': 30.0,
            'success': False
        }
    except Exception as e:
        print(f"❌ Запрос {request_id}: Ошибка: {e}")
        return {
            'request_id': request_id,
            'status': 500,
            'response': {'error': str(e)},
            'duration': 0.0,
            'success': False
        }

async def test_concurrent_webhooks(webhook_url: str, num_requests: int = 5):
    """Тестирует параллельную обработку webhook запросов"""
    print(f"🚀 Тестирование {num_requests} параллельных webhook запросов...")
    print(f"🌐 URL: {webhook_url}")
    
    # Создаем HTTP сессию
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Создаем тестовые данные
        updates = []
        for i in range(num_requests):
            user_id = 1000 + i
            message_id = 2000 + i
            update = create_photo_update(user_id, message_id)
            updates.append(update)
        
        print(f"📊 Создано {len(updates)} тестовых updates")
        
        # Запускаем параллельные запросы
        start_time = time.time()
        
        tasks = []
        for i, update in enumerate(updates):
            task = send_webhook_request(session, webhook_url, update, i + 1)
            tasks.append(task)
        
        # Ждем завершения всех запросов
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Анализируем результаты
        successful_requests = 0
        total_duration = 0
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"⏱️ Общее время выполнения: {total_time:.2f} секунд")
        
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ Исключение: {result}")
            else:
                if result['success']:
                    successful_requests += 1
                    total_duration += result['duration']
                print(f"📋 Запрос {result['request_id']}: "
                      f"Статус {result['status']}, "
                      f"Время {result['duration']:.2f}с, "
                      f"Успех: {'✅' if result['success'] else '❌'}")
        
        success_rate = successful_requests / num_requests * 100
        avg_duration = total_duration / successful_requests if successful_requests > 0 else 0
        
        print(f"\n🎯 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   ✅ Успешных запросов: {successful_requests}/{num_requests} ({success_rate:.1f}%)")
        print(f"   ⏱️ Среднее время ответа: {avg_duration:.2f} секунд")
        print(f"   🚀 Общая производительность: {num_requests/total_time:.2f} запросов/сек")
        
        return success_rate == 100 and avg_duration < 10

async def test_webhook_health(webhook_url: str):
    """Проверяет здоровье webhook"""
    print(f"🏥 Проверка здоровья webhook: {webhook_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Проверяем health check
            health_url = webhook_url.replace('/webhook', '/')
            async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка health check: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ПАРАЛЛЕЛЬНОЙ ОБРАБОТКИ WEBHOOK")
    print("=" * 60)
    
    # URL для тестирования (замените на ваш)
    webhook_url = "https://ai-bot-xxxxx-uc.a.run.app/webhook"  # Замените на реальный URL
    
    print("⚠️ ВНИМАНИЕ: Замените webhook_url на реальный URL вашего бота!")
    print(f"🌐 Текущий URL: {webhook_url}")
    
    # Проверяем, что URL изменен
    if "xxxxx" in webhook_url:
        print("\n❌ ОШИБКА: Необходимо указать реальный URL webhook!")
        print("💡 Откройте файл test_webhook_concurrency.py и замените webhook_url")
        return
    
    try:
        # Запускаем тесты
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Тест 1: Проверка здоровья
        print("\n🔬 ТЕСТ 1: Проверка здоровья webhook")
        health_ok = loop.run_until_complete(test_webhook_health(webhook_url))
        
        if not health_ok:
            print("❌ Webhook недоступен, тест прерван")
            return
        
        # Тест 2: Параллельная обработка
        print("\n🔬 ТЕСТ 2: Параллельная обработка webhook")
        concurrency_ok = loop.run_until_complete(test_concurrent_webhooks(webhook_url, 5))
        
        print("\n" + "=" * 60)
        print("📋 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
        print(f"   ✅ Health check: {'ПРОЙДЕН' if health_ok else 'ПРОВАЛЕН'}")
        print(f"   ✅ Параллельная обработка: {'ПРОЙДЕН' if concurrency_ok else 'ПРОВАЛЕН'}")
        
        if health_ok and concurrency_ok:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Webhook может параллельно обрабатывать запросы.")
            print("💡 Ваш бот готов к одновременной обработке нескольких квитанций!")
        else:
            print("\n❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ. Требуется дополнительная настройка.")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
