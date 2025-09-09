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

3. **GitHub репозиторий** с вашим кодом

## Настройка Google Cloud

### 1. Создание Service Account

```bash
# Создаем Service Account
gcloud iam service-accounts create github-actions-sa \
    --display-name="GitHub Actions Service Account"

# Привязываем роли
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Создаем ключ
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 2. Включение API

```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Настройка GitHub Secrets

В настройках вашего GitHub репозитория (Settings → Secrets and variables → Actions) добавьте:

### Обязательные секреты:

1. **`GCP_PROJECT_ID`** - ID вашего Google Cloud проекта
2. **`GCP_SA_KEY`** - содержимое JSON файла ключа Service Account (весь файл)
3. **`BOT_TOKEN`** - токен вашего Telegram бота
4. **`WEBHOOK_URL`** - URL вашего Cloud Run сервиса (будет обновлен автоматически)

### Пример значений:

```
GCP_PROJECT_ID: my-ai-bot-project
GCP_SA_KEY: {"type": "service_account", "project_id": "my-ai-bot-project", ...}
BOT_TOKEN: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
WEBHOOK_URL: https://ai-bot-xxxxx-uc.a.run.app
```

## Настройка переменных окружения

В файле `.github/workflows/deploy.yml` обновите следующие переменные:

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  SERVICE_NAME: ai-bot  # Имя вашего сервиса
  REGION: us-central1   # Регион деплоя
```

## Первый деплой

1. **Загрузите код в GitHub** в ветку `main`
2. **Настройте все секреты** в GitHub
3. **Запустите workflow** - он запустится автоматически при push в main
4. **Получите URL сервиса** из логов GitHub Actions
5. **Обновите WEBHOOK_URL** в секретах GitHub новым URL

## Проверка деплоя

После успешного деплоя:

1. **Health check**: `GET https://your-service-url/`
2. **Webhook info**: `GET https://your-service-url/get_webhook`
3. **Установка webhook**: `POST https://your-service-url/set_webhook`

## Структура проекта

```
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── .dockerignore               # Исключения для Docker
├── Dockerfile                  # Docker конфигурация
├── requirements.txt            # Python зависимости
├── main.py                     # Основной файл приложения
└── GITHUB_DEPLOY_SETUP.md     # Эта инструкция
```

## Устранение неполадок

### Ошибка аутентификации
- Проверьте правильность `GCP_SA_KEY`
- Убедитесь, что Service Account имеет нужные права

### Ошибка сборки Docker
- Проверьте `Dockerfile` и `.dockerignore`
- Убедитесь, что все зависимости в `requirements.txt`

### Ошибка деплоя
- Проверьте `PROJECT_ID` и `REGION`
- Убедитесь, что API включены в Google Cloud

### Webhook не работает
- Проверьте `BOT_TOKEN`
- Убедитесь, что `WEBHOOK_URL` правильный
- Проверьте логи Cloud Run

## Мониторинг

- **GitHub Actions**: Проверяйте статус деплоя в Actions tab
- **Google Cloud Console**: Мониторинг в Cloud Run
- **Логи**: `gcloud run logs tail ai-bot --region=us-central1`

## Обновление

При каждом push в ветку `main`:
1. GitHub Actions автоматически соберет новый Docker образ
2. Задеплоит его на Cloud Run
3. Обновит webhook URL

Никаких дополнительных действий не требуется!