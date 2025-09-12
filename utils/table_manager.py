"""
Центральный менеджер таблиц для AI Bot
Унифицированная система создания и форматирования всех типов таблиц
"""
from typing import List, Dict, Any, Optional, Tuple, Union
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config.table_config import (
    TableConfigManager, TableType, DeviceType, 
    table_config_manager, TableConfig, ColumnConfig
)
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus


class TableManager:
    """Центральный менеджер для всех таблиц в системе"""
    
    def __init__(self, locale_manager=None):
        self.config_manager = table_config_manager
        self.locale_manager = locale_manager
    
    def detect_device_type(self, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> DeviceType:
        """
        Определяет тип устройства пользователя
        
        Args:
            context: Контекст Telegram
            
        Returns:
            DeviceType: Тип устройства
        """
        # Простая эвристика - можно расширить
        if context and hasattr(context, 'user_data'):
            # Проверяем сохраненные настройки пользователя
            device_type = context.user_data.get('device_type')
            if device_type:
                try:
                    return DeviceType(device_type)
                except ValueError:
                    pass
        
        # По умолчанию считаем мобильным устройством
        return DeviceType.MOBILE
    
    def format_ingredient_matching_table(self, 
                                       result: IngredientMatchingResult, 
                                       context: Optional[ContextTypes.DEFAULT_TYPE] = None,
                                       changed_indices: set = None) -> str:
        """
        Форматирует таблицу сопоставления ингредиентов
        
        Args:
            result: Результат сопоставления ингредиентов
            context: Контекст Telegram
            changed_indices: Индексы измененных элементов
            
        Returns:
            str: Отформатированная таблица
        """
        device_type = self.detect_device_type(context)
        config = self.config_manager.get_config(
            TableType.INGREDIENT_MATCHING, 
            device_type, 
            context.user_data.get('user_id') if context else None
        )
        
        if not result.matches:
            return self._get_no_data_message("ingredient_matching", context)
        
        # Создаем заголовок с статистикой
        table_lines = []
        table_lines.append(f"**{config.title}:**\n")
        
        # Добавляем статистику
        summary = self._format_summary(result, context)
        table_lines.append(summary)
        
        # Создаем таблицу
        table_lines.append("```")
        table_lines.append(self._create_table_header(config))
        table_lines.append(self._create_table_separator(config))
        
        # Добавляем строки таблицы
        for i, match in enumerate(result.matches, 1):
            is_changed = changed_indices is not None and (i-1) in changed_indices
            table_lines.append(self._create_ingredient_matching_row(i, match, config, is_changed))
        
        table_lines.append("```")
        
        return "\n".join(table_lines)
    
    def format_google_sheets_matching_table(self, 
                                          result: IngredientMatchingResult, 
                                          context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """
        Форматирует таблицу сопоставления с Google Sheets
        
        Args:
            result: Результат сопоставления ингредиентов
            context: Контекст Telegram
            
        Returns:
            str: Отформатированная таблица
        """
        device_type = self.detect_device_type(context)
        config = self.config_manager.get_config(
            TableType.GOOGLE_SHEETS_MATCHING, 
            device_type, 
            context.user_data.get('user_id') if context else None
        )
        
        if not result.matches:
            return self._get_no_data_message("google_sheets_matching", context)
        
        # Создаем заголовок
        table_lines = []
        table_lines.append(f"**{config.title}:**\n")
        
        # Создаем таблицу
        table_lines.append("```")
        table_lines.append(self._create_table_header(config))
        table_lines.append(self._create_table_separator(config))
        
        # Добавляем строки таблицы
        for i, match in enumerate(result.matches, 1):
            table_lines.append(self._create_google_sheets_matching_row(i, match, config))
        
        table_lines.append("```")
        
        return "\n".join(table_lines)
    
    def format_receipt_preview_table(self, 
                                   receipt_data: List[Dict[str, Any]], 
                                   context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """
        Форматирует таблицу предпросмотра чека
        
        Args:
            receipt_data: Данные чека
            context: Контекст Telegram
            
        Returns:
            str: Отформатированная таблица
        """
        device_type = self.detect_device_type(context)
        config = self.config_manager.get_config(
            TableType.RECEIPT_PREVIEW, 
            device_type, 
            context.user_data.get('user_id') if context else None
        )
        
        if not receipt_data:
            return self._get_no_data_message("receipt_preview", context)
        
        # Создаем заголовок
        table_lines = []
        table_lines.append(f"**{config.title}:**\n")
        
        # Создаем таблицу
        table_lines.append("```")
        table_lines.append(self._create_table_header(config))
        table_lines.append(self._create_table_separator(config))
        
        # Добавляем строки таблицы
        for i, item in enumerate(receipt_data, 1):
            table_lines.append(self._create_receipt_preview_row(i, item, config))
        
        table_lines.append("```")
        
        return "\n".join(table_lines)
    
    def format_next_items_table(self, 
                              next_items: List[Dict[str, Any]], 
                              context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """
        Форматирует таблицу "Следующие товары"
        
        Args:
            next_items: Список следующих товаров
            context: Контекст Telegram
            
        Returns:
            str: Отформатированная таблица
        """
        device_type = self.detect_device_type(context)
        config = self.config_manager.get_config(
            TableType.NEXT_ITEMS, 
            device_type, 
            context.user_data.get('user_id') if context else None
        )
        
        if not next_items:
            return self._get_no_data_message("next_items", context)
        
        # Создаем заголовок
        table_lines = []
        table_lines.append(f"**{config.title}:**\n")
        
        # Создаем таблицу
        table_lines.append("```")
        table_lines.append(self._create_table_header(config))
        table_lines.append(self._create_table_separator(config))
        
        # Добавляем строки таблицы
        for i, item in enumerate(next_items, 1):
            table_lines.append(self._create_next_items_row(i, item, config))
        
        table_lines.append("```")
        
        return "\n".join(table_lines)
    
    def format_table_with_pagination(self, 
                                   data: List[Dict[str, Any]], 
                                   page: int = 1,
                                   table_type: TableType = TableType.GENERAL_PAGINATED,
                                   context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Форматирует таблицу с пагинацией
        
        Args:
            data: Данные для отображения
            page: Номер страницы
            table_type: Тип таблицы
            context: Контекст Telegram
            
        Returns:
            Tuple[str, InlineKeyboardMarkup]: Текст таблицы и клавиатура навигации
        """
        device_type = self.detect_device_type(context)
        config = self.config_manager.get_config(
            table_type, 
            device_type, 
            context.user_data.get('user_id') if context else None
        )
        
        if not data:
            no_data_text = self._get_no_data_message(table_type.value, context)
            return no_data_text, InlineKeyboardMarkup([])
        
        total_items = len(data)
        total_pages = (total_items + config.max_items_per_page - 1) // config.max_items_per_page
        
        # Проверяем корректность номера страницы
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # Вычисляем индексы для текущей страницы
        start_idx = (page - 1) * config.max_items_per_page
        end_idx = min(start_idx + config.max_items_per_page, total_items)
        
        # Получаем данные для текущей страницы
        page_data = data[start_idx:end_idx]
        
        # Форматируем таблицу
        table_text = self._format_paginated_table(page_data, page, start_idx, config, context)
        
        # Создаем клавиатуру навигации
        navigation_keyboard = self._create_navigation_keyboard(page, total_pages, context)
        
        return table_text, navigation_keyboard
    
    def _create_table_header(self, config: TableConfig) -> str:
        """Создает заголовок таблицы"""
        header_parts = []
        for column in config.columns:
            if column.emoji and config.style.use_emojis:
                title = f"{column.emoji} {column.title}"
            else:
                title = column.title
            
            # Выравнивание
            if column.align == "right":
                header_parts.append(f"{title:>{column.width}}")
            elif column.align == "center":
                header_parts.append(f"{title:^{column.width}}")
            else:  # left
                header_parts.append(f"{title:<{column.width}}")
        
        return " | ".join(header_parts)
    
    def _create_table_separator(self, config: TableConfig) -> str:
        """Создает разделитель таблицы"""
        if not config.style.show_separators:
            return ""
        
        total_width = sum(column.width for column in config.columns) + (len(config.columns) - 1) * 3
        return "-" * total_width
    
    def _create_ingredient_matching_row(self, row_number: int, match: IngredientMatch, config: TableConfig, is_changed: bool = False) -> str:
        """Создает строку таблицы сопоставления ингредиентов"""
        # Получаем данные для колонок
        receipt_name = match.receipt_item_name
        ingredient_name = match.matched_ingredient_name or "—"
        
        # Статус
        if is_changed:
            status_emoji = "✏️"
        else:
            status_emoji = self._get_status_emoji(match.match_status)
        
        # Создаем строку
        row_parts = []
        for column in config.columns:
            if column.key == "number":
                value = str(row_number)
            elif column.key == "receipt_item":
                value = self._wrap_text(receipt_name, column.width, config.style.max_name_length)
            elif column.key == "ingredient":
                value = self._wrap_text(ingredient_name, column.width, config.style.max_name_length)
            elif column.key == "status":
                value = status_emoji
            else:
                value = ""
            
            # Выравнивание
            if column.align == "right":
                row_parts.append(f"{value:>{column.width}}")
            elif column.align == "center":
                row_parts.append(f"{value:^{column.width}}")
            else:  # left
                row_parts.append(f"{value:<{column.width}}")
        
        return " | ".join(row_parts)
    
    def _create_google_sheets_matching_row(self, row_number: int, match: IngredientMatch, config: TableConfig) -> str:
        """Создает строку таблицы сопоставления с Google Sheets"""
        # Аналогично ingredient_matching_row, но с другими колонками
        receipt_name = match.receipt_item_name
        ingredient_name = match.matched_ingredient_name or "—"
        status_emoji = self._get_status_emoji(match.match_status)
        
        row_parts = []
        for column in config.columns:
            if column.key == "number":
                value = str(row_number)
            elif column.key == "receipt_item":
                value = self._wrap_text(receipt_name, column.width, config.style.max_name_length)
            elif column.key == "google_sheets":
                value = self._wrap_text(ingredient_name, column.width, config.style.max_name_length)
            elif column.key == "status":
                value = status_emoji
            else:
                value = ""
            
            # Выравнивание
            if column.align == "right":
                row_parts.append(f"{value:>{column.width}}")
            elif column.align == "center":
                row_parts.append(f"{value:^{column.width}}")
            else:  # left
                row_parts.append(f"{value:<{column.width}}")
        
        return " | ".join(row_parts)
    
    def _create_receipt_preview_row(self, row_number: int, item: Dict[str, Any], config: TableConfig) -> str:
        """Создает строку таблицы предпросмотра чека"""
        row_parts = []
        for column in config.columns:
            if column.key == "number":
                value = str(row_number)
            elif column.key == "item":
                value = self._wrap_text(str(item.get('name', '')), column.width, config.style.max_name_length)
            elif column.key == "quantity":
                value = str(item.get('quantity', ''))
            elif column.key == "price":
                value = str(item.get('price', ''))
            elif column.key == "total":
                value = str(item.get('total', ''))
            else:
                value = ""
            
            # Выравнивание
            if column.align == "right":
                row_parts.append(f"{value:>{column.width}}")
            elif column.align == "center":
                row_parts.append(f"{value:^{column.width}}")
            else:  # left
                row_parts.append(f"{value:<{column.width}}")
        
        return " | ".join(row_parts)
    
    def _create_next_items_row(self, row_number: int, item: Dict[str, Any], config: TableConfig) -> str:
        """Создает строку таблицы следующих товаров"""
        row_parts = []
        for column in config.columns:
            if column.key == "number":
                value = str(row_number)
            elif column.key == "item":
                value = self._wrap_text(str(item.get('name', '')), column.width, config.style.max_name_length)
            elif column.key == "status":
                value = str(item.get('status', ''))
            elif column.key == "priority":
                value = str(item.get('priority', ''))
            else:
                value = ""
            
            # Выравнивание
            if column.align == "right":
                row_parts.append(f"{value:>{column.width}}")
            elif column.align == "center":
                row_parts.append(f"{value:^{column.width}}")
            else:  # left
                row_parts.append(f"{value:<{column.width}}")
        
        return " | ".join(row_parts)
    
    def _wrap_text(self, text: str, max_width: int, max_name_length: int) -> str:
        """Переносит текст в соответствии с ограничениями"""
        if not text:
            return ""
        
        # Ограничиваем длину
        if len(text) > max_name_length:
            text = text[:max_name_length-3] + "..."
        
        # Если текст помещается в колонку, возвращаем как есть
        if len(text) <= max_width:
            return text
        
        # Иначе обрезаем
        return text[:max_width-3] + "..."
    
    def _get_status_emoji(self, status: MatchStatus) -> str:
        """Получает эмодзи для статуса сопоставления"""
        if status == MatchStatus.EXACT_MATCH:
            return "🟢"
        elif status == MatchStatus.PARTIAL_MATCH:
            return "🟡"
        else:
            return "🔴"
    
    def _format_summary(self, result: IngredientMatchingResult, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """Форматирует сводку результатов"""
        summary = f"📊 **Статистика:** Всего: {result.total_items} | "
        summary += f"🟢 Точных: {result.exact_matches} | "
        summary += f"🟡 Частичных: {result.partial_matches} | "
        summary += f"🔴 Не найдено: {result.no_matches}\n"
        return summary
    
    def _get_no_data_message(self, table_type: str, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """Получает сообщение об отсутствии данных"""
        if self.locale_manager and context:
            return self.locale_manager.get_text(f"tables.no_data.{table_type}", context)
        
        # Fallback сообщения
        messages = {
            "ingredient_matching": "Нет ингредиентов для сопоставления.",
            "google_sheets_matching": "Нет ингредиентов для сопоставления с Google Таблицами.",
            "receipt_preview": "Нет данных для предпросмотра.",
            "next_items": "Нет следующих товаров."
        }
        return messages.get(table_type, "Нет данных для отображения.")
    
    def _format_paginated_table(self, data: List[Dict[str, Any]], page: int, start_idx: int, config: TableConfig, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """Форматирует таблицу с пагинацией"""
        if not data:
            return self._get_no_data_message("general", context)
        
        lines = []
        
        # Заголовок страницы
        if self.locale_manager and context:
            page_text = self.locale_manager.get_text("common.page", context, page=page)
        else:
            page_text = f"Страница {page}"
        lines.append(page_text)
        
        # Данные таблицы
        for i, item in enumerate(data, start_idx + 1):
            lines.append(f"{i}. {str(item)}")
        
        return "\n".join(lines)
    
    def _create_navigation_keyboard(self, current_page: int, total_pages: int, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> InlineKeyboardMarkup:
        """Создает клавиатуру навигации для пагинации"""
        if total_pages <= 1:
            return InlineKeyboardMarkup([])
        
        keyboard = []
        nav_buttons = []
        
        # Получаем локализованные эмодзи
        if self.locale_manager and context:
            first_emoji = self.locale_manager.get_text("common.navigation_buttons.first_page", context)
            prev_emoji = self.locale_manager.get_text("common.navigation_buttons.previous_page", context)
            next_emoji = self.locale_manager.get_text("common.navigation_buttons.next_page", context)
            last_emoji = self.locale_manager.get_text("common.navigation_buttons.last_page", context)
        else:
            first_emoji = "⏮️"
            prev_emoji = "◀️"
            next_emoji = "▶️"
            last_emoji = "⏭️"
        
        # Кнопка "Первая страница"
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton(first_emoji, callback_data="page_1"))
        
        # Кнопка "Предыдущая страница"
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton(prev_emoji, callback_data=f"page_{current_page-1}"))
        
        # Кнопка "Следующая страница"
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton(next_emoji, callback_data=f"page_{current_page+1}"))
        
        # Кнопка "Последняя страница"
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton(last_emoji, callback_data=f"page_{total_pages}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_user_table_settings(self, user_id: int) -> Dict[str, Any]:
        """Получает настройки таблиц пользователя"""
        return self.config_manager.get_available_configs(user_id)
    
    def update_user_table_settings(self, user_id: int, table_type: TableType, device_type: DeviceType, config: TableConfig):
        """Обновляет настройки таблицы пользователя"""
        self.config_manager.set_user_config(user_id, table_type, device_type, config)
    
    def reset_user_table_settings(self, user_id: int, table_type: TableType, device_type: DeviceType):
        """Сбрасывает настройки таблицы пользователя к стандартным"""
        self.config_manager.reset_user_config(user_id, table_type, device_type)
