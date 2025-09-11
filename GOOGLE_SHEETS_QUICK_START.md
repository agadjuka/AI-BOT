# Google Sheets Manager - Быстрый старт

## Установка

Модуль уже готов к использованию. Просто импортируйте его в вашем коде:

```python
from services.google_sheets_manager import get_google_sheets_manager
```

## Базовое использование

```python
import asyncio
from services.google_sheets_manager import get_google_sheets_manager

async def main():
    # Инициализация
    manager = get_google_sheets_manager()
    user_id = 123456789  # ID пользователя Telegram
    
    # 1. Добавить таблицу
    sheet_id = await manager.add_user_sheet(
        user_id=user_id,
        sheet_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
        sheet_id="YOUR_SHEET_ID",
        friendly_name="Мои чеки"
    )
    
    # 2. Получить все таблицы
    sheets = await manager.get_user_sheets(user_id)
    
    # 3. Настроить колонки
    custom_mapping = {
        "check_date": "A",
        "product_name": "B", 
        "quantity": "C",
        "price_per_item": "D",
        "total_price": "E"
    }
    
    await manager.update_user_sheet_mapping(
        user_id=user_id,
        sheet_doc_id=sheet_id,
        new_mapping=custom_mapping,
        new_start_row=2
    )

# Запуск
asyncio.run(main())
```

## Основные функции

| Функция | Описание |
|---------|----------|
| `add_user_sheet()` | Добавить новую таблицу |
| `get_user_sheets()` | Получить все таблицы пользователя |
| `get_user_sheet_by_id()` | Получить конкретную таблицу |
| `update_user_sheet_mapping()` | Настроить маппинг колонок |
| `delete_user_sheet()` | Удалить таблицу |
| `set_default_sheet()` | Установить таблицу по умолчанию |
| `get_default_sheet()` | Получить таблицу по умолчанию |

## Дефолтный маппинг колонок

При создании новой таблицы автоматически создается следующий маппинг:

- `check_date` → колонка A
- `product_name` → колонка B  
- `quantity` → колонка C
- `price_per_item` → колонка D
- `total_price` → колонка E

## Полная документация

См. [GOOGLE_SHEETS_MANAGER.md](GOOGLE_SHEETS_MANAGER.md) для подробной документации.

## Примеры

См. [examples/google_sheets_manager_example.py](examples/google_sheets_manager_example.py) для полного примера использования.
