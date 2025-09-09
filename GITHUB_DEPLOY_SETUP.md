# Настройка автоматического деплоя на Google Cloud Run через GitHub Actions

## Предварительные требования

1. **Google Cloud Project** с включенными API:
   - Cloud Run API
   - Container Registry API
   - Cloud Build API

2. **Service Account** с правами:
   - Cloud Run Admin
   - Storage Admin
   - Service Account User

## Настройка GitHub Secrets

В настройках вашего GitHub репозитория (Settings → Secrets and variables → Actions) добавьте следующие секреты:

### 1. GCP_PROJECT_ID
- **Значение**: ID вашего Google Cloud проекта
- **Пример**: `my-ai-bot-project-123456`

### 2. GCP_SA_KEY
- **Значение**: JSON ключ Service Account
- **Как получить**:
  1. Перейдите в Google Cloud Console → IAM & Admin → Service Accounts
  2. Создайте новый Service Account или выберите существующий
  3. Назначьте роли: Cloud Run Admin, Storage Admin, Service Account User
  4. Создайте JSON ключ и скопируйте его содержимое

## Настройка Google Cloud

### 1. Включение API
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Настройка аутентификации
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 3. Создание Service Account
```bash
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions" \
    --description="Service account for GitHub Actions deployment"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Настройка переменных окружения

В файле `.github/workflows/deploy.yml` вы можете изменить следующие параметры:

- `SERVICE_NAME`: имя сервиса в Cloud Run (по умолчанию: `ai-bot`)
- `REGION`: регион развертывания (по умолчанию: `europe-west1`)

## Настройка переменных окружения для приложения

В Google Cloud Console → Cloud Run → ваш сервис → Edit & Deploy New Revision → Variables & Secrets добавьте:

- `BOT_TOKEN`: токен вашего Telegram бота
- `GOOGLE_APPLICATION_CREDENTIALS`: путь к файлу с учетными данными (если используется)
- Другие переменные из вашего `config/settings.py`

## Процесс деплоя

После настройки:

1. Сделайте push в ветку `main`
2. GitHub Actions автоматически:
   - Соберет Docker образ
   - Загрузит его в Google Container Registry
   - Развернет на Cloud Run

## Мониторинг

- **GitHub Actions**: Проверьте статус в разделе Actions вашего репозитория
- **Cloud Run**: Перейдите в Google Cloud Console → Cloud Run для просмотра логов и метрик

## Устранение неполадок

### Ошибка аутентификации
- Проверьте правильность `GCP_SA_KEY`
- Убедитесь, что Service Account имеет необходимые права

### Ошибка сборки Docker
- Проверьте `Dockerfile` и `.dockerignore`
- Убедитесь, что все зависимости указаны в `requirements.txt`

### Ошибка развертывания
- Проверьте настройки Cloud Run
- Убедитесь, что порт 8080 доступен
- Проверьте переменные окружения

## Дополнительные настройки

### Настройка домена
```bash
gcloud run domain-mappings create \
    --service=ai-bot \
    --domain=your-domain.com \
    --region=europe-west1
```

### Настройка SSL
SSL сертификаты настраиваются автоматически для доменов, добавленных через domain-mappings.

### Мониторинг и логи
```bash
# Просмотр логов
gcloud logs read --service=ai-bot --limit=50

# Просмотр метрик
gcloud run services describe ai-bot --region=europe-west1
```

