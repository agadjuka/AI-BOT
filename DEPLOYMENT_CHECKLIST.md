# Чек-лист для проверки настроек деплоя

## ✅ 1. Google Cloud Project

### Проверьте:
- [ ] **PROJECT_ID**: `just-advice-470905-a3` (из config/secrets.py)
- [ ] **Регион**: `europe-west1` (из .github/workflows/deploy.yml)
- [ ] **Сервис**: `ai-bot` (из .github/workflows/deploy.yml)

### Включенные API:
- [ ] Cloud Run API
- [ ] Container Registry API  
- [ ] Cloud Build API

## ✅ 2. Service Account

### Проверьте права Service Account:
- [ ] **Cloud Run Admin** (`roles/run.admin`)
- [ ] **Storage Admin** (`roles/storage.admin`)
- [ ] **Service Account User** (`roles/iam.serviceAccountUser`)

### Команды для проверки:
```bash
# Проверить права Service Account
gcloud projects get-iam-policy just-advice-470905-a3 \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:github-actions@just-advice-470905-a3.iam.gserviceaccount.com"
```

## ✅ 3. GitHub Secrets

### В GitHub → Settings → Secrets and variables → Actions:

- [ ] **GCP_PROJECT_ID**: `just-advice-470905-a3`
- [ ] **GCP_SA_KEY**: JSON ключ Service Account

### Проверка JSON ключа:
```bash
# Создать новый ключ (если нужно)
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@just-advice-470905-a3.iam.gserviceaccount.com
```

## ✅ 4. Переменные окружения для Cloud Run

### В Google Cloud Console → Cloud Run → ai-bot → Edit & Deploy New Revision → Variables & Secrets:

- [ ] **BOT_TOKEN**: `8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE`
- [ ] **POSTER_TOKEN**: `853931:71424838d41a70ee724e07ef6c6f0774`
- [ ] **PROJECT_ID**: `just-advice-470905-a3`
- [ ] **PORT**: `8080` (автоматически устанавливается Cloud Run)

### Дополнительные переменные (если используются):
- [ ] **GOOGLE_APPLICATION_CREDENTIALS**: путь к файлу credentials (если используется)
- [ ] **LOCATION**: `us-central1` (из config/settings.py)
- [ ] **MODEL_NAME**: `gemini-2.5-flash` (из config/settings.py)

## ✅ 5. Файлы проекта

### Проверьте наличие файлов:
- [ ] `.github/workflows/deploy.yml` - GitHub Actions workflow
- [ ] `Dockerfile` - обновлен согласно требованиям
- [ ] `.dockerignore` - исключения для Docker
- [ ] `.gitignore` - исключения для Git
- [ ] `main.py` - поддерживает переменную PORT
- [ ] `requirements.txt` - все зависимости

### Проверьте содержимое Dockerfile:
```dockerfile
# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем твой код
CMD ["python", "main.py"]
```

## ✅ 6. Google Sheets настройки

### Проверьте в config/settings.py:
- [ ] **GOOGLE_SHEETS_CREDENTIALS**: `google_sheets_credentials.json`
- [ ] **GOOGLE_SHEETS_SPREADSHEET_ID**: `1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI`
- [ ] **GOOGLE_SHEETS_WORKSHEET_NAME**: `Лист1`

### Для Cloud Run:
- [ ] Файл `google_sheets_credentials.json` должен быть в корне проекта
- [ ] Или настроить переменную окружения `GOOGLE_APPLICATION_CREDENTIALS`

## ✅ 7. Тестирование

### Локальное тестирование:
```bash
# Сборка образа
docker build -t ai-bot-test .

# Запуск с переменными окружения
docker run -p 8080:8080 \
  -e BOT_TOKEN="8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE" \
  -e POSTER_TOKEN="853931:71424838d41a70ee724e07ef6c6f0774" \
  -e PROJECT_ID="just-advice-470905-a3" \
  ai-bot-test
```

### Проверка деплоя:
- [ ] Push в ветку `main`
- [ ] Проверка GitHub Actions (статус деплоя)
- [ ] Проверка Cloud Run (логи и метрики)
- [ ] Тестирование Telegram бота

## ✅ 8. Мониторинг

### После деплоя проверьте:
- [ ] **GitHub Actions**: статус в разделе Actions
- [ ] **Cloud Run**: логи в Google Cloud Console
- [ ] **Telegram бот**: отправьте `/start`
- [ ] **Health check**: `https://your-service-url/health`

## 🔧 Команды для устранения неполадок

### Проверка Service Account:
```bash
gcloud iam service-accounts list
gcloud iam service-accounts get-iam-policy github-actions@just-advice-470905-a3.iam.gserviceaccount.com
```

### Проверка API:
```bash
gcloud services list --enabled --filter="name:run.googleapis.com OR name:containerregistry.googleapis.com OR name:cloudbuild.googleapis.com"
```

### Проверка Cloud Run:
```bash
gcloud run services list --region=europe-west1
gcloud run services describe ai-bot --region=europe-west1
```

### Просмотр логов:
```bash
gcloud logs read --service=ai-bot --region=europe-west1 --limit=50
```
