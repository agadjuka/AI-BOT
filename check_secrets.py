#!/usr/bin/env python3
"""
Скрипт для проверки секретов в GitHub Actions
"""
import os

def check_secrets():
    print("🔍 Проверка секретов в GitHub Actions...")
    
    secrets_to_check = [
        "BOT_TOKEN",
        "POSTER_TOKEN", 
        "GCP_PROJECT_ID",
        "WEBHOOK_URL",
        "GCP_SA_KEY"
    ]
    
    for secret in secrets_to_check:
        value = os.getenv(secret)
        if value:
            print(f"✅ {secret}: {'*' * len(value)} (длина: {len(value)})")
        else:
            print(f"❌ {secret}: НЕ НАЙДЕН")
    
    print("\n🔍 Все переменные окружения:")
    for key, value in sorted(os.environ.items()):
        if any(keyword in key.upper() for keyword in ["TOKEN", "PROJECT", "WEBHOOK", "SECRET"]):
            print(f"  {key}: {'*' * len(value) if value else 'NOT SET'}")

if __name__ == "__main__":
    check_secrets()
