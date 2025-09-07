"""
Общие методы для обработчиков Telegram бота
Содержит переиспользуемую логику для устранения дублирования кода
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisService


class CommonHandlers:
    """Класс с общими методами для всех обработчиков"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
    
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
            print(f"DEBUG: Unknown ingredient type: {ingredient_type}")
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
            print(f"DEBUG: Loaded {len(poster_ingredients)} poster ingredients")
        
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
            print(f"✅ Загружено {len(google_sheets_ingredients)} ингредиентов Google Sheets по требованию")
            print(f"DEBUG: Первые 5 ингредиентов: {list(google_sheets_ingredients.keys())[:5]}")
        
        return True
    
    def format_table_with_pagination(self, data: List[Dict[str, Any]], 
                                   page: int = 1, 
                                   items_per_page: int = 10,
                                   table_formatter: callable = None) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Форматирует таблицу с пагинацией
        
        Args:
            data: Список данных для отображения
            page: Номер страницы (начиная с 1)
            items_per_page: Количество элементов на странице
            table_formatter: Функция для форматирования строки таблицы
            
        Returns:
            Tuple[str, InlineKeyboardMarkup]: Текст таблицы и клавиатура навигации
        """
        if not data:
            return "Нет данных для отображения", InlineKeyboardMarkup([])
        
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
            table_text = self._default_table_formatter(page_data, page, start_idx)
        
        # Создаем клавиатуру навигации
        navigation_keyboard = self.create_navigation_buttons(page, total_pages)
        
        return table_text, navigation_keyboard
    
    def _default_table_formatter(self, data: List[Dict[str, Any]], 
                                page: int, start_idx: int) -> str:
        """Форматирование таблицы по умолчанию"""
        if not data:
            return "Нет данных для отображения"
        
        # Простое форматирование - можно переопределить в наследниках
        lines = [f"Страница {page}:"]
        for i, item in enumerate(data, start_idx + 1):
            lines.append(f"{i}. {str(item)}")
        
        return "\n".join(lines)
    
    def create_navigation_buttons(self, current_page: int, total_pages: int, 
                                base_callback: str = "page") -> InlineKeyboardMarkup:
        """
        Создает стандартные кнопки навигации для пагинации
        
        Args:
            current_page: Текущая страница
            total_pages: Общее количество страниц
            base_callback: Базовое имя callback для кнопок
            
        Returns:
            InlineKeyboardMarkup: Клавиатура с кнопками навигации
        """
        if total_pages <= 1:
            return InlineKeyboardMarkup([])
        
        keyboard = []
        
        # Кнопки навигации
        nav_buttons = []
        
        # Кнопка "Первая страница"
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton("⏮️", callback_data=f"{base_callback}_1"))
        
        # Кнопка "Предыдущая страница"
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"{base_callback}_{current_page - 1}"))
        
        # Информация о текущей странице
        nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
        
        # Кнопка "Следующая страница"
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"{base_callback}_{current_page + 1}"))
        
        # Кнопка "Последняя страница"
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton("⏭️", callback_data=f"{base_callback}_{total_pages}"))
        
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
    
    def get_status_emoji(self, status: str) -> str:
        """
        Возвращает эмодзи для статуса
        
        Args:
            status: Статус (confirmed, error, partial, no_match, exact_match, matched)
            
        Returns:
            str: Эмодзи для статуса
        """
        status_emojis = {
            'confirmed': '✅',
            'error': '🔴',
            'partial': '⚠️',
            'no_match': '❌',
            'exact_match': '🟢',
            'matched': '✅',
            'partial_match': '🟡'
        }
        
        return status_emojis.get(status, '❓')
    
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
