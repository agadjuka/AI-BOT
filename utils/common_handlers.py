"""
Общие методы для обработчиков Telegram бота
Содержит переиспользуемую логику для устранения дублирования кода
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from config.locales.locale_manager import get_global_locale_manager
from utils.table_manager import TableManager


class CommonHandlers:
    """Класс с общими методами для всех обработчиков"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        self.config = config
        self.analysis_service = analysis_service
        self.locale_manager = get_global_locale_manager()
        self.table_manager = TableManager(self.locale_manager)
    
    async def send_long_message_with_keyboard(self, message, text: str, reply_markup) -> None:
        """
        Отправка длинного сообщения с клавиатурой
        
        Args:
            message: Объект сообщения для ответа
            text: Текст сообщения
            reply_markup: Клавиатура для сообщения
        """
        if len(text) <= self.config.MAX_MESSAGE_LENGTH:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Разбиваем на части
        parts = [text[i:i + self.config.MAX_MESSAGE_LENGTH] for i in range(0, len(text), self.config.MAX_MESSAGE_LENGTH)]
        
        # Отправляем все части кроме последней
        for part in parts[:-1]:
            await message.reply_text(part, parse_mode='Markdown')
            await asyncio.sleep(self.config.MESSAGE_DELAY)
        
        # Отправляем последнюю часть с клавиатурой
        await message.reply_text(parts[-1], reply_markup=reply_markup, parse_mode='Markdown')
    
    async def ensure_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE, 
                                      ingredient_type: str = "poster") -> bool:
        """
        Обеспечивает загрузку ингредиентов, загружает их при необходимости
        
        Args:
            context: Контекст бота
            ingredient_type: Тип ингредиентов ("poster" или "google_sheets")
            
        Returns:
            bool: True если ингредиенты загружены успешно, False в противном случае
        """
        if ingredient_type == "poster":
            return await self._ensure_poster_ingredients_loaded(context)
        elif ingredient_type == "google_sheets":
            return await self._ensure_google_sheets_ingredients_loaded(context)
        else:
            debug_message = self.locale_manager.get_text("common.unknown_ingredient_type", 
                                                       context, ingredient_type=ingredient_type)
            print(debug_message)
            return False
    
    async def _ensure_poster_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Обеспечивает загрузку ингредиентов постера"""
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not poster_ingredients:
            # Загружаем ингредиенты постера
            from poster_handler import get_all_poster_ingredients
            poster_ingredients = get_all_poster_ingredients()
            
            if not poster_ingredients:
                return False
            
            # Сохраняем ингредиенты в данные бота для будущего использования
            context.bot_data["poster_ingredients"] = poster_ingredients
            debug_message = self.locale_manager.get_text("common.loaded_poster_ingredients", 
                                                       context, count=len(poster_ingredients))
            print(debug_message)
        
        return True
    
    async def _ensure_google_sheets_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Обеспечивает загрузку ингредиентов Google Sheets"""
        google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        
        if not google_sheets_ingredients:
            # Загружаем ингредиенты Google Sheets
            from google_sheets_handler import get_google_sheets_ingredients
            google_sheets_ingredients = get_google_sheets_ingredients()
            
            if not google_sheets_ingredients:
                return False
            
            # Сохраняем ингредиенты в данные бота для будущего использования
            context.bot_data["google_sheets_ingredients"] = google_sheets_ingredients
            loaded_message = self.locale_manager.get_text("common.loaded_google_sheets_ingredients", 
                                                        context, count=len(google_sheets_ingredients))
            print(loaded_message)
            
            debug_message = self.locale_manager.get_text("common.debug_first_ingredients", 
                                                       context, ingredients=list(google_sheets_ingredients.keys())[:5])
            print(debug_message)
        
        return True
    
    def format_table_with_pagination(self, data: List[Dict[str, Any]], 
                                   page: int = 1, 
                                   items_per_page: int = 10,
                                   table_formatter: callable = None,
                                   context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Форматирует таблицу с пагинацией
        
        Args:
            data: Список данных для отображения
            page: Номер страницы (начиная с 1)
            items_per_page: Количество элементов на странице
            table_formatter: Функция для форматирования строки таблицы
            context: Контекст для определения языка
            
        Returns:
            Tuple[str, InlineKeyboardMarkup]: Текст таблицы и клавиатура навигации
        """
        # Используем TableManager если доступен
        if hasattr(self, 'table_manager') and self.table_manager:
            from config.table_config import TableType
            return self.table_manager.format_table_with_pagination(
                data, page, TableType.GENERAL_PAGINATED, context
            )
        
        # Fallback на старую логику
        if not data:
            no_data_text = self.locale_manager.get_text("common.no_data_to_display", context)
            return no_data_text, InlineKeyboardMarkup([])
        
        total_items = len(data)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        # Проверяем корректность номера страницы
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # Вычисляем индексы для текущей страницы
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        
        # Получаем данные для текущей страницы
        page_data = data[start_idx:end_idx]
        
        # Форматируем таблицу
        if table_formatter:
            table_text = table_formatter(page_data, page, start_idx)
        else:
            table_text = self._default_table_formatter(page_data, page, start_idx, context)
        
        # Создаем клавиатуру навигации
        navigation_keyboard = self.create_navigation_buttons(page, total_pages, context=context)
        
        return table_text, navigation_keyboard
    
    def _default_table_formatter(self, data: List[Dict[str, Any]], 
                                page: int, start_idx: int, 
                                context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """Форматирование таблицы по умолчанию"""
        if not data:
            return self.locale_manager.get_text("common.no_data_to_display", context)
        
        # Простое форматирование - можно переопределить в наследниках
        page_text = self.locale_manager.get_text("common.page", context, page=page)
        lines = [page_text]
        for i, item in enumerate(data, start_idx + 1):
            lines.append(f"{i}. {str(item)}")
        
        return "\n".join(lines)
    
    def create_navigation_buttons(self, current_page: int, total_pages: int, 
                                base_callback: str = "page", 
                                context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> InlineKeyboardMarkup:
        """
        Создает стандартные кнопки навигации для пагинации
        
        Args:
            current_page: Текущая страница
            total_pages: Общее количество страниц
            base_callback: Базовое имя callback для кнопок
            context: Контекст для определения языка
            
        Returns:
            InlineKeyboardMarkup: Клавиатура с кнопками навигации
        """
        if total_pages <= 1:
            return InlineKeyboardMarkup([])
        
        keyboard = []
        
        # Кнопки навигации
        nav_buttons = []
        
        # Получаем локализованные эмодзи для кнопок навигации
        first_page_emoji = self.locale_manager.get_text("common.navigation_buttons.first_page", context)
        previous_page_emoji = self.locale_manager.get_text("common.navigation_buttons.previous_page", context)
        next_page_emoji = self.locale_manager.get_text("common.navigation_buttons.next_page", context)
        last_page_emoji = self.locale_manager.get_text("common.navigation_buttons.last_page", context)
        
        # Кнопка "Первая страница"
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton(first_page_emoji, callback_data=f"{base_callback}_1"))
        
        # Кнопка "Предыдущая страница"
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton(previous_page_emoji, callback_data=f"{base_callback}_{current_page - 1}"))
        
        # Информация о текущей странице
        nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
        
        # Кнопка "Следующая страница"
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton(next_page_emoji, callback_data=f"{base_callback}_{current_page + 1}"))
        
        # Кнопка "Последняя страница"
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton(last_page_emoji, callback_data=f"{base_callback}_{total_pages}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_standard_buttons(self, button_configs: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """
        Создает стандартные кнопки на основе конфигурации
        
        Args:
            button_configs: Список конфигураций кнопок
                          [{"text": "Текст кнопки", "callback": "callback_data", "row": 0}]
        
        Returns:
            InlineKeyboardMarkup: Клавиатура с кнопками
        """
        keyboard = []
        current_row = 0
        
        for config in button_configs:
            text = config.get("text", "")
            callback = config.get("callback", "noop")
            row = config.get("row", 0)
            
            # Создаем новую строку если нужно
            while len(keyboard) <= row:
                keyboard.append([])
            
            # Добавляем кнопку в соответствующую строку
            keyboard[row].append(InlineKeyboardButton(text, callback_data=callback))
        
        return InlineKeyboardMarkup(keyboard)
    
    def truncate_name(self, name: str, max_length: int) -> str:
        """
        Обрезает название до максимальной длины
        
        Args:
            name: Исходное название
            max_length: Максимальная длина
            
        Returns:
            str: Обрезанное название
        """
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
    
    def wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        Переносит текст по словам для соответствия максимальной ширине
        
        Args:
            text: Исходный текст
            max_width: Максимальная ширина строки
            
        Returns:
            List[str]: Список строк с переносами
        """
        if not text:
            return [""]
        
        if len(text) <= max_width:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # Если добавление этого слова превысит ширину
            if len(current_line) + len(word) + 1 > max_width:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Одно слово слишком длинное, разделяем его дефисом
                    lines.append(word[:max_width-1] + "-")
                    current_line = word[max_width-1:]
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def get_status_emoji(self, status: str, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """
        Возвращает эмодзи для статуса
        
        Args:
            status: Статус (confirmed, error, partial, no_match, exact_match, matched)
            context: Контекст для определения языка
            
        Returns:
            str: Эмодзи для статуса
        """
        # Получаем локализованные эмодзи для статусов
        status_emoji_key = f"common.status_emojis.{status}"
        emoji = self.locale_manager.get_text(status_emoji_key, context)
        
        # Если эмодзи не найден, возвращаем эмодзи по умолчанию
        if emoji == status_emoji_key:  # Если ключ не найден, get_text возвращает сам ключ
            emoji = self.locale_manager.get_text("common.status_emojis.unknown", context)
        
        return emoji
    
    def format_number_with_spaces(self, number: Optional[float]) -> str:
        """
        Форматирует число в русском стиле: пробелы для тысяч, запятая для десятичных
        
        Args:
            number: Число для форматирования
            
        Returns:
            str: Отформатированное число
        """
        # Handle None values
        if number is None:
            return "0"
        
        # Always show number as integer if it's whole
        if number == int(number):
            return f"{int(number):,}".replace(",", " ")
        else:
            # If there are decimal places, use comma as decimal separator
            formatted = f"{number:,.2f}".replace(",", " ")
            # Replace the last dot with comma for Russian decimal format
            if '.' in formatted:
                parts = formatted.split('.')
                if len(parts) == 2:
                    # Remove trailing zeros from decimal part
                    decimal_part = parts[1].rstrip('0')
                    if decimal_part:
                        return f"{parts[0]},{decimal_part}"
                    else:
                        return parts[0]
            return formatted
