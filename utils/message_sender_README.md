# MessageSender

Класс `MessageSender` предоставляет централизованные методы для отправки различных типов сообщений в Telegram боте.

## Основные методы

### `send_long_message_with_keyboard(update, context, text, reply_markup, parse_mode='Markdown')`
Отправляет длинное сообщение с клавиатурой, автоматически разбивая его на части при необходимости.

**Параметры:**
- `update`: Объект обновления Telegram
- `context`: Контекст бота
- `text`: Текст сообщения
- `reply_markup`: Разметка inline клавиатуры
- `parse_mode`: Режим парсинга текста (по умолчанию 'Markdown')

**Возвращает:** Объект отправленного сообщения

### `send_temp_message(update, context, text, duration=3, parse_mode='Markdown')`
Отправляет временное сообщение, которое автоматически удаляется через указанное время.

**Параметры:**
- `update`: Объект обновления Telegram
- `context`: Контекст бота
- `text`: Текст сообщения
- `duration`: Время до удаления в секундах (по умолчанию 3)
- `parse_mode`: Режим парсинга текста (по умолчанию 'Markdown')

**Возвращает:** Объект отправленного сообщения

### `send_error_message(update, context, text, duration=5, parse_mode='Markdown')`
Отправляет сообщение об ошибке с соответствующим стилем.

**Параметры:**
- `update`: Объект обновления Telegram
- `context`: Контекст бота
- `text`: Текст ошибки
- `duration`: Время до удаления в секундах (по умолчанию 5)
- `parse_mode`: Режим парсинга текста (по умолчанию 'Markdown')

**Возвращает:** Объект отправленного сообщения

### `send_success_message(update, context, text, duration=3, parse_mode='Markdown')`
Отправляет сообщение об успехе с соответствующим стилем.

**Параметры:**
- `update`: Объект обновления Telegram
- `context`: Контекст бота
- `text`: Текст сообщения об успехе
- `duration`: Время до удаления в секундах (по умолчанию 3)
- `parse_mode`: Режим парсинга текста (по умолчанию 'Markdown')

**Возвращает:** Объект отправленного сообщения

## Дополнительные методы

### `send_info_message(update, context, text, duration=4, parse_mode='Markdown')`
Отправляет информационное сообщение.

### `send_warning_message(update, context, text, duration=4, parse_mode='Markdown')`
Отправляет предупреждающее сообщение.

### `send_processing_message(update, context, text="Обрабатываю...", duration=10)`
Отправляет сообщение о процессе обработки.

### `send_confirmation_message(update, context, text, duration=5)`
Отправляет сообщение подтверждения.

## Вспомогательные методы

### `format_error_message(error, context="")`
Форматирует исключение в удобочитаемое сообщение об ошибке.

### `format_success_message(action, details="")`
Форматирует сообщение об успехе с действием и деталями.

### `format_info_message(title, content)`
Форматирует информационное сообщение с заголовком и содержимым.

### `format_warning_message(warning, suggestion="")`
Форматирует предупреждающее сообщение с рекомендацией.

## Пример использования

```python
from utils.message_sender import MessageSender
from config.settings import BotConfig

# Инициализация
config = BotConfig()
message_sender = MessageSender(config)

# Отправка сообщения об успехе
await message_sender.send_success_message(
    update, context, 
    "Данные успешно сохранены!"
)

# Отправка сообщения об ошибке
await message_sender.send_error_message(
    update, context, 
    "Не удалось сохранить данные. Попробуйте еще раз."
)

# Отправка длинного сообщения с клавиатурой
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Да", callback_data="yes")],
    [InlineKeyboardButton("Нет", callback_data="no")]
])
await message_sender.send_long_message_with_keyboard(
    update, context, 
    "Очень длинный текст сообщения...", 
    keyboard
)

# Отправка временного сообщения
await message_sender.send_temp_message(
    update, context, 
    "Это сообщение исчезнет через 5 секунд", 
    duration=5
)
```

## Интеграция с существующим кодом

Класс `MessageSender` можно легко интегрировать в существующие обработчики:

```python
# В обработчике сообщений
async def handle_some_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Выполняем действие
        result = await some_operation()
        
        # Отправляем сообщение об успехе
        await self.message_sender.send_success_message(
            update, context, 
            f"Операция выполнена: {result}"
        )
        
    except Exception as e:
        # Отправляем сообщение об ошибке
        await self.message_sender.send_error_message(
            update, context, 
            self.message_sender.format_error_message(e, "При выполнении операции")
        )
```

## Особенности

- Автоматическое разбиение длинных сообщений
- Стилизация сообщений с эмодзи и форматированием
- Автоматическое удаление временных сообщений
- Обработка ошибок при удалении сообщений
- Поддержка различных режимов парсинга текста
- Интеграция с существующей архитектурой бота
