# Быстрая настройка облачной версии

## Проблема
В облачной версии бот не может получить доступ к Google Sheets, потому что JSON файл с credentials не доступен в Cloud Run.

## Быстрое решение

### 1. Получите JSON credentials
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Выберите проект `just-advice-470905-a3`
3. Перейдите в "IAM & Admin" → "Service Accounts"
4. Найдите сервисный аккаунт или создайте новый
5. Создайте ключ (JSON) и скачайте файл

### 2. Настройте GitHub Secrets
1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте секрет `GOOGLE_APPLICATION_CREDENTIALS_JSON` со содержимым JSON файла

### 3. Проверьте доступ к таблице
1. Откройте [вашу Google Таблицу](https://docs.google.com/spreadsheets/d/1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI)
2. Нажмите "Поделиться" (Share)
3. Добавьте email сервисного аккаунта с правами "Редактор"

### 4. Деплой
```bash
# Автоматический деплой через GitHub Actions
git push origin main

# Или ручной деплой
gcloud builds submit --config cloudbuild.yaml
```

### 5. Проверка
После деплоя проверьте:
- `https://your-cloud-run-url/debug` - статус сервиса
- `https://your-cloud-run-url/` - health check

## Отладка
Если что-то не работает, проверьте логи:
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

## Структура JSON credentials
```json
{
  "type": "service_account",
  "project_id": "just-advice-470905-a3",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@just-advice-470905-a3.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```
