# Display Mode Setup Guide

## Обзор

Добавлена возможность переключения между десктопной и мобильной версиями отображения таблиц в AI Bot. Пользователи могут выбирать предпочитаемый режим отображения, который сохраняется в Firestore.

## Новые функции

### 1. `set_user_display_mode(user_id: int, mode: str) -> bool`

Устанавливает режим отображения таблиц для пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `mode` (str): Режим отображения ("desktop" или "mobile")

**Возвращает:**
- `bool`: True при успешном сохранении, False при ошибке

**Пример использования:**
```python
from services.user_service import get_user_service

user_service = get_user_service(db)
success = await user_service.set_user_display_mode(123456789, "desktop")
```

### 2. `get_user_display_mode(user_id: int) -> str`

Получает текущий режим отображения таблиц пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram

**Возвращает:**
- `str`: Режим отображения ("desktop" или "mobile")
- По умолчанию возвращает "mobile", если настройка не установлена

**Пример использования:**
```python
from services.user_service import get_user_service

user_service = get_user_service(db)
mode = await user_service.get_user_display_mode(123456789)
print(f"Current display mode: {mode}")
```

## Структура данных в Firestore

### Коллекция `users`

Каждый документ пользователя теперь содержит:

```json
{
  "user_id": "123456789",
  "role": "user",
  "display_mode": "desktop",
  "display_mode_updated_at": "2024-01-15T10:30:00Z",
  "ingredient_list": [...],
  "language": "ru",
  ...
}
```

**Новые поля:**
- `display_mode` (string): Режим отображения ("desktop" или "mobile")
- `display_mode_updated_at` (timestamp): Время последнего обновления настройки

## Валидация

- Функция `set_user_display_mode` принимает только значения "desktop" и "mobile"
- При передаче недопустимого значения функция возвращает `False`
- Функция `get_user_display_mode` всегда возвращает валидное значение ("mobile" по умолчанию)

## Тестирование

Для тестирования новых функций используйте:

```bash
python test_display_mode.py
```

Тест проверяет:
- Установку режима "desktop"
- Установку режима "mobile"
- Получение текущего режима
- Обработку недопустимых значений
- Поведение для несуществующих пользователей

## Интеграция

Новые функции интегрированы в существующий `UserService` и используют тот же экземпляр Firestore. Они совместимы с существующей архитектурой и не нарушают работу других функций.

## Миграция

Существующие пользователи автоматически получат режим "mobile" при первом обращении к функции `get_user_display_mode`. Никаких дополнительных действий для миграции не требуется.

## Логирование

Все операции логируются в консоль:
- ✅ Успешные операции
- ❌ Ошибки
- ⚠️ Предупреждения (например, использование значения по умолчанию)
