# Деплой AI Bot в Google Cloud Run

Этот документ описывает процесс деплоя Telegram бота в Google Cloud Run.

## Предварительные требования

1. **Google Cloud SDK** - установите с [официального сайта](https://cloud.google.com/sdk/docs/install)
2. **Docker** - для локальной сборки (опционально)
3. **Аккаунт Google Cloud** с включенным биллингом

## Настройка

### 1. Авторизация в Google Cloud

```bash
gcloud auth login
gcloud config set project just-advice-470905-a3
```

### 2. Включение необходимых API

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Деплой

### Автоматический деплой (рекомендуется)

#### Для Linux/macOS:
```bash
chmod +x deploy.sh
./deploy.sh
```

#### Для Windows PowerShell:
```powershell
.\deploy.ps1
```

### Ручной деплой

1. **Сборка образа:**
```bash
gcloud builds submit --tag gcr.io/just-advice-470905-a3/ai-bot .
```

2. **Деплой в Cloud Run:**
```bash
gcloud run deploy ai-bot \
    --image gcr.io/just-advice-470905-a3/ai-bot \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 300 \
    --set-env-vars "BOT_TOKEN=YOUR_BOT_TOKEN,POSTER_TOKEN=YOUR_POSTER_TOKEN,PROJECT_ID=just-advice-470905-a3"
```

## Мониторинг

### Просмотр логов
```bash
gcloud logs tail --follow --service=ai-bot --region=us-central1
```

### Просмотр статуса сервиса
```bash
gcloud run services describe ai-bot --region=us-central1
```

### Просмотр URL сервиса
```bash
gcloud run services describe ai-bot --region=us-central1 --format="value(status.url)"
```

## Структура файлов для деплоя

- `Dockerfile` - конфигурация Docker контейнера
- `.dockerignore` - файлы, исключаемые из сборки
- `main_cloud.py` - адаптированная версия main.py для Cloud Run
- `cloudbuild.yaml` - конфигурация Cloud Build
- `app.yaml` - конфигурация Cloud Run
- `deploy.sh` / `deploy.ps1` - скрипты автоматического деплоя

## Особенности Cloud Run версии

1. **HTTP сервер** - добавлен для health checks на порту 8080
2. **Переменные окружения** - все секреты передаются через переменные окружения
3. **Polling режим** - бот работает в polling режиме, а не webhook
4. **Автоматическое масштабирование** - от 0 до 10 экземпляров

## Устранение неполадок

### Ошибка авторизации
```bash
gcloud auth login
gcloud auth application-default login
```

### Ошибка сборки
Проверьте, что все зависимости указаны в `requirements.txt`

### Ошибка запуска
Проверьте логи:
```bash
gcloud logs tail --follow --service=ai-bot --region=us-central1
```

### Проблемы с токенами
Убедитесь, что переменные окружения установлены корректно:
- `BOT_TOKEN` - токен Telegram бота
- `POSTER_TOKEN` - токен Poster API
- `PROJECT_ID` - ID проекта Google Cloud

## Обновление

Для обновления сервиса просто запустите скрипт деплоя снова. Cloud Run автоматически обновит сервис с новой версией.
