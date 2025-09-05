# Настройка Google Sheets для AI Bot

## Обзор

Добавлена функциональность загрузки данных чека напрямую в Google Таблицы. Интерфейс полностью скопирован с функциональности "получить файл для загрузки в постер", но адаптирован для работы с Google Sheets.

## Что нужно настроить

### 1. Google Sheets API Credentials

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API
4. Создайте Service Account:
   - Перейдите в "IAM & Admin" → "Service Accounts"
   - Нажмите "Create Service Account"
   - Заполните название и описание
   - Создайте ключ (JSON) и скачайте файл
5. Скопируйте скачанный JSON файл в корень проекта как `google_sheets_credentials.json`

### 2. Google Sheets Spreadsheet

1. Создайте новую Google Таблицу
2. Скопируйте ID таблицы из URL (часть между `/d/` и `/edit`)
3. Предоставьте доступ Service Account к таблице:
   - Откройте таблицу
   - Нажмите "Поделиться"
   - Добавьте email Service Account (из JSON файла)
   - Дайте права "Редактор"

### 3. Конфигурация

Обновите `config/settings.py`:

```python
# Google Sheets settings
self.GOOGLE_SHEETS_CREDENTIALS: str = "google_sheets_credentials.json"  # Путь к файлу credentials
self.GOOGLE_SHEETS_SPREADSHEET_ID: str = "YOUR_SPREADSHEET_ID_HERE"  # ID таблицы
self.GOOGLE_SHEETS_WORKSHEET_NAME: str = "Receipts"  # Название листа

# Ingredient matching settings
self.INGREDIENT_LIST: dict = {
    "ingredient_name_lowercase": "ingredient_id",
    # Добавьте ваш список ингредиентов здесь
}
```

### 4. Список ингредиентов

Добавьте готовый список ингредиентов в `config/settings.py` в формате:
```python
self.INGREDIENT_LIST = {
    "tomato": "tomato_001",
    "cucumber": "cucumber_002",
    "carrot": "carrot_003",
    # ... и так далее
}
```

## Функциональность

### Кнопки в интерфейсе

- **📊 Загрузить в Google Sheets** - загружает данные чека в Google Таблицу
- **📄 Сгенерировать файл** - генерирует файл для загрузки в постер (как раньше)
- **✏️ Отредактировать сопоставления** - редактирует сопоставления ингредиентов

### Процесс работы

1. Пользователь загружает фото чека
2. Бот анализирует чек и извлекает данные
3. Пользователь видит таблицу с кнопками:
   - Загрузить в Google Sheets
   - Сгенерировать файл для постер
   - Отредактировать сопоставления
4. При нажатии "Загрузить в Google Sheets":
   - Загружается справочник ингредиентов из конфигурации
   - Выполняется сопоставление товаров с ингредиентами
   - Данные загружаются в Google Таблицу

### Структура данных в Google Sheets

| Timestamp | Item Name | Matched Ingredient | Quantity | Price per Unit | Total Amount | Match Status | Similarity Score |
|-----------|-----------|-------------------|----------|----------------|--------------|--------------|------------------|
| 2024-01-01 12:00:00 | Tomato | tomato | 3 | 12.50 | 37.50 | exact_match | 0.95 |

## Установка зависимостей

Добавьте в `requirements.txt`:

```
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
```

## Безопасность

- Никогда не коммитьте файл `google_sheets_credentials.json` в репозиторий
- Добавьте его в `.gitignore`
- Храните credentials в безопасном месте

## Отладка

Для проверки настройки запустите:

```python
from google_sheets_handler import validate_google_sheets_config
is_valid, message = validate_google_sheets_config()
print(f"Config valid: {is_valid}, Message: {message}")
```

## Примечания

- Функциональность полностью копирует интерфейс работы с постером
- Все кнопки работают аналогично
- Добавлены места для настройки API и списка ингредиентов
- Код готов к добавлению реальной интеграции с Google Sheets API
