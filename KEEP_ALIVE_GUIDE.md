# Keep-Alive механизм для Cloud Run

## Описание

Механизм keep-alive предотвращает "холодный старт" и выключение контейнера в Google Cloud Run из-за отсутствия трафика, не изменяя настройки `min-instances`.

## Как это работает

1. **Получение публичного URL**: Приложение получает свой внешний URL из переменной окружения `SERVICE_URL`
2. **Фоновая задача**: Создается асинхронная задача `keep_alive_ping()`, которая каждые 5 минут отправляет HTTP-запрос на собственный `/health` эндпоинт
3. **Эндпоинт для пингов**: Создан специальный эндпоинт `/health` для приема keep-alive запросов
4. **Управление жизненным циклом**: Используется FastAPI lifespan для автоматического запуска и остановки задачи

## Компоненты

### 1. Переменная окружения SERVICE_URL

```bash
# В Cloud Run автоматически устанавливается Google
SERVICE_URL=https://your-service-name-hash-uc.a.run.app
```

### 2. Функция keep_alive_ping()

```python
async def keep_alive_ping(service_url: str) -> None:
    """Асинхронная функция для отправки keep-alive пингов на собственный URL"""
    while True:
        try:
            await asyncio.sleep(300)  # 5 минут
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{service_url}/health")
                if response.status_code == 200:
                    print("💓 Keep-alive ping sent successfully.")
        except Exception as e:
            print(f"❌ Keep-alive ping failed: {e}")
```

### 3. Эндпоинт /health

```python
@app.get("/health")
async def health_ping():
    """Health ping endpoint для keep-alive запросов"""
    return {"status": "ok"}
```

### 4. Lifespan управление

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск при старте
    service_url = os.getenv("SERVICE_URL")
    if service_url:
        keep_alive_task_obj = asyncio.create_task(keep_alive_ping(service_url))
    
    yield
    
    # Остановка при выключении
    if keep_alive_task_obj and not keep_alive_task_obj.done():
        keep_alive_task_obj.cancel()
```

## Логика работы

1. **При запуске приложения**:
   - Проверяется наличие переменной `SERVICE_URL`
   - Если переменная установлена, запускается фоновая задача keep-alive
   - Если переменная не установлена (локальный режим), keep-alive отключается

2. **Во время работы**:
   - Каждые 5 минут отправляется GET-запрос на `{SERVICE_URL}/health`
   - При успешном ответе (200 OK) выводится сообщение об успехе
   - При ошибке выводится сообщение об ошибке, но цикл продолжается

3. **При остановке приложения**:
   - Keep-alive задача корректно отменяется
   - Выводится сообщение об отмене задачи

## Преимущества

- ✅ **Автоматическое управление**: Задача запускается и останавливается автоматически
- ✅ **Условная активация**: Работает только в Cloud Run (когда установлен SERVICE_URL)
- ✅ **Устойчивость к ошибкам**: Продолжает работу даже при сетевых ошибках
- ✅ **Минимальное потребление ресурсов**: Простые HTTP-запросы каждые 5 минут
- ✅ **Логирование**: Подробные логи для мониторинга работы

## Мониторинг

### Логи keep-alive

```
💓 Keep-alive ping запущен для https://your-service-name-hash-uc.a.run.app
💓 Keep-alive ping sent successfully.
💓 Keep-alive ping sent successfully.
```

### Проверка статуса

Можно проверить статус keep-alive через эндпоинты:

- `GET /` - общая информация о приложении
- `GET /health` - простой health check
- `GET /keepalive` - детальная информация о keep-alive

## Настройка

### Для Cloud Run

Никаких дополнительных настроек не требуется. Переменная `SERVICE_URL` автоматически устанавливается Google Cloud Run.

### Для локальной разработки

Keep-alive автоматически отключается, если `SERVICE_URL` не установлен:

```
⚠️ SERVICE_URL не установлен - keep-alive отключен (локальный режим)
```

## Устранение неполадок

### Keep-alive не запускается

1. Проверьте, что переменная `SERVICE_URL` установлена
2. Проверьте логи при запуске приложения
3. Убедитесь, что приложение запущено в Cloud Run

### Ошибки HTTP-запросов

1. Проверьте, что эндпоинт `/health` доступен
2. Проверьте сетевую связность
3. Проверьте таймауты (установлен 30 секунд)

### Высокое потребление ресурсов

1. Интервал пингов можно изменить в коде (по умолчанию 5 минут)
2. Таймаут HTTP-запросов можно настроить (по умолчанию 30 секунд)

## Технические детали

- **Интервал пингов**: 5 минут (300 секунд)
- **Таймаут HTTP-запросов**: 30 секунд
- **Библиотека HTTP-клиента**: httpx (асинхронная)
- **Обработка ошибок**: Продолжение работы при любых ошибках
- **Логирование**: Подробные логи для отладки