# Пошаговая отладка деплоя

## Шаг 1: Максимально простая версия

Создана версия `main_simple.py` без внешних зависимостей:

```python
# Простой HTTP сервер на встроенном Python
# Никаких FastAPI, numpy, pandas и т.д.
```

## Шаг 2: Упрощенный Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY main_simple.py .
ENV PORT=8080
CMD ["python", "main_simple.py"]
```

## Шаг 3: Локальное тестирование

Перед деплоем протестируйте локально:

```bash
# Соберите образ
docker build -t ai-bot-simple .

# Запустите локально
docker run -p 8080:8080 ai-bot-simple

# В другом терминале проверьте
curl http://localhost:8080/
curl http://localhost:8080/health
```

## Шаг 4: Проверка логов

После деплоя проверьте логи:

```bash
# Получите логи Cloud Run
gcloud run logs tail ai-bot --region=us-central1 --limit=50

# Или через консоль
# https://console.cloud.google.com/logs/viewer
```

## Шаг 5: Если простая версия не работает

### Возможные проблемы:

1. **Неправильный регион** - проверьте в workflow
2. **Неправильный PROJECT_ID** - проверьте в GitHub Secrets
3. **Проблемы с правами** - проверьте Service Account
4. **Проблемы с сетью** - проверьте настройки Cloud Run

### Проверьте настройки в workflow:

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}  # Должен быть правильный
  SERVICE_NAME: ai-bot
  REGION: us-central1  # Проверьте регион
```

## Шаг 6: Альтернативный подход

Если простой сервер не работает, попробуйте:

### Вариант A: Используйте готовый образ

```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Вариант B: Проверьте права доступа

```bash
# Проверьте права Service Account
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Проверьте, что API включены
gcloud services list --enabled
```

## Шаг 7: Диагностика Cloud Run

```bash
# Получите информацию о сервисе
gcloud run services describe ai-bot --region=us-central1

# Проверьте ревизии
gcloud run revisions list --service=ai-bot --region=us-central1

# Получите детальные логи
gcloud run logs tail ai-bot --region=us-central1 --follow
```

## Шаг 8: Если ничего не помогает

1. **Создайте новый проект** Google Cloud
2. **Настройте заново** Service Account
3. **Проверьте все переменные** в GitHub Secrets
4. **Используйте другой регион** (например, europe-west1)

## Проверочный список:

- [ ] Локальное тестирование прошло успешно
- [ ] Все переменные окружения настроены
- [ ] Service Account имеет нужные права
- [ ] API включены в Google Cloud
- [ ] Регион правильный
- [ ] PROJECT_ID правильный
- [ ] Логи показывают запуск сервера
- [ ] Health check возвращает 200

## Быстрое решение:

Если ничего не работает, попробуйте деплой через Google Cloud Console:

1. Откройте Cloud Run в консоли
2. Создайте новый сервис
3. Загрузите образ вручную
4. Настройте переменные окружения
5. Проверьте, что работает
6. Затем настройте автоматический деплой
