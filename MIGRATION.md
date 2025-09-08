# Миграция с Polling на Webhook

Этот документ описывает изменения, необходимые для перехода с polling режима на webhook режим для работы с Google Cloud Run.

## Основные изменения

### 1. main.py

**Было (polling):**
```python
def main():
    # ... инициализация ...
    application.run_polling()
```

**Стало (webhook):**
```python
# Flask приложение
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    # Обработка обновлений от Telegram
    
def main():
    # ... инициализация ...
    app.run(host="0.0.0.0", port=port)
```

### 2. requirements.txt

Добавлены зависимости:
```
flask==3.0.0
gunicorn==21.2.0
```

### 3. Dockerfile

**Было:**
```dockerfile
CMD ["python", "main.py"]
```

**Стало:**
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "1", "--threads", "2", "--timeout", "120", "main:app"]
```

## Новые файлы

1. **setup_webhook.py** - скрипт для настройки webhook в Telegram
2. **deploy.sh** / **deploy.ps1** - скрипты для быстрого развертывания
3. **DEPLOYMENT.md** - подробная инструкция по развертыванию

## Преимущества webhook режима

1. **Масштабируемость** - Cloud Run может автоматически масштабировать количество экземпляров
2. **Надежность** - нет необходимости поддерживать постоянное соединение
3. **Экономичность** - плата только за время обработки запросов
4. **Простота развертывания** - стандартный HTTP контейнер

## Обратная совместимость

Для локальной разработки можно использовать старый режим polling, создав файл `main_polling.py`:

```python
# main_polling.py - для локальной разработки
from main import create_application, cleanup_old_files_periodically
from utils.ingredient_storage import IngredientStorage
import threading

def main():
    application = create_application()
    ingredient_storage = IngredientStorage(max_age_hours=1)
    
    cleanup_thread = threading.Thread(
        target=cleanup_old_files_periodically, 
        args=(ingredient_storage,), 
        daemon=True
    )
    cleanup_thread.start()
    
    application.run_polling()

if __name__ == "__main__":
    main()
```

## Миграция существующего бота

1. **Остановите текущий бот** (если запущен)
2. **Обновите код** согласно изменениям выше
3. **Разверните на Cloud Run**:
   ```bash
   ./deploy.sh YOUR_PROJECT_ID YOUR_SERVICE_NAME
   ```
4. **Настройте webhook**:
   ```bash
   python setup_webhook.py YOUR_BOT_TOKEN https://YOUR_SERVICE_URL/webhook
   ```
5. **Проверьте работу**:
   ```bash
   python setup_webhook.py YOUR_BOT_TOKEN --info
   ```

## Откат на polling

Если нужно вернуться к polling режиму:

1. **Удалите webhook**:
   ```bash
   python setup_webhook.py YOUR_BOT_TOKEN --delete
   ```
2. **Остановите Cloud Run сервис**
3. **Запустите локально** с `main_polling.py`

## Мониторинг

После миграции следите за:
- Логами Cloud Run
- Метриками производительности
- Статусом webhook
- Ошибками обработки запросов

## Troubleshooting

### Webhook не работает
- Проверьте URL сервиса
- Убедитесь, что сервис запущен
- Проверьте логи Cloud Run

### Ошибки обработки
- Проверьте переменные окружения
- Убедитесь в корректности токена бота
- Проверьте права доступа к Google Cloud

### Таймауты
- Увеличьте timeout в настройках Cloud Run
- Оптимизируйте обработку запросов
