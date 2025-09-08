# Быстрое развертывание AI Bot на Google Cloud Run

## Что исправлено

✅ **Устранен конфликт слияния Git** - код приведен в порядок  
✅ **Переведен на FastAPI** - более современный и быстрый фреймворк  
✅ **Добавлена настройка webhook** - автоматическая установка при запуске  
✅ **Детальное логирование** - для отладки проблем  
✅ **Обновлены зависимости** - FastAPI + uvicorn вместо Flask + gunicorn  

## Развертывание

### Вариант 1: Автоматический (рекомендуется)
```bash
python deploy_webhook.py
```

### Вариант 2: Ручной
```bash
# 1. Развертывание
gcloud run deploy aibot \
    --source . \
    --region asia-southeast1 \
    --project just-advice-470905-a3 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars WEBHOOK_URL=https://aibot-366461711404.asia-southeast1.run.app \
    --memory 1Gi --cpu 1 --timeout 300 --max-instances 10

# 2. Установка webhook
curl -X POST "https://api.telegram.org/bot8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://aibot-366461711404.asia-southeast1.run.app/webhook", "drop_pending_updates": true}'
```

## Проверка работы

1. **Health check**: https://aibot-366461711404.asia-southeast1.run.app/
2. **API документация**: https://aibot-366461711404.asia-southeast1.run.app/docs
3. **Webhook info**: https://aibot-366461711404.asia-southeast1.run.app/get_webhook

## Отладка

Если бот не работает, проверьте логи:
```bash
gcloud logs read --project=just-advice-470905-a3 --region=asia-southeast1 --service=aibot --limit=50
```

## Основные изменения

- **FastAPI** вместо Flask - лучше производительность и async поддержка
- **uvicorn** вместо gunicorn - оптимизирован для FastAPI
- **Автоматическая настройка webhook** при запуске
- **Детальные логи** для отладки
- **Современная структура** с async/await

Теперь бот должен работать правильно! 🚀
