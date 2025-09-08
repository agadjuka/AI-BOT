#!/usr/bin/env python3
"""
Скрипт для развертывания бота на Google Cloud Run с настройкой webhook
"""
import os
import subprocess
import sys
import json
import requests
import time

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно")
        if result.stdout:
            print(f"📤 Вывод: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка")
        print(f"📤 Вывод: {e.stdout}")
        print(f"❌ Ошибка: {e.stderr}")
        return None

def get_cloud_run_url(project_id, service_name, region="asia-southeast1"):
    """Получает URL сервиса Cloud Run"""
    command = f"gcloud run services describe {service_name} --region={region} --project={project_id} --format='value(status.url)'"
    result = run_command(command, f"Получение URL сервиса {service_name}")
    if result and result.stdout.strip():
        return result.stdout.strip()
    return None

def set_webhook_via_api(webhook_url, bot_token):
    """Устанавливает webhook через Telegram API"""
    webhook_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    data = {
        "url": f"{webhook_url}/webhook",
        "drop_pending_updates": True
    }
    
    print(f"🔄 Установка webhook: {webhook_url}/webhook")
    try:
        response = requests.post(webhook_api_url, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            print(f"✅ Webhook установлен успешно")
            print(f"📊 Результат: {result}")
        else:
            print(f"❌ Ошибка установки webhook: {result}")
        return result
    except Exception as e:
        print(f"❌ Ошибка при установке webhook: {e}")
        return None

def get_webhook_info(bot_token):
    """Получает информацию о текущем webhook"""
    webhook_info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    print(f"🔄 Получение информации о webhook")
    try:
        response = requests.get(webhook_info_url, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result.get("result", {})
            print(f"📊 Текущий webhook URL: {webhook_info.get('url', 'Не установлен')}")
            print(f"📊 Количество ожидающих обновлений: {webhook_info.get('pending_update_count', 0)}")
            return webhook_info
        else:
            print(f"❌ Ошибка получения информации о webhook: {result}")
        return None
    except Exception as e:
        print(f"❌ Ошибка при получении информации о webhook: {e}")
        return None

def main():
    """Основная функция развертывания"""
    print("🚀 Развертывание AI Bot на Google Cloud Run")
    
    # Параметры
    PROJECT_ID = "just-advice-470905-a3"
    SERVICE_NAME = "aibot"
    REGION = "asia-southeast1"
    BOT_TOKEN = "8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE"
    
    print(f"📋 Параметры:")
    print(f"   Проект: {PROJECT_ID}")
    print(f"   Сервис: {SERVICE_NAME}")
    print(f"   Регион: {REGION}")
    print(f"   Бот токен: {BOT_TOKEN[:10]}...")
    
    # 1. Сборка и развертывание
    print("\n" + "="*50)
    print("1. Сборка и развертывание на Cloud Run")
    print("="*50)
    
    # Установка переменной окружения для webhook
    webhook_url_env = f"WEBHOOK_URL=https://{SERVICE_NAME}-{PROJECT_ID}.{REGION}.run.app"
    
    deploy_command = f"""
    gcloud run deploy {SERVICE_NAME} \
        --source . \
        --region {REGION} \
        --project {PROJECT_ID} \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars WEBHOOK_URL=https://{SERVICE_NAME}-{PROJECT_ID}.{REGION}.run.app \
        --memory 1Gi \
        --cpu 1 \
        --timeout 300 \
        --max-instances 10
    """
    
    result = run_command(deploy_command, "Развертывание на Cloud Run")
    if not result:
        print("❌ Ошибка при развертывании")
        return False
    
    # 2. Получение URL сервиса
    print("\n" + "="*50)
    print("2. Получение URL сервиса")
    print("="*50)
    
    webhook_url = get_cloud_run_url(PROJECT_ID, SERVICE_NAME, REGION)
    if not webhook_url:
        print("❌ Не удалось получить URL сервиса")
        return False
    
    print(f"✅ URL сервиса: {webhook_url}")
    
    # 3. Проверка доступности сервиса
    print("\n" + "="*50)
    print("3. Проверка доступности сервиса")
    print("="*50)
    
    health_url = f"{webhook_url}/"
    print(f"🔄 Проверка доступности: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=30)
        if response.status_code == 200:
            print("✅ Сервис доступен")
            print(f"📊 Ответ: {response.json()}")
        else:
            print(f"❌ Сервис недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке доступности: {e}")
        return False
    
    # 4. Установка webhook
    print("\n" + "="*50)
    print("4. Установка webhook")
    print("="*50)
    
    # Сначала получаем текущую информацию о webhook
    get_webhook_info(BOT_TOKEN)
    
    # Устанавливаем новый webhook
    webhook_result = set_webhook_via_api(webhook_url, BOT_TOKEN)
    if not webhook_result or not webhook_result.get("ok"):
        print("❌ Не удалось установить webhook")
        return False
    
    # Проверяем, что webhook установлен
    print("\n🔄 Проверка установки webhook...")
    time.sleep(2)
    get_webhook_info(BOT_TOKEN)
    
    # 5. Тестирование webhook
    print("\n" + "="*50)
    print("5. Тестирование webhook")
    print("="*50)
    
    test_webhook_url = f"{webhook_url}/get_webhook"
    print(f"🔄 Тестирование webhook endpoint: {test_webhook_url}")
    
    try:
        response = requests.get(test_webhook_url, timeout=30)
        if response.status_code == 200:
            print("✅ Webhook endpoint работает")
            print(f"📊 Ответ: {response.json()}")
        else:
            print(f"❌ Webhook endpoint не работает: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании webhook: {e}")
    
    # 6. Тестирование FastAPI docs
    print("\n🔄 Тестирование FastAPI документации...")
    docs_url = f"{webhook_url}/docs"
    try:
        response = requests.get(docs_url, timeout=30)
        if response.status_code == 200:
            print(f"✅ FastAPI docs доступны: {docs_url}")
        else:
            print(f"⚠️ FastAPI docs недоступны: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка при проверке docs: {e}")
    
    print("\n" + "="*50)
    print("✅ Развертывание завершено!")
    print("="*50)
    print(f"🌐 URL сервиса: {webhook_url}")
    print(f"📡 Webhook URL: {webhook_url}/webhook")
    print(f"❤️ Health check: {webhook_url}/")
    print(f"🔧 Webhook info: {webhook_url}/get_webhook")
    print("\n💡 Теперь отправьте сообщение боту для тестирования!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
