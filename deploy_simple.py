#!/usr/bin/env python3
"""
Простой скрипт для развертывания бота на Google Cloud Run
"""
import subprocess
import sys
import time
import requests

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

def main():
    """Основная функция развертывания"""
    print("🚀 Развертывание AI Bot на Google Cloud Run")
    
    PROJECT_ID = "just-advice-470905-a3"
    SERVICE_NAME = "aibot"
    REGION = "asia-southeast1"
    BOT_TOKEN = "8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE"
    WEBHOOK_URL = f"https://{SERVICE_NAME}-{PROJECT_ID}.{REGION}.run.app"
    
    print(f"📋 Параметры:")
    print(f"   Проект: {PROJECT_ID}")
    print(f"   Сервис: {SERVICE_NAME}")
    print(f"   Регион: {REGION}")
    print(f"   Webhook URL: {WEBHOOK_URL}")
    
    # 1. Развертывание через gcloud
    print("\n" + "="*50)
    print("1. Развертывание на Cloud Run")
    print("="*50)
    
    deploy_command = f"""
    gcloud run deploy {SERVICE_NAME} \
        --source . \
        --region {REGION} \
        --project {PROJECT_ID} \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars WEBHOOK_URL={WEBHOOK_URL} \
        --memory 1Gi \
        --cpu 1 \
        --timeout 300 \
        --max-instances 10 \
        --quiet
    """
    
    result = run_command(deploy_command, "Развертывание на Cloud Run")
    if not result:
        print("❌ Ошибка при развертывании")
        return False
    
    # 2. Ожидание готовности сервиса
    print("\n" + "="*50)
    print("2. Ожидание готовности сервиса")
    print("="*50)
    
    print("⏳ Ожидание 30 секунд...")
    time.sleep(30)
    
    # 3. Проверка доступности
    print("\n" + "="*50)
    print("3. Проверка доступности сервиса")
    print("="*50)
    
    health_url = f"{WEBHOOK_URL}/"
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
    
    webhook_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {
        "url": f"{WEBHOOK_URL}/webhook",
        "drop_pending_updates": True
    }
    
    print(f"🔄 Установка webhook: {WEBHOOK_URL}/webhook")
    try:
        response = requests.post(webhook_api_url, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            print(f"✅ Webhook установлен успешно")
            print(f"📊 Результат: {result}")
        else:
            print(f"❌ Ошибка установки webhook: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при установке webhook: {e}")
        return False
    
    # 5. Проверка webhook
    print("\n" + "="*50)
    print("5. Проверка webhook")
    print("="*50)
    
    webhook_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(webhook_info_url, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result.get("result", {})
            print(f"📊 Текущий webhook URL: {webhook_info.get('url', 'Не установлен')}")
            print(f"📊 Количество ожидающих обновлений: {webhook_info.get('pending_update_count', 0)}")
        else:
            print(f"❌ Ошибка получения информации о webhook: {result}")
    except Exception as e:
        print(f"❌ Ошибка при получении информации о webhook: {e}")
    
    print("\n" + "="*50)
    print("✅ Развертывание завершено!")
    print("="*50)
    print(f"🌐 URL сервиса: {WEBHOOK_URL}")
    print(f"📡 Webhook URL: {WEBHOOK_URL}/webhook")
    print(f"❤️ Health check: {WEBHOOK_URL}/")
    print(f"📚 API docs: {WEBHOOK_URL}/docs")
    print("\n💡 Теперь отправьте сообщение боту для тестирования!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
