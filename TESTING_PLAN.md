# План пошагового тестирования

## ✅ Шаг 1: Простая версия (РАБОТАЕТ)
- `main_simple.py` - простой HTTP сервер
- Без зависимостей
- **Результат**: ✅ Запустилось

## 🔄 Шаг 2: FastAPI версия (ТЕСТИРУЕМ)
- `main_fastapi.py` - FastAPI без Telegram
- Зависимости: `fastapi`, `uvicorn`
- **Тест**: Деплой и проверка

## 🔄 Шаг 3: Telegram версия (СЛЕДУЮЩИЙ)
- `main_telegram.py` - с Telegram Bot API
- Зависимости: `python-telegram-bot`, `fastapi`, `uvicorn`
- **Тест**: Деплой и проверка webhook

## 🔄 Шаг 4: С Google AI (СЛЕДУЮЩИЙ)
- Добавить `google-cloud-aiplatform`, `vertexai`
- **Тест**: Деплой и проверка

## 🔄 Шаг 5: С numpy/pandas (ПРОБЛЕМНЫЙ)
- Добавить `numpy`, `pandas`
- **Тест**: Деплой и проверка

## 🔄 Шаг 6: Полная версия (ФИНАЛЬНЫЙ)
- `main.py` - полная версия
- Все зависимости
- **Тест**: Деплой и проверка

## Текущий статус:

### Тестируем сейчас: FastAPI версия
```bash
# Деплой
git add .
git commit -m "Test FastAPI version"
git push origin main

# Проверка
curl https://your-service-url/
curl https://your-service-url/health
```

### Если FastAPI работает, переходим к Telegram версии
```bash
# Обновить Dockerfile для main_telegram.py
# Деплой и проверка webhook
```

### Если Telegram работает, добавляем Google AI
```bash
# Добавить google-cloud-aiplatform
# Деплой и проверка
```

### Если Google AI работает, добавляем numpy/pandas
```bash
# Добавить numpy, pandas
# Деплой и проверка
```

## Возможные проблемы:

1. **numpy/pandas** - требуют компиляции, могут вызывать проблемы
2. **google-cloud-aiplatform** - большие зависимости
3. **Импорты в main.py** - могут быть циклические импорты
4. **Переменные окружения** - BOT_TOKEN, WEBHOOK_URL

## Решения:

1. **Для numpy/pandas**: использовать предкомпилированные версии
2. **Для Google AI**: добавить по одной зависимости
3. **Для импортов**: проверить все импорты в main.py
4. **Для переменных**: добавить проверки и fallback значения
