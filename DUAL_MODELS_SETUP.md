# Поддержка двух моделей Gemini (Pro и Flash)

## Обзор

Ваш бот теперь поддерживает две модели Gemini:
- **Gemini 2.5 Pro** (основная) - более точная и мощная модель
- **Gemini 2.5 Flash** (быстрая) - быстрая модель для простых задач

## Конфигурация

### Настройки по умолчанию
- **Основная модель**: `gemini-2.5-pro` (Pro)
- **Локация**: `global` (для совместимости с google-generativeai)
- **Быстрая модель**: `gemini-2.5-flash` (Flash)

### Файлы конфигурации
- `config/settings.py` - основные настройки моделей
- `requirements.txt` - зависимости (google-generativeai)

## Использование

### Команды бота
- `/model_info` - показать информацию о текущей модели
- `/switch_model pro` - переключиться на Pro модель
- `/switch_model flash` - переключиться на Flash модель

### Программное использование

```python
from services.ai_service import AIServiceFactory
from config.settings import BotConfig
from config.prompts import PromptManager

# Инициализация
config = BotConfig()
prompt_manager = PromptManager()
factory = AIServiceFactory(config, prompt_manager)

# Получение сервисов
pro_service = factory.get_pro_service()      # Pro модель
flash_service = factory.get_flash_service()  # Flash модель
default_service = factory.get_default_service()  # По умолчанию Pro

# Переключение модели
service.switch_model("pro")    # Переключить на Pro
service.switch_model("flash")  # Переключить на Flash

# Информация о модели
info = service.get_current_model_info()
print(f"Текущая модель: {info['name']} ({info['type']})")
```

## Технические детали

### Архитектура
- `AIServiceFactory` - фабрика для создания сервисов с разными моделями
- `AIService` - основной сервис с поддержкой переключения моделей
- Кэширование сервисов для оптимизации производительности

### Модели
- **Pro**: `gemini-2.5-pro` - используется по умолчанию
- **Flash**: `gemini-2.5-flash` - доступна для переключения

### Локация
- Все модели используют `global` локацию для совместимости с google-generativeai SDK

## Установка зависимостей

```bash
pip install -r requirements.txt
```

Основные зависимости:
- `google-generativeai==0.8.3` - новый SDK для работы с Gemini
- `python-telegram-bot==20.7` - Telegram Bot API

## Проверка работы

Бот автоматически инициализируется с Pro моделью. Для проверки:

1. Запустите бота
2. Отправьте команду `/model_info`
3. Используйте `/switch_model flash` для переключения на Flash
4. Используйте `/switch_model pro` для возврата к Pro

## Примечания

- Переключение моделей доступно только администраторам
- Pro модель используется по умолчанию для максимального качества
- Flash модель доступна для быстрых операций
- Все настройки сохраняются в конфигурации
