# Система управления таблицами AI Bot

## Обзор

Новая централизованная система управления таблицами позволяет унифицировать отображение всех таблиц в боте с поддержкой:
- Адаптивного дизайна для разных устройств (мобильные/планшеты/десктопы)
- Пользовательских настроек
- Легкого расширения новыми типами таблиц

## Архитектура

### Основные компоненты

1. **TableConfigManager** (`config/table_config.py`) - управление конфигурациями таблиц
2. **TableManager** (`utils/table_manager.py`) - центральный менеджер для форматирования
3. **TableSettingsHandler** (`handlers/table_settings_handler.py`) - обработчик пользовательских настроек

### Типы таблиц

- `INGREDIENT_MATCHING` - сопоставление ингредиентов
- `GOOGLE_SHEETS_MATCHING` - сопоставление с Google Таблицами
- `RECEIPT_PREVIEW` - предпросмотр чека
- `NEXT_ITEMS` - следующие товары
- `GENERAL_PAGINATED` - общие таблицы с пагинацией

### Типы устройств

- `MOBILE` - мобильные устройства (компактные таблицы)
- `TABLET` - планшеты (средние таблицы)
- `DESKTOP` - десктопы (полные таблицы)

## Использование

### Базовое использование

```python
from utils.table_manager import TableManager
from config.table_config import TableType, DeviceType

# Создание менеджера
table_manager = TableManager(locale_manager)

# Форматирование таблицы сопоставления ингредиентов
table_text = table_manager.format_ingredient_matching_table(
    matching_result, 
    context=context
)

# Форматирование с пагинацией
table_text, keyboard = table_manager.format_table_with_pagination(
    data, 
    page=1, 
    table_type=TableType.GENERAL_PAGINATED, 
    context=context
)
```

### Пользовательские настройки

```python
# Получение настроек пользователя
user_settings = table_manager.get_user_table_settings(user_id)

# Обновление настроек
table_manager.update_user_table_settings(
    user_id, 
    TableType.INGREDIENT_MATCHING, 
    DeviceType.MOBILE, 
    custom_config
)

# Сброс к стандартным настройкам
table_manager.reset_user_table_settings(
    user_id, 
    TableType.INGREDIENT_MATCHING, 
    DeviceType.MOBILE
)
```

## Конфигурация таблиц

### Стандартные конфигурации

Система поставляется с предустановленными конфигурациями для всех типов таблиц и устройств:

#### Мобильные таблицы
- Максимальная длина названия: 12-20 символов
- Элементов на странице: 5-10
- Компактный режим: включен
- Эмодзи: включены

#### Десктопные таблицы
- Максимальная длина названия: 20-35 символов
- Элементов на странице: 15-20
- Компактный режим: выключен
- Эмодзи: включены

### Пользовательские настройки

Пользователи могут настраивать:
- Максимальную длину названий товаров
- Количество элементов на странице
- Компактный режим
- Отображение эмодзи
- Тип устройства

## Интеграция с существующим кодом

### Обновление обработчиков

Все существующие обработчики автоматически получают доступ к `TableManager` через базовый класс:

```python
class MyHandler(BaseCallbackHandler):
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        # table_manager доступен как self.table_manager
```

### Обновление форматтеров

Существующие форматтеры обновлены для использования новой системы:

```python
# IngredientFormatter теперь поддерживает TableManager
formatter = IngredientFormatter(table_manager)
table_text = formatter.format_matching_table(result, context=context)
```

## Расширение системы

### Добавление нового типа таблицы

1. Добавьте новый тип в `TableType` enum
2. Создайте конфигурации в `TableConfigManager._load_default_configs()`
3. Добавьте метод форматирования в `TableManager`

### Добавление нового типа устройства

1. Добавьте новый тип в `DeviceType` enum
2. Создайте конфигурации для всех типов таблиц
3. Обновите логику определения устройства в `TableManager.detect_device_type()`

## Примеры использования

### Таблица сопоставления ингредиентов

```python
# Мобильная версия
mobile_table = table_manager.format_ingredient_matching_table(
    matching_result, 
    context=mobile_context
)

# Десктопная версия
desktop_table = table_manager.format_ingredient_matching_table(
    matching_result, 
    context=desktop_context
)
```

### Таблица предпросмотра чека

```python
receipt_data = [
    {"name": "Молоко", "quantity": "1", "price": "85.50", "total": "85.50"},
    {"name": "Хлеб", "quantity": "2", "price": "45.00", "total": "90.00"}
]

table_text = table_manager.format_receipt_preview_table(
    receipt_data, 
    context=context
)
```

### Таблица с пагинацией

```python
large_data = [{"name": f"Товар {i}"} for i in range(1, 101)]

table_text, keyboard = table_manager.format_table_with_pagination(
    large_data,
    page=1,
    table_type=TableType.GENERAL_PAGINATED,
    context=context
)
```

## Настройки пользователя

### Меню настроек

Пользователи могут получить доступ к настройкам таблиц через:
- Главное меню → Настройки таблиц
- Выбор типа таблицы для настройки
- Изменение параметров отображения
- Сброс к стандартным настройкам

### Сохранение настроек

Настройки сохраняются в памяти и привязаны к пользователю:
- При первом запуске используются стандартные настройки
- Пользователь может изменить настройки через интерфейс
- Настройки применяются ко всем таблицам данного типа

## Тестирование

Для тестирования системы используйте:

```bash
python test_table_system.py
```

Тест проверяет:
- Создание и управление конфигурациями
- Форматирование таблиц для разных устройств
- Пользовательские настройки
- Пагинацию
- Все типы таблиц

## Совместимость

Система полностью совместима с существующим кодом:
- Все существующие вызовы продолжают работать
- Добавлена поддержка контекста для автоматического определения устройства
- Fallback на старую логику при отсутствии TableManager

## Производительность

- Конфигурации загружаются один раз при инициализации
- Пользовательские настройки кэшируются в памяти
- Минимальные накладные расходы на определение типа устройства
- Эффективное форматирование с предварительно настроенными шаблонами
