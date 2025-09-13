# Google Sheets Manager

Модуль для управления Google-таблицами пользователей в Telegram-боте с использованием Firestore.

## Описание

`GoogleSheetsManager` предоставляет асинхронные функции для управления пользовательскими Google-таблицами, включая настройку маппинга колонок для записи данных из чеков.

## Структура данных в Firestore

```
users/{telegram_user_id}/
  └── google_sheets/
      └── {sheet_doc_id}/
          ├── sheet_url (string)
          ├── sheet_id (string) 
          ├── friendly_name (string)
          ├── sheet_name (string) - Default: "Sheet1"
          ├── is_default (boolean)
          ├── created_at (timestamp)
          ├── data_start_row (integer)
          └── column_mapping (map)
              ├── check_date -> "A"
              ├── product_name -> "B"
              ├── quantity -> "C"
              ├── price_per_item -> "D"
              └── total_price -> "E"
```

## Стандартные ключи данных

Модуль работает со следующими стандартными ключами данных из чеков:
- `check_date` - дата чека
- `product_name` - название товара
- `quantity` - количество
- `price_per_item` - цена за единицу
- `total_price` - общая цена

## API

### Инициализация

```python
from services.google_sheets_manager import get_google_sheets_manager

# Использование глобального экземпляра Firestore
manager = get_google_sheets_manager()

# Или с передачей конкретного экземпляра Firestore
manager = get_google_sheets_manager(db_instance)
```

### Методы

#### `add_user_sheet(user_id, sheet_url, sheet_id, friendly_name)`

Добавляет новую Google-таблицу для пользователя с дефолтным маппингом колонок.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `sheet_url` (str): Полный URL Google-таблицы
- `sheet_id` (str): ID документа Google Sheets
- `friendly_name` (str): Понятное имя таблицы

**Возвращает:**
- `str`: ID созданного документа или `False` при ошибке

**Особенности:**
- Первая таблица пользователя автоматически становится дефолтной (`is_default = True`)
- Автоматически создается дефолтный `column_mapping`
- `data_start_row` устанавливается в `1`

#### `get_user_sheets(user_id)`

Получает все Google-таблицы пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram

**Возвращает:**
- `List[Dict]`: Список словарей с информацией о таблицах

#### `get_user_sheet_by_id(user_id, sheet_doc_id)`

Получает конкретную таблицу по ID документа.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `sheet_doc_id` (str): ID документа таблицы

**Возвращает:**
- `Dict`: Словарь с информацией о таблице или `None`

#### `update_user_sheet_mapping(user_id, sheet_doc_id, new_mapping, new_start_row)`

Обновляет маппинг колонок и начальную строку для таблицы.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `sheet_doc_id` (str): ID документа таблицы
- `new_mapping` (Dict[str, str]): Новый маппинг колонок
- `new_start_row` (int): Новый номер начальной строки

**Возвращает:**
- `bool`: `True` при успехе, `False` при ошибке

#### `delete_user_sheet(user_id, sheet_doc_id)`

Удаляет таблицу пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `sheet_doc_id` (str): ID документа таблицы

**Возвращает:**
- `bool`: `True` при успехе, `False` при ошибке

**Особенности:**
- Если удаляемая таблица была дефолтной, автоматически назначается другая таблица (самая старая)

#### `set_default_sheet(user_id, sheet_doc_id)`

Устанавливает указанную таблицу как дефолтную.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `sheet_doc_id` (str): ID документа таблицы

**Возвращает:**
- `bool`: `True` при успехе, `False` при ошибке

**Особенности:**
- Использует транзакции для обеспечения атомарности операции
- Все остальные таблицы пользователя становятся не-дефолтными

#### `get_default_sheet(user_id)`

Получает дефолтную таблицу пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram

**Возвращает:**
- `Dict`: Словарь с информацией о дефолтной таблице или `None`

## Пример использования

```python
import asyncio
from services.google_sheets_manager import get_google_sheets_manager

async def main():
    manager = get_google_sheets_manager()
    user_id = 123456789
    
    # Добавить новую таблицу
    sheet_id = await manager.add_user_sheet(
        user_id=user_id,
        sheet_url="https://docs.google.com/spreadsheets/d/1ABC123/edit",
        sheet_id="1ABC123",
        friendly_name="Мои чеки"
    )
    
    # Получить все таблицы пользователя
    sheets = await manager.get_user_sheets(user_id)
    
    # Обновить маппинг колонок
    new_mapping = {
        "check_date": "A",
        "product_name": "B",
        "quantity": "C",
        "price_per_item": "D", 
        "total_price": "E",
        "store_name": "F"  # Добавить новую колонку
    }
    
    await manager.update_user_sheet_mapping(
        user_id=user_id,
        sheet_doc_id=sheet_id,
        new_mapping=new_mapping,
        new_start_row=3
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Интеграция с существующим проектом

Модуль автоматически использует глобальный экземпляр Firestore из `main.py`. Для интеграции в существующие обработчики:

```python
from services.google_sheets_manager import get_google_sheets_manager

# В обработчике команд или сообщений
async def handle_sheet_command(update, context):
    manager = get_google_sheets_manager()
    user_id = update.effective_user.id
    
    # Получить таблицы пользователя
    sheets = await manager.get_user_sheets(user_id)
    
    # Показать пользователю список таблиц
    if sheets:
        message = "Ваши Google-таблицы:\n"
        for sheet in sheets:
            status = " (по умолчанию)" if sheet['is_default'] else ""
            message += f"• {sheet['friendly_name']}{status}\n"
    else:
        message = "У вас пока нет настроенных Google-таблиц."
    
    await update.message.reply_text(message)
```

## Обработка ошибок

Все методы включают обработку ошибок и логирование:
- Сообщения об ошибках выводятся в консоль
- Методы возвращают `False` или `None` при ошибках
- Проверяется доступность Firestore перед выполнением операций

## Требования

- `google-cloud-firestore`
- Асинхронная среда выполнения (asyncio)
- Инициализированный клиент Firestore
