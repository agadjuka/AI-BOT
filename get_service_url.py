#!/usr/bin/env python3
"""
Скрипт для получения URL сервиса Cloud Run
"""
import subprocess
import sys

def get_service_url():
    try:
        # Получаем URL сервиса
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'ai-bot',
            '--region=us-central1',
            '--format=value(status.url)'
        ], capture_output=True, text=True, check=True)
        
        url = result.stdout.strip()
        print(f"🌐 Service URL: {url}")
        print(f"📋 Add this to GitHub Secrets as WEBHOOK_URL: {url}")
        
        return url
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting service URL: {e}")
        print("Make sure you're authenticated with gcloud")
        return None
    except FileNotFoundError:
        print("❌ gcloud CLI not found. Install it first.")
        return None

if __name__ == "__main__":
    get_service_url()
