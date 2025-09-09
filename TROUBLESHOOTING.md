# Устранение неполадок деплоя

## Проблема: Container failed to start and listen on port

### Симптомы:
```
ERROR: (gcloud.run.services.update) Revision 'xxx' is not ready and cannot serve traffic. 
The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout.
```

### Возможные причины:

1. **Отсутствуют переменные окружения** (BOT_TOKEN, WEBHOOK_URL)
2. **Ошибки в коде** при инициализации приложения
3. **Проблемы с зависимостями** (numpy, pandas)
4. **Неправильная конфигурация порта**

### Решения:

#### 1. Проверьте переменные окружения

Убедитесь, что в GitHub Secrets настроены:
- `BOT_TOKEN` - токен Telegram бота
- `WEBHOOK_URL` - URL вашего Cloud Run сервиса
- `GCP_PROJECT_ID` - ID Google Cloud проекта
- `GCP_SA_KEY` - ключ Service Account

#### 2. Используйте тестовую версию

Для проверки, что контейнер может запуститься, используйте `main_test.py`:

```bash
# Временно замените в Dockerfile
CMD ["python", "main_test.py"]
```

#### 3. Проверьте логи

```bash
# Получите логи Cloud Run
gcloud run logs tail ai-bot --region=us-central1

# Или через консоль Google Cloud
# https://console.cloud.google.com/logs/viewer
```

#### 4. Локальное тестирование

```bash
# Соберите образ локально
docker build -t ai-bot-test .

# Запустите с переменными окружения
docker run -p 8080:8080 -e BOT_TOKEN=your_token -e WEBHOOK_URL=http://localhost:8080 ai-bot-test

# Проверьте health check
curl http://localhost:8080/
```

#### 5. Пошаговая отладка

1. **Сначала деплойте тестовую версию**:
   ```bash
   # Используйте Dockerfile.test
   docker build -f Dockerfile.test -t gcr.io/PROJECT_ID/ai-bot:test .
   docker push gcr.io/PROJECT_ID/ai-bot:test
   
   # Деплойте тестовую версию
   gcloud run deploy ai-bot --image gcr.io/PROJECT_ID/ai-bot:test --region us-central1 --allow-unauthenticated
   ```

2. **Если тестовая версия работает**, проблема в основном коде

3. **Проверьте импорты** в main.py:
   ```python
   # Добавьте try-catch для всех импортов
   try:
       from config.settings import BotConfig
   except ImportError as e:
       print(f"Import error: {e}")
   ```

#### 6. Обновленный workflow для отладки

Добавьте в `.github/workflows/deploy.yml`:

```yaml
- name: Test container locally
  run: |
    # Соберите образ
    docker build -t test-container .
    
    # Запустите в фоне
    docker run -d -p 8080:8080 -e BOT_TOKEN=test test-container
    
    # Подождите
    sleep 10
    
    # Проверьте health check
    curl -f http://localhost:8080/ || exit 1
    
    # Остановите контейнер
    docker stop $(docker ps -q --filter ancestor=test-container)
```

### Проверочный список:

- [ ] Все переменные окружения настроены в GitHub Secrets
- [ ] Dockerfile использует правильный CMD
- [ ] Приложение слушает на порту 8080
- [ ] Нет ошибок импорта в коде
- [ ] Логи показывают успешный запуск
- [ ] Health check endpoint возвращает 200

### Быстрое решение:

1. Используйте `main_test.py` для первого деплоя
2. После успешного деплоя переключитесь на `main.py`
3. Добавьте обработку ошибок в код
4. Проверьте все переменные окружения
