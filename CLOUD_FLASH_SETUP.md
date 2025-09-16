# Облачная настройка с поддержкой Flash-модели

## Обзор

Облачная версия бота теперь поддерживает две модели Gemini:
- **Gemini 2.5 Pro** (основная) - использует `google.generativeai` с регионом `global`
- **Gemini 2.5 Flash** (быстрая) - использует `vertexai` с регионом `asia-southeast1` (Сингапур)

## Cloud Run конфигурация

### Переменные окружения
- `PROJECT_ID=just-advice-470905-a3` - ID проекта Google Cloud
- `GOOGLE_CLOUD_LOCATION=asia-southeast1` - Регион для Flash-модели (Сингапур)
- `DEFAULT_MODEL=pro` - Модель по умолчанию (Pro)
- `GEMINI_ANALYSIS_MODE=production` - Режим анализа

### Регион развертывания
- **Cloud Run регион**: `us-central1` (оптимальный для Gemini)
- **Flash-модель регион**: `asia-southeast1` (Сингапур)
- **Pro-модель регион**: `global`

### Настройки ресурсов
- **Память**: 1Gi
- **CPU**: 1
- **Максимум экземпляров**: 10
- **Минимум экземпляров**: 0
- **Таймаут**: 300 секунд

## Архитектура моделей

### Flash-модель (TURBO режим)
- **SDK**: `vertexai` (как в откатной версии)
- **Регион**: `asia-southeast1` (Сингапур)
- **Инициализация**: `vertexai.init(project=PROJECT_ID, location="asia-southeast1")`
- **Fallback**: `us-central1` если `asia-southeast1` недоступен

### Pro-модель (по умолчанию)
- **SDK**: `google.generativeai`
- **Регион**: `global`
- **Инициализация**: `genai.configure()`

## Аутентификация

### Cloud Run
- Использует Application Default Credentials (ADC)
- Сервисный аккаунт: `ai-bot-service-account@just-advice-470905-a3.iam.gserviceaccount.com`
- Переменная `GOOGLE_APPLICATION_CREDENTIALS_JSON` передается через GitHub Secrets

### Локальная разработка
- Использует файл `just-advice-470905-a3-ee25a8712359.json`
- Fallback на Application Default Credentials

## Развертывание

### Автоматическое развертывание
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
  --set-env-vars="PROJECT_ID=just-advice-470905-a3,GOOGLE_CLOUD_LOCATION=asia-southeast1,DEFAULT_MODEL=pro"
```

## Проверка работы

### Команды бота
- `/model_info` - информация о текущей модели
- `/switch_model pro` - переключить на Pro
- `/switch_model flash` - переключить на Flash

### Логи Cloud Run
```
✅ Vertex AI инициализирован для Flash модели (регион: asia-southeast1)
✅ Google Generative AI инициализирован для Pro модели (регион: global)
```

## Технические детали

### Зависимости
- `google-cloud-aiplatform==1.71.1` - для Flash-модели (vertexai)
- `google-generativeai==0.8.3` - для Pro-модели

### Обработка изображений
- **Flash**: `Part.from_data(data=image_data, mime_type="image/jpeg")`
- **Pro**: `{"mime_type": "image/jpeg", "data": image_data}`

### Параллельная обработка
- Пул AI сервисов для изоляции запросов
- ThreadPoolExecutor для асинхронной обработки
- Fallback механизмы для регионов

## Примечания

- Flash-модель работает точно так же, как в откатной версии
- TURBO режим автоматически использует Flash-модель
- OpenCV анализ может выбрать Flash-модель для простых чеков
- Все настройки совместимы с существующей архитектурой
