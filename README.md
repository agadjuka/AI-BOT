# AI Bot - Receipt Analysis

Telegram бот для анализа чеков с использованием Google Gemini AI.

## Структура проекта

```
AI Bot/
├── config/                 # Конфигурация
│   ├── __init__.py
│   └── settings.py        # Настройки бота и промпты
├── services/              # Сервисы
│   ├── __init__.py
│   └── ai_service.py      # Сервис для работы с AI
├── models/                # Модели данных
│   ├── __init__.py
│   └── receipt.py         # Модели чека и элементов
├── handlers/              # Обработчики
│   ├── __init__.py
│   ├── message_handlers.py    # Обработчики сообщений
│   └── callback_handlers.py   # Обработчики callback'ов
├── utils/                 # Утилиты
│   ├── __init__.py
│   ├── formatters.py      # Форматирование данных
│   └── receipt_processor.py   # Обработка данных чека
├── validators/            # Валидация
│   ├── __init__.py
│   └── receipt_validator.py   # Валидация данных чека
├── main.py               # Главный файл запуска
├── requirements.txt      # Зависимости
└── README.md            # Документация
```

## Установка и запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения для Google Cloud (если необходимо)

3. Запустите бота:
```bash
python main.py
```

## Принципы SOLID

Проект структурирован в соответствии с принципами SOLID:

- **Single Responsibility Principle**: Каждый модуль отвечает за одну задачу
- **Open/Closed Principle**: Сервисы открыты для расширения, закрыты для модификации
- **Liskov Substitution Principle**: Модели данных взаимозаменяемы
- **Interface Segregation Principle**: Интерфейсы разделены по функциональности
- **Dependency Inversion Principle**: Зависимости инвертированы через внедрение

## Функциональность

- Анализ фото чеков с помощью Google Gemini AI
- Интерактивное редактирование данных чека
- Автоматическая валидация и расчеты
- Форматирование данных для мобильных устройств
- Управление строками чека (добавление, удаление, редактирование)
