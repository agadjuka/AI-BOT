# Развертывание AI Bot с Webhook на Google Cloud Run

## Проблема
Бот запускается на Cloud Run, но не обрабатывает сообщения от Telegram. В логах видно `payload: "payloadNotSet"`, что означает, что webhook не настроен правильно.

## Решение

### 1. Автоматическое развертывание
Запустите скрипт автоматического развертывания:

```bash
python deploy_webhook.py
```

Этот скрипт:
- Соберет и развернет приложение на Cloud Run
- Установит переменную окружения `WEBHOOK_URL`
- Настроит webhook в Telegram API
- Протестирует работу webhook

### 2. Ручное развертывание

#### Шаг 1: Развертывание на Cloud Run
```bash
gcloud run deploy aibot \
    --source . \
    --region asia-southeast1 \
    --project just-advice-470905-a3 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars WEBHOOK_URL=https://aibot-366461711404.asia-southeast1.run.app \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10
```

#### Шаг 2: Установка webhook через API
```bash
curl -X POST "https://api.telegram.org/bot8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://aibot-366461711404.asia-southeast1.run.app/webhook",
       "drop_pending_updates": true
     }'
```

#### Шаг 3: Проверка webhook
```bash
curl "https://api.telegram.org/bot8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE/getWebhookInfo"
```

### 3. Проверка работы

#### Health Check
```bash
curl https://aibot-366461711404.asia-southeast1.run.app/
```

#### Webhook Info
```bash
curl https://aibot-366461711404.asia-southeast1.run.app/get_webhook
```

## Что было исправлено

1. **Добавлена настройка webhook** - теперь бот автоматически устанавливает webhook URL при запуске
2. **Добавлено детальное логирование** - в webhook endpoint добавлены подробные логи для отладки
3. **Исправлен Dockerfile** - правильная обработка переменной PORT
4. **Добавлены endpoints для управления webhook** - `/set_webhook` и `/get_webhook`
5. **Добавлена переменная окружения WEBHOOK_URL** - для автоматической настройки webhook

## Отладка

Если бот все еще не работает:

1. Проверьте логи Cloud Run:
```bash
gcloud logs read --project=just-advice-470905-a3 --region=asia-southeast1 --service=aibot --limit=50
```

2. Проверьте webhook info:
```bash
curl https://aibot-366461711404.asia-southeast1.run.app/get_webhook
```

3. Отправьте тестовое сообщение боту и проверьте логи на предмет новых записей

## Структура endpoints

- `GET /` - Health check
- `POST /webhook` - Webhook для Telegram (основной endpoint)
- `POST /set_webhook` - Установка webhook вручную
- `GET /get_webhook` - Получение информации о webhook
