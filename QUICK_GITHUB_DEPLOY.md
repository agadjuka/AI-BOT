# Быстрый деплой на Google Cloud Run через GitHub

## 1. Подготовка Google Cloud

```bash
# Включить API
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Создать Service Account
gcloud iam service-accounts create github-actions --display-name="GitHub Actions"

# Назначить роли
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Создать ключ
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## 2. Настройка GitHub Secrets

В GitHub → Settings → Secrets and variables → Actions добавить:

- `GCP_PROJECT_ID`: ID вашего Google Cloud проекта
- `GCP_SA_KEY`: содержимое файла `github-actions-key.json`

## 3. Настройка переменных окружения в Cloud Run

В Google Cloud Console → Cloud Run → ваш сервис → Edit & Deploy New Revision → Variables & Secrets:

- `BOT_TOKEN`: токен вашего Telegram бота
- Другие переменные из `config/settings.py`

## 4. Деплой

Просто сделайте push в ветку `main` - деплой произойдет автоматически!

## Структура файлов

```
.github/workflows/deploy.yml  # GitHub Actions workflow
Dockerfile                    # Обновленный Dockerfile
.dockerignore                # Исключения для Docker
.gitignore                   # Исключения для Git
GITHUB_DEPLOY_SETUP.md       # Подробная инструкция
QUICK_GITHUB_DEPLOY.md       # Эта инструкция
```

## Проверка

После деплоя проверьте:
- GitHub Actions: статус в разделе Actions
- Cloud Run: логи в Google Cloud Console
- Telegram бот: отправьте `/start`

