"""
Конфигурация таблиц для AI Bot
Централизованная система управления настройками таблиц
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class TableType(Enum):
    """Типы таблиц в системе"""
    INGREDIENT_MATCHING = "ingredient_matching"
    GOOGLE_SHEETS_MATCHING = "google_sheets_matching"
    RECEIPT_PREVIEW = "receipt_preview"
    GOOGLE_SHEETS_PREVIEW = "google_sheets_preview"
    NEXT_ITEMS = "next_items"
    GENERAL_PAGINATED = "general_paginated"


class DeviceType(Enum):
    """Типы устройств"""
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"


@dataclass
class ColumnConfig:
    """Конфигурация колонки таблицы"""
    key: str
    title: str
    width: int
    align: str = "left"  # left, right, center
    wrap_text: bool = True
    max_lines: int = 3
    emoji: Optional[str] = None


@dataclass
class TableStyle:
    """Стиль таблицы"""
    max_name_length: int = 15
    show_separators: bool = True
    use_emojis: bool = True
    compact_mode: bool = False
    show_row_numbers: bool = True
    header_style: str = "bold"  # bold, italic, normal


@dataclass
class TableConfig:
    """Конфигурация таблицы"""
    table_type: TableType
    device_type: DeviceType
    columns: List[ColumnConfig]
    style: TableStyle
    title: str
    description: Optional[str] = None
    max_items_per_page: int = 10
    show_pagination: bool = True
    custom_formatter: Optional[str] = None  # Имя кастомного форматтера


class TableConfigManager:
    """Менеджер конфигураций таблиц"""
    
    def __init__(self):
        self._configs: Dict[str, TableConfig] = {}
        self._user_customizations: Dict[int, Dict[str, TableConfig]] = {}  # user_id -> configs
        self._load_default_configs()
    
    def _load_default_configs(self):
        """Загружает стандартные конфигурации таблиц"""
        
        # Таблица сопоставления ингредиентов - мобильная версия
        self._configs["ingredient_matching_mobile"] = TableConfig(
            table_type=TableType.INGREDIENT_MATCHING,
            device_type=DeviceType.MOBILE,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("receipt_item", "formatters.table_headers.product", 12, "left", emoji="📦"),
                ColumnConfig("ingredient", "formatters.table_headers.ingredient", 12, "left", emoji="🏷️"),
                 ColumnConfig("status", "", 4, "center", emoji="📊")
            ],
            style=TableStyle(
                max_name_length=12,
                compact_mode=True,
                show_separators=True
            ),
            title="matching.matching_title",
            max_items_per_page=8
        )
        
        # Таблица сопоставления ингредиентов - десктопная версия
        self._configs["ingredient_matching_desktop"] = TableConfig(
            table_type=TableType.INGREDIENT_MATCHING,
            device_type=DeviceType.DESKTOP,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("receipt_item", "formatters.table_headers.product", 20, "left", emoji="📦"),
                ColumnConfig("ingredient", "formatters.table_headers.ingredient", 20, "left", emoji="🏷️"),
                 ColumnConfig("status", "", 6, "center", emoji="📊")
            ],
            style=TableStyle(
                max_name_length=20,
                compact_mode=False,
                show_separators=True
            ),
            title="matching.matching_title",
            max_items_per_page=15
        )
        
        # Таблица Google Sheets - мобильная версия
        self._configs["google_sheets_matching_mobile"] = TableConfig(
            table_type=TableType.GOOGLE_SHEETS_MATCHING,
            device_type=DeviceType.MOBILE,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("receipt_item", "formatters.table_headers.name", 25, "left"),
                ColumnConfig("google_sheets", "formatters.table_headers.ingredient", 20, "left"),
                ColumnConfig("status", "", 4, "center")
            ],
            style=TableStyle(
                max_name_length=30,
                compact_mode=True,
                show_separators=True
            ),
            title="sheets.callback.matching_table_title",
            max_items_per_page=8
        )
        
        # Таблица Google Sheets - десктопная версия
        self._configs["google_sheets_matching_desktop"] = TableConfig(
            table_type=TableType.GOOGLE_SHEETS_MATCHING,
            device_type=DeviceType.DESKTOP,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("receipt_item", "formatters.table_headers.name", 35, "left"),
                ColumnConfig("google_sheets", "formatters.table_headers.ingredient", 30, "left"),
                ColumnConfig("status", "", 6, "center")
            ],
            style=TableStyle(
                max_name_length=40,
                compact_mode=False,
                show_separators=True
            ),
            title="sheets.callback.matching_table_title",
            max_items_per_page=15
        )
        
        # Таблица предпросмотра чека - мобильная версия
        self._configs["receipt_preview_mobile"] = TableConfig(
            table_type=TableType.RECEIPT_PREVIEW,
            device_type=DeviceType.MOBILE,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("item", "Товар", 18, "left", emoji="🛒"),
                ColumnConfig("quantity", "Кол-во", 6, "right", emoji="📊"),
                ColumnConfig("price", "Цена", 8, "right", emoji="💰")
            ],
            style=TableStyle(
                max_name_length=18,
                compact_mode=True
            ),
            title="Предпросмотр чека",
            max_items_per_page=10
        )
        
        # Таблица предпросмотра чека - десктопная версия
        self._configs["receipt_preview_desktop"] = TableConfig(
            table_type=TableType.RECEIPT_PREVIEW,
            device_type=DeviceType.DESKTOP,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("item", "Товар", 30, "left", emoji="🛒"),
                ColumnConfig("quantity", "Количество", 10, "right", emoji="📊"),
                ColumnConfig("price", "Цена за единицу", 12, "right", emoji="💰"),
                ColumnConfig("total", "Итого", 10, "right", emoji="💵")
            ],
            style=TableStyle(
                max_name_length=30,
                compact_mode=False
            ),
            title="Предпросмотр чека",
            max_items_per_page=20
        )
        
        # Таблица предпросмотра Google Sheets - мобильная версия (динамическая)
        self._configs["google_sheets_preview_mobile"] = TableConfig(
            table_type=TableType.GOOGLE_SHEETS_PREVIEW,
            device_type=DeviceType.MOBILE,
            columns=[],  # Будет заполняться динамически на основе column_mapping пользователя
            style=TableStyle(
                max_name_length=15,
                compact_mode=True,
                show_separators=False
            ),
            title="Предпросмотр Google Таблицы",
            max_items_per_page=10
        )
        
        # Таблица предпросмотра Google Sheets - десктопная версия (динамическая)
        self._configs["google_sheets_preview_desktop"] = TableConfig(
            table_type=TableType.GOOGLE_SHEETS_PREVIEW,
            device_type=DeviceType.DESKTOP,
            columns=[],  # Будет заполняться динамически на основе column_mapping пользователя
            style=TableStyle(
                max_name_length=25,
                compact_mode=False,
                show_separators=False
            ),
            title="Предпросмотр Google Таблицы",
            max_items_per_page=20
        )
        
        # Таблица "Следующие" - мобильная версия
        self._configs["next_items_mobile"] = TableConfig(
            table_type=TableType.NEXT_ITEMS,
            device_type=DeviceType.MOBILE,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("item", "Следующий товар", 20, "left", emoji="⏭️"),
                ColumnConfig("status", "", 6, "center", emoji="📋")
            ],
            style=TableStyle(
                max_name_length=20,
                compact_mode=True
            ),
            title="Следующие товары",
            max_items_per_page=8
        )
        
        # Таблица "Следующие" - десктопная версия
        self._configs["next_items_desktop"] = TableConfig(
            table_type=TableType.NEXT_ITEMS,
            device_type=DeviceType.DESKTOP,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("item", "Следующий товар", 35, "left", emoji="⏭️"),
                ColumnConfig("status", "", 10, "center", emoji="📋"),
                ColumnConfig("priority", "Приоритет", 8, "center", emoji="⭐")
            ],
            style=TableStyle(
                max_name_length=35,
                compact_mode=False
            ),
            title="Следующие товары",
            max_items_per_page=15
        )
    
    def get_config(self, table_type: TableType, device_type: DeviceType, user_id: Optional[int] = None) -> TableConfig:
        """
        Получает конфигурацию таблицы
        
        Args:
            table_type: Тип таблицы
            device_type: Тип устройства
            user_id: ID пользователя (для пользовательских настроек)
            
        Returns:
            TableConfig: Конфигурация таблицы
        """
        config_key = f"{table_type.value}_{device_type.value}"
        
        # Проверяем пользовательские настройки
        if user_id and user_id in self._user_customizations:
            user_configs = self._user_customizations[user_id]
            if config_key in user_configs:
                return user_configs[config_key]
        
        # Возвращаем стандартную конфигурацию
        if config_key in self._configs:
            return self._configs[config_key]
        
        # Fallback на десктопную версию
        fallback_key = f"{table_type.value}_desktop"
        if fallback_key in self._configs:
            return self._configs[fallback_key]
        
        # Если ничего не найдено, создаем базовую конфигурацию
        return self._create_fallback_config(table_type, device_type)
    
    def set_user_config(self, user_id: int, table_type: TableType, device_type: DeviceType, config: TableConfig):
        """
        Устанавливает пользовательскую конфигурацию таблицы
        
        Args:
            user_id: ID пользователя
            table_type: Тип таблицы
            device_type: Тип устройства
            config: Конфигурация таблицы
        """
        if user_id not in self._user_customizations:
            self._user_customizations[user_id] = {}
        
        config_key = f"{table_type.value}_{device_type.value}"
        self._user_customizations[user_id][config_key] = config
    
    def reset_user_config(self, user_id: int, table_type: TableType, device_type: DeviceType):
        """
        Сбрасывает пользовательскую конфигурацию к стандартной
        
        Args:
            user_id: ID пользователя
            table_type: Тип таблицы
            device_type: Тип устройства
        """
        if user_id in self._user_customizations:
            config_key = f"{table_type.value}_{device_type.value}"
            self._user_customizations[user_id].pop(config_key, None)
    
    def get_available_configs(self, user_id: Optional[int] = None) -> Dict[str, TableConfig]:
        """
        Получает все доступные конфигурации
        
        Args:
            user_id: ID пользователя (для пользовательских настроек)
            
        Returns:
            Dict[str, TableConfig]: Словарь конфигураций
        """
        if user_id and user_id in self._user_customizations:
            # Объединяем стандартные и пользовательские конфигурации
            result = self._configs.copy()
            result.update(self._user_customizations[user_id])
            return result
        
        return self._configs.copy()
    
    def _create_fallback_config(self, table_type: TableType, device_type: DeviceType) -> TableConfig:
        """Создает базовую конфигурацию если стандартная не найдена"""
        return TableConfig(
            table_type=table_type,
            device_type=device_type,
            columns=[
                ColumnConfig("number", "№", 2, "right"),
                ColumnConfig("item", "Элемент", 20, "left"),
                ColumnConfig("status", "", 6, "center")
            ],
            style=TableStyle(max_name_length=20),
            title=f"Таблица {table_type.value}",
            max_items_per_page=10
        )


# Глобальный экземпляр менеджера конфигураций
table_config_manager = TableConfigManager()
