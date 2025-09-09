# Быстрый деплой на Google Cloud Run через GitHub

## 🚀 Шаги для первого деплоя

### 1. Подготовка Google Cloud

```bash
# Установите gcloud CLI и авторизуйтесь
gcloud auth login

# Установите проект
gcloud config set project YOUR_PROJECT_ID

# Включите API
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Создайте Service Account
gcloud iam service-accounts create github-actions-sa --display-name="GitHub Actions"

# Привяжите роли
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Создайте ключ
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 2. Настройка GitHub Secrets

Перейдите в ваш репозиторий: **Settings → Secrets and variables → Actions**

Добавьте секреты:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | `YOUR_PROJECT_ID` |
| `GCP_SA_KEY` | Содержимое файла `github-actions-key.json` |
| `BOT_TOKEN` | `YOUR_TELEGRAM_BOT_TOKEN` |
| `WEBHOOK_URL` | `https://ai-bot-xxxxx-uc.a.run.app` (будет обновлен автоматически) |

### 3. Загрузка кода

```bash
# Добавьте все файлы в git
git add .
git commit -m "Add GitHub Actions deployment"
git push origin main
```

### 4. Проверка деплоя

1. Перейдите в **Actions** tab в GitHub
2. Дождитесь завершения workflow
3. Скопируйте URL сервиса из логов
4. Обновите `WEBHOOK_URL` в секретах GitHub

### 5. Тестирование

```bash
# Health check
curl https://your-service-url/

# Проверка webhook
curl https://your-service-url/get_webhook
```

## ✅ Готово!

Теперь при каждом push в `main` ваш бот будет автоматически обновляться на Google Cloud Run.

## 🔧 Настройки в workflow

Если нужно изменить настройки, отредактируйте `.github/workflows/deploy.yml`:

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  SERVICE_NAME: ai-bot        # Имя сервиса
  REGION: us-central1         # Регион
```

И в секции деплоя:

```yaml
--memory 1Gi                  # Память
--cpu 1                       # CPU
--max-instances 10            # Максимум инстансов
--min-instances 0             # Минимум инстансов
--timeout 300                 # Таймаут
```

## 🆘 Проблемы?

1. **Ошибка аутентификации** → Проверьте `GCP_SA_KEY`
2. **Ошибка сборки** → Проверьте `Dockerfile` и `requirements.txt`
3. **Webhook не работает** → Проверьте `BOT_TOKEN` и `WEBHOOK_URL`
4. **Сервис не запускается** → Проверьте логи в Cloud Run Console