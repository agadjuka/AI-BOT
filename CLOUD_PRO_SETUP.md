# Cloud Run настройка с Pro моделью

## Обзор

Ваш бот настроен для работы в Google Cloud Run с **Gemini 2.5 Pro** моделью по умолчанию.

## Cloud конфигурация

### Переменные окружения
- `DEFAULT_MODEL=pro` - Pro модель по умолчанию
- `GOOGLE_CLOUD_LOCATION=global` - Global локация для google-generativeai
- `PROJECT_ID=just-advice-470905-a3` - ID проекта Google Cloud

### Регион развертывания
- **Регион**: `us-central1` (оптимальный для Gemini Pro)
- **Платформа**: Cloud Run (managed)

### Настройки ресурсов
- **Память**: 1Gi
- **CPU**: 1
- **Максимум экземпляров**: 10
- **Минимум экземпляров**: 0
- **Таймаут**: 300 секунд

## Развертывание

### Автоматическое развертывание через Cloud Build
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Ручное развертывание
```bash
gcloud run deploy ai-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --timeout 300 \
  --set-env-vars="DEFAULT_MODEL=pro,GOOGLE_CLOUD_LOCATION=global"
```

## Модели в Cloud

### По умолчанию
- **Модель**: `gemini-2.5-pro`
- **Тип**: Pro (высокое качество)
- **Локация**: global

### Доступные команды
- `/model_info` - информация о текущей модели
- `/switch_model pro` - переключить на Pro
- `/switch_model flash` - переключить на Flash

## Технические детали

### SDK
- Используется `google-generativeai` вместо устаревшего `vertexai`
- Application Default Credentials (ADC) для аутентификации
- Global локация для совместимости

### Конфигурация
- Настройки читаются из переменных окружения
- Fallback на значения по умолчанию
- Поддержка переключения моделей в runtime

## Мониторинг

### Логи
- Cloud Logging включен
- Логи доступны в Google Cloud Console
- Уровень логирования: INFO

### Метрики
- Время ответа модели
- Количество запросов
- Использование ресурсов

## Безопасность

### Аутентификация
- Service Account для Cloud Run
- Application Default Credentials
- Безопасное хранение секретов

### Доступ
- Только администраторы могут переключать модели
- Whitelist для доступа к боту
- Защищенные команды

## Проверка работы

После развертывания проверьте:
1. Бот отвечает на команды
2. `/model_info` показывает Pro модель
3. Анализ чеков работает корректно
4. Переключение на Flash работает

## Поддержка

При проблемах проверьте:
- Логи в Cloud Console
- Переменные окружения
- Права доступа Service Account
- Квоты API Gemini
