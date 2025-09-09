# AI Bot - Receipt Analysis

Telegram бот для анализа чеков с использованием Google Gemini AI.

## Структура проекта

```
AI Bot/
├── config/                 # Конфигурация
│   ├── __init__.py
│   ├── settings.py        # Настройки бота и промпты
│   └── google_sheets_example.py  # Пример настройки Google Sheets
├── services/              # Сервисы
│   ├── __init__.py
│   ├── ai_service.py      # Сервис для работы с AI
│   ├── file_generator_service.py  # Генерация файлов для Poster
│   ├── google_sheets_service.py   # Загрузка в Google Sheets
│   └── ingredient_matching_service.py  # Сопоставление ингредиентов
├── models/                # Модели данных
│   ├── __init__.py
│   ├── receipt.py         # Модели чека и элементов
│   └── ingredient_matching.py  # Модели сопоставления ингредиентов
├── handlers/              # Обработчики
│   ├── __init__.py
│   ├── message_handlers.py    # Обработчики сообщений
│   └── callback_handlers.py   # Обработчики callback'ов
├── utils/                 # Утилиты
│   ├── __init__.py
│   ├── formatters.py      # Форматирование данных
│   ├── receipt_processor.py   # Обработка данных чека
│   ├── ingredient_formatter.py  # Форматирование ингредиентов
│   ├── ingredient_storage.py   # Хранение сопоставлений
│   └── ui_manager.py      # Управление интерфейсом
├── validators/            # Валидация
│   ├── __init__.py
│   └── receipt_validator.py   # Валидация данных чека
├── data/                  # Данные
│   └── *.json            # Файлы сопоставления ингредиентов
├── main.py               # Главный файл запуска
├── poster_handler.py     # Обработчик Poster API
├── google_sheets_handler.py  # Обработчик Google Sheets
├── test_google_sheets_config.py  # Тест конфигурации
├── requirements.txt      # Зависимости
├── README.md            # Документация
└── GOOGLE_SHEETS_SETUP.md  # Настройка Google Sheets
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
- **🆕 Загрузка данных в Google Таблицы**
- **🆕 Генерация файлов для загрузки в Poster**
- **🆕 Сопоставление ингредиентов с готовыми справочниками**

## Новая функциональность: Google Sheets

Добавлена возможность загрузки данных чека напрямую в Google Таблицы:

- 📊 **Загрузка в Google Sheets** - данные чека автоматически загружаются в Google Таблицу
- 📄 **Генерация файлов для Poster** - создание файлов для загрузки в систему Poster
- 🥬 **Сопоставление ингредиентов** - автоматическое сопоставление товаров с готовыми справочниками

### Настройка Google Sheets

Подробные инструкции по настройке см. в [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

### Быстрый тест конфигурациии

```bash
python test_google_sheets_config.py
```
