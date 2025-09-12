# AI Bot - Receipt Analysis 765

Telegram бот для анализа чеков с использованием Google Gemini AI.

## 🚀 Быстрый старт

### Локальная разработка
```bash
# 1. Настройка среды разработки
python dev_setup.py

# 2. Редактирование .env файла с вашими токенами
# 3. Запуск локальной версии
python run_local.py
```

### Production деплой
```bash
# Автоматический деплой при push в main ветку
git push origin main
```

## 📁 Структура проекта

```
AI Bot/
├── main.py                    # Production версия (FastAPI + webhook)
├── main_local.py             # Локальная версия (polling)
├── run_local.py              # Скрипт запуска локальной версии
├── dev_setup.py              # Настройка среды разработки
├── switch_mode.py            # Переключение между версиями
├── requirements.txt          # Production зависимости
├── requirements_local.txt    # Локальные зависимости
├── env.example              # Пример конфигурации
├── .env                     # Ваши токены (создать вручную)
├── config/                  # Конфигурация
│   ├── __init__.py
│   ├── settings.py         # Настройки бота и промпты
│   └── google_sheets_example.py  # Пример настройки Google Sheets
├── services/               # Сервисы
│   ├── __init__.py
│   ├── ai_service.py      # Сервис для работы с AI
│   ├── file_generator_service.py  # Генерация файлов для Google Sheets
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
├── google_sheets_handler.py  # Обработчик Google Sheets
├── test_google_sheets_config.py  # Тест конфигурации
├── README.md            # Документация
├── README_LOCAL.md      # Документация по локальной разработке
└── GOOGLE_SHEETS_SETUP.md  # Настройка Google Sheets
```

## 🔧 Режимы работы

| Режим | Файл | Протокол | Назначение |
|-------|------|----------|------------|
| **Production** | `main.py` | Webhook (FastAPI) | Деплой в Google Cloud Run |
| **Local** | `main_local.py` | Polling | Локальная разработка |

## 📖 Документация

- **[README_LOCAL.md](README_LOCAL.md)** - Подробная документация по локальной разработке
- **[GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)** - Настройка Google Sheets

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
- **🆕 Сопоставление ингредиентов с готовыми справочниками**

## Новая функциональность: Google Sheets

Добавлена возможность загрузки данных чека напрямую в Google Таблицы:

- 📊 **Загрузка в Google Sheets** - данные чека автоматически загружаются в Google Таблицу
- 🥬 **Сопоставление ингредиентов** - автоматическое сопоставление товаров с готовыми справочниками

### Настройка Google Sheets

Подробные инструкции по настройке см. в [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

### Быстрый тест конфигурациии

```bash
python test_google_sheets_config.py
```
