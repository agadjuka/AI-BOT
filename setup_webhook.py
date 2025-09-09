#!/usr/bin/env python3
"""
Скрипт для настройки webhook в Telegram Bot API
Использование: python setup_webhook.py <BOT_TOKEN> <WEBHOOK_URL>
"""

import sys
import requests
import json

def set_webhook(bot_token: str, webhook_url: str) -> bool:
    """
    Устанавливает webhook для Telegram бота
    
    Args:
        bot_token: Токен бота от @BotFather
        webhook_url: URL webhook (например: https://aibot-xxxxx-uc.a.run.app/webhook)
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    data = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"]  # Только нужные типы обновлений
    }
    
    try:
        print(f"🔗 Настройка webhook: {webhook_url}")
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Webhook успешно настроен!")
                print(f"📡 URL: {webhook_url}")
                print(f"📊 Описание: {result.get('description', 'N/A')}")
                return True
            else:
                print(f"❌ Ошибка API: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False

def get_webhook_info(bot_token: str) -> dict:
    """
    Получает информацию о текущем webhook
    
    Args:
        bot_token: Токен бота от @BotFather
    
    Returns:
        dict: Информация о webhook
    """
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ HTTP ошибка при получении информации: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети при получении информации: {e}")
        return {}

def delete_webhook(bot_token: str) -> bool:
    """
    Удаляет webhook (возвращает к polling режиму)
    
    Args:
        bot_token: Токен бота от @BotFather
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    try:
        print("🗑️ Удаление webhook...")
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Webhook успешно удален!")
                return True
            else:
                print(f"❌ Ошибка API: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("❌ Использование:")
        print("  python setup_webhook.py <BOT_TOKEN> <WEBHOOK_URL>")
        print("  python setup_webhook.py <BOT_TOKEN> --info")
        print("  python setup_webhook.py <BOT_TOKEN> --delete")
        print("\nПримеры:")
        print("  python setup_webhook.py 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11 https://aibot-xxxxx-uc.a.run.app/webhook")
        print("  python setup_webhook.py 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11 --info")
        print("  python setup_webhook.py 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11 --delete")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    
    if len(sys.argv) == 3:
        if sys.argv[2] == "--info":
            # Показать информацию о webhook
            print("📊 Получение информации о webhook...")
            info = get_webhook_info(bot_token)
            if info:
                result = info.get("result", {})
                print(f"📡 URL: {result.get('url', 'Не установлен')}")
                print(f"🔢 Pending updates: {result.get('pending_update_count', 0)}")
                print(f"📅 Last error date: {result.get('last_error_date', 'N/A')}")
                print(f"❌ Last error message: {result.get('last_error_message', 'N/A')}")
                print(f"🔄 Max connections: {result.get('max_connections', 'N/A')}")
            sys.exit(0)
        elif sys.argv[2] == "--delete":
            # Удалить webhook
            delete_webhook(bot_token)
            sys.exit(0)
        else:
            # Установить webhook
            webhook_url = sys.argv[2]
            if not webhook_url.startswith("https://"):
                print("❌ Webhook URL должен начинаться с https://")
                sys.exit(1)
            
            success = set_webhook(bot_token, webhook_url)
            if success:
                print("\n🎉 Настройка завершена!")
                print("💡 Теперь ваш бот будет получать обновления через webhook")
                print("🔍 Проверить статус: python setup_webhook.py <BOT_TOKEN> --info")
            else:
                print("\n❌ Настройка не удалась")
                sys.exit(1)
    else:
        print("❌ Неверное количество аргументов")
        sys.exit(1)

if __name__ == "__main__":
    main()
