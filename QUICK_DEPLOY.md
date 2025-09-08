<<<<<<< HEAD
# 🚀 Быстрый деплой AI Bot в Google Cloud Run

## Готовые файлы для деплоя:

✅ **Dockerfile** - конфигурация контейнера  
✅ **main_cloud.py** - адаптированная версия для Cloud Run  
✅ **deploy.ps1** - скрипт деплоя для Windows  
✅ **deploy.sh** - скрипт деплоя для Linux/macOS  
✅ **cloudbuild.yaml** - конфигурация автоматической сборки  
✅ **app.yaml** - конфигурация Cloud Run  

## 🎯 Быстрый старт:

### 1. Установите Google Cloud SDK
Скачайте с [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)

### 2. Авторизуйтесь
```powershell
gcloud auth login
gcloud config set project just-advice-470905-a3
```

### 3. Запустите деплой
```powershell
.\deploy.ps1
```

## 🔧 Что изменилось для Cloud Run:

1. **Добавлен HTTP сервер** на порту 8080 для health checks
2. **Переменные окружения** вместо hardcoded токенов
3. **Polling режим** вместо webhook (лучше для Cloud Run)
4. **Автоматическое масштабирование** от 0 до 10 экземпляров

## 📊 После деплоя:

- **URL сервиса** будет показан в консоли
- **Логи**: `gcloud logs tail --follow --service=ai-bot --region=us-central1`
- **Статус**: `gcloud run services describe ai-bot --region=us-central1`

## ⚠️ Важно:

- Все токены уже настроены в скриптах
- Функционал бота остался **полностью неизменным**
- Добавлен только HTTP сервер для Cloud Run
- Бот будет работать точно так же, как и раньше

## 🆘 Если что-то не работает:

1. Проверьте логи: `gcloud logs tail --follow --service=ai-bot --region=us-central1`
2. Убедитесь, что API включены: `gcloud services enable cloudbuild.googleapis.com run.googleapis.com`
3. Проверьте авторизацию: `gcloud auth list`

**Готово к деплою! 🎉**

=======
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
>>>>>>> 562d10c69e6e854963bf134dc1a919227ef51d4d
