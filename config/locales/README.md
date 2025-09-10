# LocaleManager - Система локализации

`LocaleManager` - это класс для управления локализацией в AI Bot, который поддерживает получение языка из `context.user_data`, возврат текстов по ключам, интерполяцию переменных и fallback на русский язык.

## Основные возможности

- ✅ Получение языка из `context.user_data`
- ✅ Возврат текстов по ключам
- ✅ Интерполяция переменных в формате `{variable}`
- ✅ Fallback на русский язык
- ✅ Поддержка русского и английского языков
- ✅ Установка языка пользователя

## Использование

### Базовое использование

```python
from config.locales.locale_manager import LocaleManager

# Создание экземпляра
locale_manager = LocaleManager()

# Получение текста (язык определяется из context)
text = locale_manager.get_text('welcome', context)

# Получение текста с указанием языка
text = locale_manager.get_text('welcome', language='en')

# Получение текста с интерполяцией переменных
text = locale_manager.get_text('receipt_processing_with_name', context, 
                              receipt_name='Название чека')
```

### Интерполяция переменных

Поддерживается формат `{variable}` и `{variable:format}`:

```python
# Простая интерполяция
text = locale_manager.get_text('ingredient_count', context, count=5)
# Результат: "Найдено ингредиентов: 5"

# Интерполяция с форматированием
text = locale_manager.get_text('file_generated_with_name', context, 
                              filename='receipt.xlsx')
# Результат: "Файл 'receipt.xlsx' успешно сгенерирован"
```

### Управление языком пользователя

```python
# Получение языка из context
language = locale_manager.get_language_from_context(context)

# Установка языка пользователя
success = locale_manager.set_user_language(context, 'en')

# Проверка поддержки языка
is_supported = locale_manager.is_language_supported('en')

# Получение списка доступных языков
languages = locale_manager.get_available_languages()
```

## Структура файлов

```
config/locales/
├── locale_manager.py    # Основной класс LocaleManager
├── ru.py               # Русские переводы
├── en.py               # Английские переводы
├── id.py               # Индонезийские переводы
└── README.md           # Документация
```

## Добавление новых переводов

1. Добавьте ключ и перевод в `ru.py`:
```python
RU_TRANSLATIONS = {
    # ... существующие переводы ...
    'new_key': 'Новый текст',
    'new_key_with_vars': 'Текст с {variable}',
}
```

2. Добавьте соответствующий перевод в `en.py` и `id.py`:
```python
EN_TRANSLATIONS = {
    # ... существующие переводы ...
    'new_key': 'New text',
    'new_key_with_vars': 'Text with {variable}',
}

ID_TRANSLATIONS = {
    # ... существующие переводы ...
    'new_key': 'Teks baru',
    'new_key_with_vars': 'Teks dengan {variable}',
}
```

## Fallback механизм

Если запрашиваемый ключ не найден в текущем языке, система автоматически ищет его в русском языке (язык по умолчанию). Если ключ не найден и там, возвращается сам ключ.

## Поддерживаемые языки

- `ru` - Русский (язык по умолчанию)
- `en` - Английский
- `id` - Индонезийский

## Примеры использования в коде

```python
# В обработчике сообщений
def handle_message(update, context):
    # Получение локализованного текста
    welcome_text = locale_manager.get_text('welcome', context)
    await update.message.reply_text(welcome_text)
    
    # С интерполяцией
    processing_text = locale_manager.get_text('receipt_processing_with_name', 
                                            context, 
                                            receipt_name='Чек №123')
    await update.message.reply_text(processing_text)
```
