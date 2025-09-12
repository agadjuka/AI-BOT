# Настройка Google Sheets для облачной версии

## Проблема
В облачной версии бот не может получить доступ к Google Sheets, потому что JSON файл с credentials не доступен в Cloud Run.

## Решение
Используем переменную окружения `GOOGLE_APPLICATION_CREDENTIALS_JSON` для передачи credentials через GitHub Secrets.

## Шаги настройки

### 1. Получите JSON файл credentials
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Выберите ваш проект
3. Перейдите в "IAM & Admin" → "Service Accounts"
4. Найдите или создайте сервисный аккаунт для бота
5. Создайте ключ (JSON) для этого сервисного аккаунта
6. Скачайте JSON файл

### 2. Настройте GitHub Secrets
1. Перейдите в ваш репозиторий на GitHub
2. Перейдите в Settings → Secrets and variables → Actions
3. Добавьте новый секрет:
   - **Name**: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
   - **Value**: Содержимое JSON файла (весь файл как одна строка)

### 3. Обновите Cloud Build
Файл `cloudbuild.yaml` уже обновлен для использования переменной окружения.

### 4. Проверьте права доступа
Убедитесь, что сервисный аккаунт имеет права:
- **Google Sheets API**: включен
- **Firestore API**: включен (если используется)
- **Vertex AI API**: включен (для AI функций)

### 5. Проверьте ID таблицы
В файле `config/settings.py` убедитесь, что `GOOGLE_SHEETS_SPREADSHEET_ID` правильный:
```python
self.GOOGLE_SHEETS_SPREADSHEET_ID: str = "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"
```

### 6. Проверьте доступ к таблице
Убедитесь, что сервисный аккаунт имеет доступ к вашей Google Таблице:
1. Откройте вашу Google Таблицу
2. Нажмите "Поделиться" (Share)
3. Добавьте email сервисного аккаунта с правами "Редактор" (Editor)

## Отладка

### Проверка через API
После деплоя проверьте статус через endpoint:
```
GET https://your-cloud-run-url/debug
```

В ответе должно быть:
```json
{
  "google_sheets_config": {
    "service_available": true,
    "credentials_path": "google_sheets_credentials.json",
    "spreadsheet_id": "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"
  },
  "environment_vars": {
    "GOOGLE_APPLICATION_CREDENTIALS_JSON": "***"
  }
}
```

### Логи Cloud Run
Проверьте логи Cloud Run для отладочной информации:
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

## Структура JSON credentials
JSON файл должен содержать:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
```

## Альтернативный способ (если GitHub Secrets не работает)
Можно использовать Cloud Build substitutions:
1. В `cloudbuild.yaml` замените `${_GOOGLE_APPLICATION_CREDENTIALS_JSON}` на реальный JSON
2. Или используйте Cloud Build triggers с переменными

## Проверка работы
После настройки:
1. Запустите бота
2. Отправьте фото чека
3. Выберите "Загрузить в Google Таблицы"
4. Проверьте, что данные появились в таблице
