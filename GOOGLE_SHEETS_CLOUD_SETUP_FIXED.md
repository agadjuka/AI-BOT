# Исправление проблемы с Google Sheets в облачной версии

## Проблема
Облачная версия не может получить доступ к Google Sheets в трех местах:
1. Проверка доступа к таблице при добавлении
2. Загрузка данных в таблицу  
3. Отмена загрузки данных

## Причины проблемы

### 1. Неправильная инициализация сервиса
- В `main.py` GoogleSheetsService инициализируется с жестко заданным путем к файлу `google_sheets_credentials_fixed.json`
- В облачной среде этот файл не существует

### 2. Отсутствие fallback на Application Default Credentials
- Код не пытается использовать ADC как последний вариант

### 3. Недостаточная диагностика
- Нет проверки доступа к таблице при инициализации

## Исправления

### 1. Обновлен GoogleSheetsService
- Добавлен fallback на Application Default Credentials (ADC)
- Улучшена диагностика ошибок
- Добавлена проверка существования файла credentials

### 2. Обновлен main.py
- Исправлена инициализация GoogleSheetsService для облачной среды
- Добавлена проверка доступа к таблице при запуске
- Улучшена диагностика конфигурации

### 3. Обновлен cloudbuild.yaml
- Добавлен service account для Cloud Run
- Улучшена передача переменных окружения

## Настройка секретов в GitHub

### 1. Создайте Service Account
```bash
# Создайте service account
gcloud iam service-accounts create ai-bot-service-account \
    --display-name="AI Bot Service Account" \
    --description="Service account for AI Bot Google Sheets access"

# Создайте ключ
gcloud iam service-accounts keys create ai-bot-key.json \
    --iam-account=ai-bot-service-account@just-advice-470905-a3.iam.gserviceaccount.com

# Назначьте роли
gcloud projects add-iam-policy-binding just-advice-470905-a3 \
    --member="serviceAccount:ai-bot-service-account@just-advice-470905-a3.iam.gserviceaccount.com" \
    --role="roles/spreadsheets.editor"

gcloud projects add-iam-policy-binding just-advice-470905-a3 \
    --member="serviceAccount:ai-bot-service-account@just-advice-470905-a3.iam.gserviceaccount.com" \
    --role="roles/firestore.user"
```

### 2. Настройте GitHub Secrets
В настройках репозитория GitHub (Settings → Secrets and variables → Actions) добавьте:

- `GOOGLE_SHEETS_CREDENTIALS_JSON` - содержимое файла `ai-bot-key.json`
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - содержимое файла `ai-bot-key.json` (для совместимости)
- `BOT_TOKEN` - токен Telegram бота
- `PROJECT_ID` - `just-advice-470905-a3`

### 3. Предоставьте доступ к таблице
1. Откройте Google Sheets таблицу
2. Нажмите "Поделиться"
3. Добавьте email service account: `ai-bot-service-account@just-advice-470905-a3.iam.gserviceaccount.com`
4. Установите права "Редактор"

## Тестирование

### Локальное тестирование
```bash
# Установите переменную окружения
export GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account",...}'

# Запустите тест
python test_google_sheets_cloud.py
```

### Облачное тестирование
После деплоя проверьте логи Cloud Run:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-bot" \
    --limit=50 --format="table(timestamp,severity,textPayload)" \
    --project=just-advice-470905-a3
```

## Ожидаемые результаты

После исправлений в логах должно появиться:
```
✅ Google Sheets credentials loaded from GOOGLE_SHEETS_CREDENTIALS_JSON
✅ Google Sheets service initialized successfully
✅ Google Sheets access verified - spreadsheet title: [Название таблицы]
```

## Дополнительные проверки

### 1. Проверьте права service account
```bash
gcloud projects get-iam-policy just-advice-470905-a3 \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:ai-bot-service-account@just-advice-470905-a3.iam.gserviceaccount.com"
```

### 2. Проверьте доступ к таблице
```bash
# Используйте service account для доступа к таблице
gcloud auth activate-service-account --key-file=ai-bot-key.json
gcloud auth list
```

### 3. Проверьте API
Убедитесь, что Google Sheets API включен:
```bash
gcloud services enable sheets.googleapis.com --project=just-advice-470905-a3
```

## Устранение неполадок

### Ошибка 403 (Forbidden)
- Проверьте права service account
- Убедитесь, что таблица доступна для service account

### Ошибка 404 (Not Found)
- Проверьте правильность ID таблицы
- Убедитесь, что таблица существует

### Ошибка 401 (Unauthorized)
- Проверьте правильность credentials
- Убедитесь, что ключ не истек

### Service не инициализирован
- Проверьте переменные окружения
- Убедитесь, что JSON credentials корректный
