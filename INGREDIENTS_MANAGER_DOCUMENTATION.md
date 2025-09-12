# Ingredients Manager Documentation

## Обзор

Модуль `services/ingredients_manager.py` предоставляет функциональность для управления списками ингредиентов пользователей в Firestore. Он позволяет сохранять, получать и удалять персональные списки ингредиентов для каждого пользователя.

## Структура данных в Firestore

В коллекции `users` каждый документ пользователя (с ID равным `telegram_user_id`) содержит поле `ingredient_list` типа `array` (список строк).

### Пример структуры документа пользователя:
```json
{
  "user_id": "123456789",
  "language": "ru",
  "ingredient_list": ["Молоко", "Хлеб", "Яйца", "Масло"]
}
```

## API

### Класс IngredientsManager

#### Инициализация
```python
from services.ingredients_manager import get_ingredients_manager

# Получить глобальный экземпляр (рекомендуется)
manager = get_ingredients_manager()

# Или создать новый экземпляр с конкретным клиентом Firestore
manager = IngredientsManager(db_instance)
```

#### Методы

##### `get_user_ingredients(user_id: int) -> List[str]`
Получает список ингредиентов пользователя.

**Параметры:**
- `user_id` (int): Telegram ID пользователя

**Возвращает:**
- `List[str]`: Список ингредиентов. Возвращает пустой список `[]`, если поле не существует или пустое.

**Пример:**
```python
ingredients = await manager.get_user_ingredients(123456789)
print(ingredients)  # ['Молоко', 'Хлеб', 'Яйца']
```

##### `update_user_ingredients(user_id: int, ingredients_list: List[str]) -> bool`
Полностью перезаписывает список ингредиентов пользователя.

**Параметры:**
- `user_id` (int): Telegram ID пользователя
- `ingredients_list` (List[str]): Новый список ингредиентов

**Возвращает:**
- `bool`: `True` при успешном обновлении, `False` при ошибке

**Пример:**
```python
new_ingredients = ["Молоко", "Хлеб", "Яйца", "Масло"]
success = await manager.update_user_ingredients(123456789, new_ingredients)
if success:
    print("Список ингредиентов обновлен!")
```

##### `delete_user_ingredients(user_id: int) -> bool`
Удаляет поле `ingredient_list` из документа пользователя.

**Параметры:**
- `user_id` (int): Telegram ID пользователя

**Возвращает:**
- `bool`: `True` при успешном удалении, `False` при ошибке

**Пример:**
```python
success = await manager.delete_user_ingredients(123456789)
if success:
    print("Список ингредиентов удален!")
```

## Примеры использования

### Базовое использование
```python
import asyncio
from services.ingredients_manager import get_ingredients_manager

async def main():
    manager = get_ingredients_manager()
    user_id = 123456789
    
    # Получить текущий список
    ingredients = await manager.get_user_ingredients(user_id)
    print(f"Текущие ингредиенты: {ingredients}")
    
    # Обновить список
    new_ingredients = ["Молоко", "Хлеб", "Яйца"]
    success = await manager.update_user_ingredients(user_id, new_ingredients)
    
    if success:
        print("Список обновлен успешно!")
    
    # Удалить список
    success = await manager.delete_user_ingredients(user_id)
    if success:
        print("Список удален!")

asyncio.run(main())
```

### Интеграция с обработчиками Telegram
```python
from services.ingredients_manager import get_ingredients_manager

async def handle_ingredients_command(update, context):
    """Обработчик команды /ingredients"""
    manager = get_ingredients_manager()
    user_id = update.effective_user.id
    
    # Получить список ингредиентов пользователя
    ingredients = await manager.get_user_ingredients(user_id)
    
    if ingredients:
        message = "Ваш список ингредиентов:\n" + "\n".join(f"• {ingredient}" for ingredient in ingredients)
    else:
        message = "У вас пока нет сохраненных ингредиентов."
    
    await update.message.reply_text(message)

async def handle_save_ingredients(update, context):
    """Обработчик сохранения ингредиентов"""
    manager = get_ingredients_manager()
    user_id = update.effective_user.id
    
    # Получить текст сообщения как список ингредиентов
    text = update.message.text
    ingredients = [item.strip() for item in text.split(',') if item.strip()]
    
    # Сохранить список
    success = await manager.update_user_ingredients(user_id, ingredients)
    
    if success:
        await update.message.reply_text(f"Сохранено {len(ingredients)} ингредиентов!")
    else:
        await update.message.reply_text("Ошибка при сохранении списка.")
```

## Обработка ошибок

Модуль включает встроенную обработку ошибок:

- **Firestore недоступен**: Все методы возвращают безопасные значения по умолчанию
- **Неверные типы данных**: Автоматическое преобразование в строки и фильтрация пустых значений
- **Несуществующие пользователи**: `get_user_ingredients` возвращает пустой список
- **Ошибки сети**: Логируются в консоль, методы возвращают `False` или пустой список

## Тестирование

Для тестирования модуля запустите:
```bash
python test_ingredients_manager.py
```

Этот скрипт демонстрирует все основные функции модуля.

## Зависимости

- `google-cloud-firestore`: Для работы с Firestore
- `asyncio`: Для асинхронных операций
- `typing`: Для типизации

## Примечания

- Все операции асинхронные и должны вызываться с `await`
- Модуль автоматически подключается к глобальному экземпляру Firestore из `main.py`
- Пустые строки автоматически фильтруются из списков ингредиентов
- Все не-строковые элементы автоматически преобразуются в строки
