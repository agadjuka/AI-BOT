"""
Message handlers for Telegram bot
"""
import asyncio
import json
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from models.receipt import ReceiptData, ReceiptItem
from models.ingredient_matching import IngredientMatchingResult
from services.ai_service import ReceiptAnalysisService
from services.ingredient_matching_service import IngredientMatchingService
from utils.formatters import ReceiptFormatter, NumberFormatter, TextParser
from utils.ingredient_formatter import IngredientFormatter
from utils.ingredient_storage import IngredientStorage
from utils.receipt_processor import ReceiptProcessor
from utils.ui_manager import UIManager
from validators.receipt_validator import ReceiptValidator


class MessageHandlers:
    """Handlers for Telegram messages"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.formatter = ReceiptFormatter()
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
        self.processor = ReceiptProcessor()
        self.validator = ReceiptValidator()
        self.ingredient_matching_service = IngredientMatchingService()
        self.ingredient_formatter = IngredientFormatter()
        self.ingredient_storage = IngredientStorage()
        self.ui_manager = UIManager(config)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Create start menu with buttons
        keyboard = [
            [InlineKeyboardButton("📸 Анализировать чек", callback_data="analyze_receipt")],
            [InlineKeyboardButton("📄 Получить файл для загрузки в постер", callback_data="generate_supply_file")]
        ]
        
        # Add back button if there's existing receipt data
        if context.user_data.get('receipt_data'):
            keyboard.append([InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(
            f"Привет, {update.effective_user.mention_html()}! 👋\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
        return self.config.AWAITING_CORRECTION
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle photo upload"""
        # Set anchor message (first receipt message)
        self.ui_manager.set_anchor(context, update.message.message_id)
        
        # ALWAYS clear ALL data when uploading new photo to ensure completely fresh start
        self._clear_receipt_data(context)
        print(f"DEBUG: Cleared all data for new receipt upload")
        
        processing_message = await self.ui_manager.send_temp(update, context, "Обрабатываю квитанцию", duration=10)
        
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(self.config.PHOTO_FILE_NAME)

        try:
            analysis_data = self.analysis_service.analyze_receipt(self.config.PHOTO_FILE_NAME)
            
            # Convert to ReceiptData model
            receipt_data = ReceiptData.from_dict(analysis_data)
            
            # Validate and correct data
            is_valid, message = self.validator.validate_receipt_data(receipt_data)
            if not is_valid:
                print(f"Предупреждение валидации: {message}")
            
            context.user_data['receipt_data'] = receipt_data
            # Save original data for change tracking
            context.user_data['original_data'] = ReceiptData.from_dict(receipt_data.to_dict())  # Deep copy
            
            # AUTOMATICALLY create ingredient matching table for this receipt
            await self._create_ingredient_matching_for_receipt(update, context, receipt_data)
            
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            print(f"Ошибка парсинга JSON или структуры данных от Gemini: {e}")
            await update.message.reply_text("Не удалось распознать структуру чека. Попробуйте сделать фото более четким.")
            return self.config.AWAITING_CORRECTION

        # Always show final report with edit button
        await self.show_final_report_with_edit_button(update, context)
        return self.config.AWAITING_CORRECTION  # Stay in active state for button processing
    
    async def handle_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user text input"""
        user_input = update.message.text.strip()
        line_number = context.user_data.get('line_to_edit')
        field_to_edit = context.user_data.get('field_to_edit')
        
        print(f"DEBUG: handle_user_input called with: '{user_input}'")
        print(f"DEBUG: Current conversation state: {context.user_data.get('_conversation_state')}")
        print(f"DEBUG: google_sheets_search_mode: {context.user_data.get('google_sheets_search_mode')}")
        print(f"DEBUG: awaiting_google_sheets_ingredient_name: {context.user_data.get('awaiting_google_sheets_ingredient_name')}")
        print(f"DEBUG: google_sheets_search_item_index: {context.user_data.get('google_sheets_search_item_index')}")
        
        # Delete user message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение пользователя: {e}")
        
        # Check for Google Sheets ingredient search
        if context.user_data.get('awaiting_google_sheets_ingredient_name'):
            return await self._handle_google_sheets_ingredient_search(update, context, user_input)
        
        # Check for Google Sheets search mode
        if context.user_data.get('google_sheets_search_mode'):
            print(f"DEBUG: Google Sheets search mode detected for input: '{user_input}'")
            return await self._handle_google_sheets_search(update, context, user_input)
        
        if field_to_edit:
            # Edit specific field
            return await self._handle_field_edit(update, context, user_input, line_number, field_to_edit)
        else:
            # Old format (for compatibility)
            return await self._handle_old_format_edit(update, context, user_input, line_number)
    
    async def _handle_field_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                user_input: str, line_number: int, field_to_edit: str) -> int:
        """Handle field-specific editing"""
        try:
            data: ReceiptData = context.user_data['receipt_data']
            item_to_edit = data.get_item(line_number)
            
            if not item_to_edit:
                await update.message.reply_text("Ошибка: строка не найдена")
                return self.config.AWAITING_FIELD_EDIT
            
            # Process input based on field type
            if field_to_edit == 'name':
                is_valid, message = self.validator.validate_text_input(user_input, "название товара")
                if not is_valid:
                    await self.ui_manager.send_temp(
                        update, context, f"Ошибка: {message}", duration=5
                    )
                    return self.config.AWAITING_FIELD_EDIT
                item_to_edit.name = user_input
                
            elif field_to_edit in ['quantity', 'price', 'total']:
                # Parse number, considering possible separators (including decimal fractions)
                numeric_value = self.text_parser.parse_user_input_number(user_input)
                if numeric_value < 0:
                    await self.ui_manager.send_temp(
                        update, context, "Значение не может быть отрицательным. Попробуйте еще раз.", duration=5
                    )
                    return self.config.AWAITING_FIELD_EDIT
                
                setattr(item_to_edit, field_to_edit, numeric_value)
                
                # If changed quantity or price, and sum was automatically calculated,
                # then recalculate sum automatically
                if field_to_edit in ['quantity', 'price'] and item_to_edit.auto_calculated:
                    quantity = item_to_edit.quantity
                    price = item_to_edit.price
                    if quantity is not None and price is not None and quantity > 0 and price > 0:
                        item_to_edit.total = quantity * price
                        item_to_edit.auto_calculated = True
                elif field_to_edit == 'total':
                    # If user manually entered sum, reset automatic calculation flag
                    item_to_edit.auto_calculated = False
            
            # Automatically calculate sum and update status based on new data
            item_to_edit = self.processor.auto_calculate_total_if_needed(item_to_edit)
            item_to_edit = self.processor.auto_update_item_status(item_to_edit)
            
            # Update ingredient matching after item edit
            await self._update_ingredient_matching_after_data_change(update, context, data, "item_edit")
            
            # Show success message
            field_labels = {
                'name': 'название товара',
                'quantity': 'количество',
                'price': 'цену за единицу',
                'total': 'сумму'
            }
            
            new_value = getattr(item_to_edit, field_to_edit, '')
            if field_to_edit in ['quantity', 'price', 'total'] and isinstance(new_value, (int, float)):
                new_value = self.number_formatter.format_number_with_spaces(new_value)
            
            status_icon = "✅" if item_to_edit.status == 'confirmed' else "🔴" if item_to_edit.status == 'error' else "⚠️"
            
            # Show success message
            await self.ui_manager.send_temp(
                update, context,
                f"✅ Обновлено! {field_labels[field_to_edit].capitalize()}: **{new_value}** {status_icon}",
                duration=2
            )
            
            # Show updated edit menu with new data
            edit_menu_message_id = context.user_data.get('edit_menu_message_id')
            await self._send_edit_menu(update, context, edit_menu_message_id)
            
            return self.config.AWAITING_FIELD_EDIT
            
        except Exception as e:
            print(f"Ошибка при редактировании поля: {e}")
            # Show updated edit menu even on error
            edit_menu_message_id = context.user_data.get('edit_menu_message_id')
            await self._send_edit_menu(update, context, edit_menu_message_id)
            return self.config.AWAITING_FIELD_EDIT
    
    async def _handle_old_format_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    user_input: str, line_number: int) -> int:
        """Handle old format editing (for compatibility)"""
        try:
            name, qty_str, price_str, total_str = [x.strip() for x in user_input.split(',')]
            qty = float(qty_str)
            price = float(price_str)
            total = float(total_str)
            
            data: ReceiptData = context.user_data['receipt_data']
            item = data.get_item(line_number)
            if item:
                item.name = name
                item.quantity = qty
                item.price = price
                item.total = total
                # Automatically update status based on new data
                item = self.processor.auto_update_item_status(item)
            
            # Update ingredient matching after item edit
            await self._update_ingredient_matching_after_data_change(update, context, data, "item_edit")
            
            # Update report with new data
            await self.show_final_report_with_edit_button(update, context)
            return self.config.AWAITING_CORRECTION

        except (ValueError, IndexError):
            await self.ui_manager.send_temp(
                update, context,
                "Ошибка формата. Пожалуйста, попробуйте еще раз.\n"
                "Формат: `Название, Количество, Цена, Сумма` (4 значения через запятую)\n"
                "Пример: `Udang Kupas, 4, 150000, 600000`",
                duration=10
            )
            return self.config.AWAITING_INPUT
    
    async def handle_line_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle line number input for editing"""
        user_input = update.message.text.strip()
        
        try:
            line_number = int(user_input)
            
            # Check if line number is valid
            data: ReceiptData = context.user_data.get('receipt_data')
            is_valid, message = self.validator.validate_line_number(data, line_number)
            
            if not is_valid:
                await self.ui_manager.send_temp(
                    update, context, f"{message}\n\nПопробуйте еще раз:", duration=10
                )
                return self.config.AWAITING_LINE_NUMBER
            
            # Delete user message
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение пользователя: {e}")
            
            
            # Set line number for editing
            context.user_data['line_to_edit'] = line_number
            
            # Show edit menu for line
            await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
            
        except ValueError:
            await self.ui_manager.send_temp(
                update, context, "Неверный формат. Введите только номер строки (например: `3`):", duration=10
            )
            return self.config.AWAITING_LINE_NUMBER
    
    async def handle_delete_line_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle line number input for deletion"""
        user_input = update.message.text.strip()
        
        try:
            line_number = int(user_input)
            
            # Check if line number is valid
            data: ReceiptData = context.user_data.get('receipt_data')
            is_valid, message = self.validator.validate_line_number(data, line_number)
            
            if not is_valid:
                await self.ui_manager.send_temp(
                    update, context, f"{message}\n\nПопробуйте еще раз:", duration=10
                )
                return self.config.AWAITING_DELETE_LINE_NUMBER
            
            # Delete user message
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение пользователя: {e}")
            
            
            # Remove line from data
            success = data.remove_item(line_number)
            if success:
                # Update original_data to reflect the changes
                if context.user_data.get('original_data'):
                    context.user_data['original_data'].remove_item(line_number)
                
                # Update ingredient matching after line deletion
                await self._update_ingredient_matching_after_deletion(update, context, data, line_number)
                
                # Show success message
                await self.ui_manager.send_temp(
                    update, context, f"✅ Строка {line_number} удалена! Обновляю таблицу...", duration=2
                )
                
                # Return to updated report
                await self.show_final_report_with_edit_button(update, context)
            
            return self.config.AWAITING_CORRECTION
            
        except ValueError:
            await self.ui_manager.send_temp(
                update, context, "Неверный формат. Введите только номер строки (например: `3`):", duration=10
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
    
    async def handle_total_edit_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle total sum edit input"""
        user_input = update.message.text.strip()
        
        # Delete user message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение пользователя: {e}")
        
        
        try:
            # Parse new total sum
            new_total = self.text_parser.parse_user_input_number(user_input)
            
            if new_total < 0:
                await self.ui_manager.send_temp(
                    update, context, "Итоговая сумма не может быть отрицательной. Попробуйте еще раз.", duration=5
                )
                return self.config.AWAITING_TOTAL_EDIT
            
            # Update total sum in data
            data: ReceiptData = context.user_data.get('receipt_data')
            data.grand_total_text = str(int(new_total)) if new_total == int(new_total) else str(new_total)
            
            # Update original_data to reflect the changes
            if context.user_data.get('original_data'):
                context.user_data['original_data'].grand_total_text = data.grand_total_text
            
            # Update ingredient matching after total change
            await self._update_ingredient_matching_after_data_change(update, context, data, "total_change")
            
            # Show success message
            formatted_total = self.number_formatter.format_number_with_spaces(new_total)
            await self.ui_manager.send_temp(
                update, context, f"✅ Итоговая сумма обновлена: **{formatted_total}**", duration=2
            )
            
            # Return to updated report
            await self.show_final_report_with_edit_button(update, context)
            
            return self.config.AWAITING_CORRECTION
            
        except Exception as e:
            print(f"Ошибка при обновлении итоговой суммы: {e}")
            await self.ui_manager.send_temp(
                update, context, "Ошибка при обновлении итоговой суммы. Попробуйте еще раз.", duration=5
            )
            return self.config.AWAITING_TOTAL_EDIT
    
    async def handle_ingredient_matching_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle manual ingredient matching input"""
        user_input = update.message.text.strip()
        
        # Delete user message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение пользователя: {e}")
        
        # Check if we're waiting for search input
        if context.user_data.get('awaiting_search'):
            context.user_data.pop('awaiting_search', None)
            return await self._handle_ingredient_search(update, context, user_input)
        
        # Check if we're waiting for position search input
        if context.user_data.get('awaiting_position_search'):
            context.user_data.pop('awaiting_position_search', None)
            return await self._handle_position_search(update, context, user_input)
        
        # Check if we're waiting for line number input for position matching
        if context.user_data.get('awaiting_line_number_for_position'):
            context.user_data.pop('awaiting_line_number_for_position', None)
            return await self._handle_line_number_for_position(update, context, user_input)
        
        # Check if we're waiting for ingredient name input for position matching
        if context.user_data.get('awaiting_ingredient_name_for_position'):
            context.user_data.pop('awaiting_ingredient_name_for_position', None)
            return await self._handle_ingredient_name_for_position(update, context, user_input)
        
        # Check if we're in position selection mode and user entered a line number
        if context.user_data.get('in_position_selection_mode'):
            return await self._handle_line_number_for_position(update, context, user_input)
        
        # Get current matching data
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        current_match = matching_result.matches[current_match_index]
        
        try:
            if user_input == "0":
                # Skip this ingredient
                await self.ui_manager.send_temp(
                    update, context, f"✅ Пропущен ингредиент: {current_match.receipt_item_name}", duration=2
                )
                await self._process_next_ingredient_match(update, context)
                
            elif user_input.startswith("search:"):
                # Search for ingredients
                query = user_input[7:].strip()
                if not query:
                    await self.ui_manager.send_temp(
                        update, context, "Введите поисковый запрос после 'search:'", duration=5
                    )
                    return self.config.AWAITING_MANUAL_MATCH
                
                return await self._handle_ingredient_search(update, context, query)
                
            else:
                # Try to parse as suggestion number
                try:
                    suggestion_number = int(user_input)
                    if 1 <= suggestion_number <= len(current_match.suggested_matches):
                        # Apply suggestion
                        selected_suggestion = current_match.suggested_matches[suggestion_number - 1]
                        manual_match = self.ingredient_matching_service.manual_match_ingredient(
                            current_match.receipt_item_name,
                            selected_suggestion['id'],
                            poster_ingredients
                        )
                        
                        # Update the match in the result
                        matching_result.matches[current_match_index] = manual_match
                        context.user_data['ingredient_matching_result'] = matching_result
                        
                        await self.ui_manager.send_temp(
                            update, context, f"✅ Сопоставлено: {current_match.receipt_item_name} → {selected_suggestion['name']}", duration=2
                        )
                        await self._process_next_ingredient_match(update, context)
                        
                    else:
                        await self.ui_manager.send_temp(
                            update, context, f"Неверный номер. Введите число от 1 до {len(current_match.suggested_matches)} или 0 для пропуска.", duration=5
                        )
                        return self.config.AWAITING_MANUAL_MATCH
                        
                except ValueError:
                    await self.ui_manager.send_temp(
                        update, context, "Неверный формат. Введите номер предложения, 0 для пропуска или 'search: запрос' для поиска.", duration=5
                    )
                    return self.config.AWAITING_MANUAL_MATCH
                    
        except Exception as e:
            print(f"Ошибка при обработке ручного сопоставления: {e}")
            await self.ui_manager.send_temp(
                update, context, "Произошла ошибка. Попробуйте еще раз.", duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_position_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
        """Handle position search for manual matching"""
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Search for ingredients in the loaded list
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            query, poster_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                search_text = f"**Результаты поиска для '{query}':**\n\n"
                search_text += f"Найдено вариантов: **{len(filtered_results)}**\n\n"
                search_text += "**Выберите ингредиент для сопоставления:**\n"
                
                # Create horizontal buttons for search results (max 2 per row)
                keyboard = []
                for i, result in enumerate(filtered_results[:8], 1):  # Show up to 8 results
                    name = self.ingredient_formatter._truncate_name(result['name'], 15)
                    score = int(result['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    
                    if i % 2 == 1:
                        # Start new row
                        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_position_{i}")])
                    else:
                        # Add to existing row
                        keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_position_{i}"))
                
                # Add control buttons
                keyboard.extend([
                    [InlineKeyboardButton("🔍 Новый поиск", callback_data="select_position_for_matching")],
                    [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_receipt")]
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.ui_manager.send_menu(
                    update, context, search_text, reply_markup, 'Markdown'
                )
                
                # Save search results for selection
                context.user_data['position_search_results'] = filtered_results
            else:
                await self.ui_manager.send_menu(
                    update, context,
                    f"❌ **По запросу '{query}' не найдено подходящих вариантов**\n\n"
                    "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Новый поиск", callback_data="select_position_for_matching")],
                        [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
        else:
            await self.ui_manager.send_menu(
                update, context,
                f"❌ **По запросу '{query}' ничего не найдено**\n\n"
                "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Новый поиск", callback_data="select_position_for_matching")],
                    [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_ingredient_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
        """Handle ingredient search"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        current_match = matching_result.matches[current_match_index]
        
        # Search for ingredients
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            query, poster_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                progress_text = f"**Результаты поиска для '{query}':**\n\n"
                progress_text += f"**Текущий товар:** {current_match.receipt_item_name}\n\n"
                progress_text += "**Выберите подходящий ингредиент:**\n"
                
                # Create buttons for search results (max 4 buttons)
                keyboard = []
                for i, result in enumerate(filtered_results[:4], 1):
                    name = self.ingredient_formatter._truncate_name(result['name'], 20)
                    score = int(result['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_search_{i}")])
                
                # Add control buttons
                keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search_ingredient")])
                keyboard.append([InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_ingredient")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.ui_manager.send_menu(
                    update, context, progress_text, reply_markup, 'Markdown'
                )
                
                # Save search results for selection
                context.user_data['search_results'] = filtered_results
            else:
                await self.ui_manager.send_temp(
                    update, context, f"По запросу '{query}' не найдено подходящих вариантов (с вероятностью > 50%).", duration=5
                )
        else:
            await self.ui_manager.send_temp(
                update, context, f"По запросу '{query}' ничего не найдено.", duration=5
            )
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_line_number_for_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle line number input for position matching"""
        try:
            line_number = int(user_input)
            
            # Check if line number is valid
            matching_result = context.user_data.get('ingredient_matching_result')
            if not matching_result or line_number < 1 or line_number > len(matching_result.matches):
                await self.ui_manager.send_temp(
                    update, context, f"Неверный номер строки. Введите число от 1 до {len(matching_result.matches) if matching_result else 0}", duration=5
                )
                return self.config.AWAITING_MANUAL_MATCH
            
            # Set the selected line number for position matching
            context.user_data['selected_line_number'] = line_number
            
            # Clear position selection mode flag
            context.user_data.pop('in_position_selection_mode', None)
            
            # Show instruction to enter ingredient name
            await self.ui_manager.send_temp(
                update, context, f"Выбрана строка {line_number}. Теперь введите название ингредиента из постер для поиска:", duration=10
            )
            context.user_data['awaiting_ingredient_name_for_position'] = True
            
            return self.config.AWAITING_MANUAL_MATCH
            
        except ValueError:
            await self.ui_manager.send_temp(
                update, context, "Неверный формат. Введите только номер строки (например: `3`):", duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_ingredient_name_for_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle ingredient name input for position matching"""
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
        
        # Search for ingredients in the loaded list
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            user_input, poster_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                search_text = f"**Результаты поиска для '{user_input}':**\n\n"
                search_text += f"Найдено вариантов: **{len(filtered_results)}**\n\n"
                search_text += "**Выберите ингредиент для сопоставления:**\n"
                
                # Create horizontal buttons for search results (max 2 per row)
                keyboard = []
                for i, result in enumerate(filtered_results[:8], 1):  # Show up to 8 results
                    name = self.ingredient_formatter._truncate_name(result['name'], 15)
                    score = int(result['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    
                    if i % 2 == 1:
                        # Start new row
                        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_position_match_{i}")])
                    else:
                        # Add to existing row
                        keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_position_match_{i}"))
                
                # Add control buttons
                keyboard.extend([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.ui_manager.send_menu(
                    update, context, search_text, reply_markup, 'Markdown'
                )
                
                # Save search results for selection
                context.user_data['position_match_search_results'] = filtered_results
            else:
                await self.ui_manager.send_menu(
                    update, context,
                    f"❌ **По запросу '{user_input}' не найдено подходящих вариантов**\n\n"
                    "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
        else:
            await self.ui_manager.send_menu(
                update, context,
                f"❌ **По запросу '{user_input}' ничего не найдено**\n\n"
                "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _process_next_ingredient_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process next ingredient match or finish matching"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            return
        
        current_match_index += 1
        context.user_data['current_match_index'] = current_match_index
        
        if current_match_index >= len(matching_result.matches):
            # All matches processed, show final result
            await self._show_final_ingredient_matching_result(update, context)
        else:
            # Show next match
            await self._show_manual_matching_for_current_item(update, context)
    
    async def _show_manual_matching_for_current_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching interface for current item"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            return
        
        current_match = matching_result.matches[current_match_index]
        
        # Show current match info
        progress_text = f"**Сопоставление ингредиентов** ({current_match_index + 1}/{len(matching_result.matches)})\n\n"
        progress_text += f"**Текущий товар:** {current_match.receipt_item_name}\n\n"
        
        if current_match.match_status.value == "exact":
            # Already matched, show confirmation
            progress_text += f"✅ **Автоматически сопоставлено:** {current_match.matched_ingredient_name}\n\n"
            progress_text += "Нажмите /continue для перехода к следующему товару."
        else:
            # Show suggestions for manual matching
            if current_match.suggested_matches:
                suggestions_text = self.ingredient_formatter.format_suggestions_for_manual_matching(current_match)
                progress_text += suggestions_text + "\n\n"
            
            instructions = self.ingredient_formatter.format_manual_matching_instructions()
            progress_text += instructions
        
        await self.ui_manager.send_menu(
            update, context, progress_text, InlineKeyboardMarkup([]), 'Markdown'
        )
    
    async def _show_final_ingredient_matching_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final ingredient matching result"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        # Format final result
        final_text = self.ingredient_formatter.format_matching_table(matching_result)
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, final_text, reply_markup, 'Markdown'
        )
    
    async def _create_ingredient_matching_for_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, receipt_data: ReceiptData) -> None:
        """Automatically create ingredient matching table for the receipt"""
        try:
            # Get poster ingredients from bot data
            poster_ingredients = context.bot_data.get('poster_ingredients', {})
            
            if not poster_ingredients:
                print("DEBUG: Poster ingredients not loaded, skipping automatic matching")
                return
            
            # Perform ingredient matching
            matching_result = self.ingredient_matching_service.match_ingredients(receipt_data, poster_ingredients)
            
            # Save matching result to context
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['changed_ingredient_indices'] = set()
            context.user_data['current_match_index'] = 0
            
            # Save to persistent storage
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            success = self.ingredient_storage.save_matching_result(user_id, matching_result, set(), receipt_hash)
            print(f"DEBUG: Auto-created matching for receipt {receipt_hash}, success: {success}")
            
        except Exception as e:
            print(f"DEBUG: Error creating automatic ingredient matching: {e}")
    
    async def _auto_match_ingredient_for_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                            receipt_item: ReceiptItem) -> None:
        """Automatically match ingredient for a single item"""
        try:
            # Get poster ingredients from bot data
            poster_ingredients = context.bot_data.get('poster_ingredients', {})
            
            if not poster_ingredients:
                print("DEBUG: Poster ingredients not loaded, skipping automatic matching for new item")
                return None
            
            # Perform ingredient matching for this single item
            from models.receipt import ReceiptData
            temp_receipt = ReceiptData(items=[receipt_item])
            matching_result = self.ingredient_matching_service.match_ingredients(temp_receipt, poster_ingredients)
            
            if matching_result.matches:
                return matching_result.matches[0]  # Return the first (and only) match
            return None
            
        except Exception as e:
            print(f"DEBUG: Error in automatic ingredient matching for item: {e}")
            return None

    async def _update_ingredient_matching_after_data_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                           receipt_data: ReceiptData, change_type: str = "general") -> None:
        """Update ingredient matching after any data change"""
        try:
            # Get current matching result from context or storage
            matching_result = context.user_data.get('ingredient_matching_result')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if not matching_result:
                # Try to load from storage using old hash
                user_id = update.effective_user.id
                old_receipt_data = context.user_data.get('original_data')
                if old_receipt_data:
                    old_receipt_hash = old_receipt_data.get_receipt_hash()
                    saved_data = self.ingredient_storage.load_matching_result(user_id, old_receipt_hash)
                    if saved_data:
                        matching_result, changed_indices = saved_data
                        # Update context with loaded data
                        context.user_data['ingredient_matching_result'] = matching_result
                        context.user_data['changed_ingredient_indices'] = changed_indices
            
            if not matching_result:
                print(f"DEBUG: No matching result found to update after {change_type}")
                return
            
            # For different change types, we need different handling
            if change_type == "deletion":
                # This will be handled by the specific deletion function
                return
            elif change_type == "addition":
                # Add a new empty match for the new item
                from models.ingredient_matching import IngredientMatch, MatchStatus
                new_match = IngredientMatch(
                    receipt_item_name="Новый товар",
                    matched_ingredient_name="",
                    matched_ingredient_id="",
                    match_status=MatchStatus.NO_MATCH,
                    similarity_score=0.0,
                    suggested_matches=[]
                )
                matching_result.matches.append(new_match)
                
            elif change_type == "item_edit":
                # For item edits, we need to regenerate matching for that specific item
                # This is more complex, so for now we'll just mark that matching needs to be redone
                # The user will need to redo ingredient matching if they want accurate results
                print("DEBUG: Item edited - ingredient matching may need to be redone")
                return
                
            # Update context
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['changed_ingredient_indices'] = changed_indices
            
            # Save updated matching result with new receipt hash
            user_id = update.effective_user.id
            new_receipt_hash = receipt_data.get_receipt_hash()
            success = self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, new_receipt_hash)
            
            # Clear old matching result file if hash changed
            if context.user_data.get('original_data'):
                old_receipt_hash = context.user_data['original_data'].get_receipt_hash()
                if old_receipt_hash != new_receipt_hash:
                    self.ingredient_storage.clear_matching_result(user_id, old_receipt_hash)
            
            print(f"DEBUG: Updated ingredient matching after {change_type}, new hash: {new_receipt_hash}, success: {success}")
                
        except Exception as e:
            print(f"DEBUG: Error updating ingredient matching after {change_type}: {e}")
    
    async def _update_ingredient_matching_after_deletion(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       receipt_data: ReceiptData, deleted_line_number: int) -> None:
        """Update ingredient matching after line deletion"""
        try:
            # Get current matching result from context or storage
            matching_result = context.user_data.get('ingredient_matching_result')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if not matching_result:
                # Try to load from storage using old hash
                user_id = update.effective_user.id
                old_receipt_data = context.user_data.get('original_data')
                if old_receipt_data:
                    old_receipt_hash = old_receipt_data.get_receipt_hash()
                    saved_data = self.ingredient_storage.load_matching_result(user_id, old_receipt_hash)
                    if saved_data:
                        matching_result, changed_indices = saved_data
                        # Update context with loaded data
                        context.user_data['ingredient_matching_result'] = matching_result
                        context.user_data['changed_ingredient_indices'] = changed_indices
            
            if not matching_result:
                print("DEBUG: No matching result found to update after deletion")
                return
            
            # Find the index of the deleted item in the matching result
            # The matching result should have the same order as the original receipt items
            deleted_index = None
            for i, match in enumerate(matching_result.matches):
                # We need to find the match that corresponds to the deleted line
                # Since we don't have direct mapping, we'll use the order
                if i == deleted_line_number - 1:  # Convert line number to 0-based index
                    deleted_index = i
                    break
            
            if deleted_index is not None:
                # Remove the match at the deleted index
                matching_result.matches.pop(deleted_index)
                
                # Update changed indices - remove any indices >= deleted_index and decrement others
                updated_changed_indices = set()
                for idx in changed_indices:
                    if idx < deleted_index:
                        updated_changed_indices.add(idx)
                    elif idx > deleted_index:
                        updated_changed_indices.add(idx - 1)
                # Don't add the deleted index itself
                
                # Update context
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = updated_changed_indices
                
                # Save updated matching result with new receipt hash
                user_id = update.effective_user.id
                new_receipt_hash = receipt_data.get_receipt_hash()
                success = self.ingredient_storage.save_matching_result(user_id, matching_result, updated_changed_indices, new_receipt_hash)
                
                # Clear old matching result file
                if context.user_data.get('original_data'):
                    old_receipt_hash = context.user_data['original_data'].get_receipt_hash()
                    if old_receipt_hash != new_receipt_hash:
                        self.ingredient_storage.clear_matching_result(user_id, old_receipt_hash)
                
                print(f"DEBUG: Updated ingredient matching after deletion, new hash: {new_receipt_hash}, success: {success}")
            else:
                print(f"DEBUG: Could not find matching index for deleted line {deleted_line_number}")
                
        except Exception as e:
            print(f"DEBUG: Error updating ingredient matching after deletion: {e}")
    
    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all receipt-related data from context"""
        keys_to_clear = [
            'receipt_data', 'original_data', 'line_to_edit', 'field_to_edit',
            'cached_final_report', 'table_message_id', 'edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id', 'ingredient_matching_result', 'current_match_index',
            'processing_message_id', 'changed_ingredient_indices', 'search_results',
            'position_search_results', 'awaiting_search', 'awaiting_position_search',
            'in_position_selection_mode', 'selected_line_number', 'position_match_search_results',
            'awaiting_ingredient_name_for_position'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    async def show_final_report_with_edit_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons"""
        # Clean up all messages except anchor
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        final_data: ReceiptData = context.user_data.get('receipt_data')
        
        if not final_data:
            await self.ui_manager.send_temp(
                update, context, "Произошла ошибка, данные не найдены.", duration=5
            )
            return

        try:
            # Automatically update statuses of all elements
            final_data = self.processor.auto_update_all_statuses(final_data)
            context.user_data['receipt_data'] = final_data
            
            # Check if there are errors
            has_errors = not self.processor.check_all_items_confirmed(final_data)
            
            # Create aligned table programmatically
            aligned_table = self.formatter.format_aligned_table(final_data)
            
            # Calculate total sum
            calculated_total = self.formatter.calculate_total_sum(final_data)
            receipt_total = self.text_parser.parse_number_from_text(final_data.grand_total_text)
            
            # Form final report
            final_report = ""
            
            # Add red marker if there are errors
            if has_errors:
                final_report += "🔴 **Обнаружены ошибки в данных чека**\n\n"
            
            final_report += f"```\n{aligned_table}\n```\n\n"
            
            if abs(calculated_total - receipt_total) < 0.01:
                final_report += "✅ **Итоговая сумма соответствует!**\n"
            else:
                difference = abs(calculated_total - receipt_total)
                final_report += f"❗ **Несоответствие итоговой суммы! Разница: {self.number_formatter.format_number_with_spaces(difference)}**\n"
            
            # Save report in cache for quick access
            context.user_data['cached_final_report'] = final_report
            
            # Create buttons
            keyboard = []
            
            # If there are errors, add buttons for fixing problematic lines
            if has_errors:
                fix_buttons = []
                for item in final_data.items:
                    status = item.status
                    
                    # Check calculation mismatch
                    quantity = item.quantity
                    price = item.price
                    total = item.total
                    has_calculation_error = False
                    
                    if quantity is not None and price is not None and total is not None and quantity > 0 and price > 0 and total > 0:
                        expected_total = quantity * price
                        has_calculation_error = abs(expected_total - total) > 0.01
                    
                    # Check if name is unreadable
                    item_name = item.name
                    is_unreadable = item_name == "???" or item_name == "**не распознано**"
                    
                    # If there are calculation errors, unreadable data or status not confirmed
                    if status != 'confirmed' or has_calculation_error or is_unreadable:
                        fix_buttons.append(InlineKeyboardButton(
                            f"Исправить строку {item.line_number}",
                            callback_data=f"edit_{item.line_number}"
                        ))
                
                # Distribute fix buttons across 1-3 columns based on quantity
                if fix_buttons:
                    if len(fix_buttons) <= 3:
                        # 1 column for 1-3 buttons
                        for button in fix_buttons:
                            keyboard.append([button])
                    elif len(fix_buttons) <= 6:
                        # 2 columns for 4-6 buttons
                        for i in range(0, len(fix_buttons), 2):
                            row = fix_buttons[i:i+2]
                            if len(row) == 1:
                                row.append(InlineKeyboardButton("", callback_data="noop"))  # Empty button for alignment
                            keyboard.append(row)
                    else:
                        # 3 columns for 7+ buttons
                        for i in range(0, len(fix_buttons), 3):
                            row = fix_buttons[i:i+3]
                            while len(row) < 3:
                                row.append(InlineKeyboardButton("", callback_data="noop"))  # Empty buttons for alignment
                            keyboard.append(row)
            
            # Add line management buttons
            keyboard.append([
                InlineKeyboardButton("➕ Добавить строку", callback_data="add_row"),
                InlineKeyboardButton("➖ Удалить строку", callback_data="delete_row")
            ])
            
            # Add edit line by number button under add/delete buttons
            keyboard.append([InlineKeyboardButton("🔢 Редактировать строку по номеру", callback_data="edit_line_number")])
            
            # Add total edit and reanalysis buttons in one row
            keyboard.append([
                InlineKeyboardButton("💰 Редактировать Итого", callback_data="edit_total"),
                InlineKeyboardButton("🔄 Проанализировать заново", callback_data="reanalyze")
            ])
            
            # Add Google Sheets upload button
            keyboard.append([InlineKeyboardButton("📊 Загрузить в Google Таблицы", callback_data="upload_to_google_sheets")])
            
            # Add file generation button
            keyboard.append([InlineKeyboardButton("📄 Получить файл для загрузки в постер", callback_data="generate_supply_file")])
            
            # Add back button
            keyboard.append([InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send report with buttons using UI manager
            message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
            # Save table message ID for subsequent editing
            context.user_data['table_message_id'] = message.message_id
        
        except Exception as e:
            print(f"Ошибка при формировании отчета: {e}")
            await self.ui_manager.send_temp(
                update, context, f"Произошла ошибка при формировании отчета: {e}", duration=5
            )
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id_to_edit: int = None):
        """Send edit menu for specific line"""
        line_number = context.user_data.get('line_to_edit')
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number)
        
        if not item_to_edit:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: строка не найдена", duration=5
            )
            return
        
        # Automatically calculate sum and update status before display
        item_to_edit = self.processor.auto_calculate_total_if_needed(item_to_edit)
        item_to_edit = self.processor.auto_update_item_status(item_to_edit)
        
        # Format current values
        name = item_to_edit.name
        quantity = self.number_formatter.format_number_with_spaces(item_to_edit.quantity)
        price = self.number_formatter.format_number_with_spaces(item_to_edit.price)
        total = self.number_formatter.format_number_with_spaces(item_to_edit.total)
        
        # Check if sum was automatically calculated
        is_auto_calculated = item_to_edit.auto_calculated
        
        # Determine current status (flag)
        status = item_to_edit.status
        if status == 'confirmed':
            status_icon = "✅"
        elif status == 'error':
            status_icon = "🔴"
        else:
            status_icon = "⚠️"
        
        text = f"**Редактирование строки {line_number}:** {status_icon}\n\n"
        text += f"📝 **Название:** {name}\n"
        text += f"🔢 **Количество:** {quantity}\n"
        text += f"💰 **Цена:** {price}\n"
        
        # Show sum with note about whether it was automatically calculated
        if is_auto_calculated:
            text += f"💵 **Сумма:** {total} *(автоматически рассчитана)*\n\n"
        else:
            text += f"💵 **Сумма:** {total}\n\n"
        
        text += "Выберите поле для редактирования:"
        
        keyboard = [
            [
                InlineKeyboardButton("📝 Название", callback_data=f"field_{line_number}_name"),
                InlineKeyboardButton("🔢 Количество", callback_data=f"field_{line_number}_quantity"),
                InlineKeyboardButton("💰 Цена", callback_data=f"field_{line_number}_price")
            ],
            [
                InlineKeyboardButton("💵 Сумма", callback_data=f"field_{line_number}_total"),
                InlineKeyboardButton("✅ Применить", callback_data=f"apply_{line_number}"),
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if message_id_to_edit:
            # Edit existing message
            success = await self.ui_manager.edit_menu(
                update, context, message_id_to_edit, text, reply_markup, 'Markdown'
            )
            if not success:
                # If couldn't edit, send new message
                message = await self.ui_manager.send_menu(
                    update, context, text, reply_markup, 'Markdown'
                )
                context.user_data['edit_menu_message_id'] = message.message_id
        else:
            # Create new message
            message = await self.ui_manager.send_menu(
                update, context, text, reply_markup, 'Markdown'
            )
            # Save message ID for subsequent editing
            context.user_data['edit_menu_message_id'] = message.message_id
    
    async def _send_long_message_with_keyboard(self, message, text: str, reply_markup):
        """Send long message with keyboard"""
        if len(text) <= self.config.MAX_MESSAGE_LENGTH:
            sent_message = await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return sent_message
        
        # Split into parts
        parts = [text[i:i + self.config.MAX_MESSAGE_LENGTH] for i in range(0, len(text), self.config.MAX_MESSAGE_LENGTH)]
        
        # Send all parts except last
        for part in parts[:-1]:
            await message.reply_text(part, parse_mode='Markdown')
            await asyncio.sleep(self.config.MESSAGE_DELAY)
        
        # Send last part with keyboard
        sent_message = await message.reply_text(parts[-1], reply_markup=reply_markup, parse_mode='Markdown')
        return sent_message
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        if len(text) <= self.config.MAX_MESSAGE_LENGTH:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Split into parts
        parts = [text[i:i + self.config.MAX_MESSAGE_LENGTH] for i in range(0, len(text), self.config.MAX_MESSAGE_LENGTH)]
        
        # Send all parts except last
        for part in parts[:-1]:
            await message.reply_text(part, parse_mode='Markdown')
            await asyncio.sleep(self.config.MESSAGE_DELAY)
        
        # Send last part with keyboard
        await message.reply_text(parts[-1], reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_google_sheets_ingredient_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle Google Sheets ingredient name search"""
        from handlers.callback_handlers import CallbackHandlers
        
        # Get the selected line number
        selected_line = context.user_data.get('selected_google_sheets_line')
        if not selected_line:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: не выбрана строка для сопоставления.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Get Google Sheets ingredients
        google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        
        if not google_sheets_ingredients:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: справочник Google Таблиц не загружен.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Convert format from {id: {'name': name}} to {name: id} for search service
        google_sheets_ingredients_for_search = {}
        for ingredient_id, ingredient_data in google_sheets_ingredients.items():
            ingredient_name = ingredient_data.get('name', '')
            if ingredient_name:
                google_sheets_ingredients_for_search[ingredient_name] = ingredient_id
        
        # Use the same smart search as in poster
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            user_input, google_sheets_ingredients_for_search, limit=10
        )
        
        print(f"DEBUG: Smart search for '{user_input}' in {len(google_sheets_ingredients_for_search)} Google Sheets ingredients (ingredient search)")
        print(f"DEBUG: Found {len(search_results)} search results (ingredient search)")
        
        # Clear the search flag
        context.user_data.pop('awaiting_google_sheets_ingredient_name', None)
        
        if search_results:
            # Show search results
            await self._show_google_sheets_search_results(update, context, user_input, search_results, selected_line)
        else:
            await self.ui_manager.send_temp(
                update, context, f"По запросу '{user_input}' в Google Таблицах ничего не найдено.", duration=5
            )
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_google_sheets_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle Google Sheets search mode"""
        print(f"DEBUG: _handle_google_sheets_search called with input: '{user_input}'")
        item_index = context.user_data.get('google_sheets_search_item_index')
        if item_index is None:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: не выбран товар для поиска.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Get Google Sheets ingredients
        google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        
        if not google_sheets_ingredients:
            # Try to load Google Sheets ingredients
            from google_sheets_handler import get_google_sheets_ingredients
            google_sheets_ingredients = get_google_sheets_ingredients()
            
            if not google_sheets_ingredients:
                await self.ui_manager.send_temp(
                    update, context, "Ошибка: справочник Google Таблиц не загружен.", duration=5
                )
                return self.config.AWAITING_CORRECTION
            
            # Save to bot data
            context.bot_data['google_sheets_ingredients'] = google_sheets_ingredients
            print(f"✅ Загружено {len(google_sheets_ingredients)} ингредиентов Google Sheets для поиска")
        else:
            print(f"✅ Используем уже загруженные {len(google_sheets_ingredients)} ингредиентов Google Sheets")
        
        # Convert format from {id: {'name': name}} to {name: id} for search service
        google_sheets_ingredients_for_search = {}
        for ingredient_id, ingredient_data in google_sheets_ingredients.items():
            ingredient_name = ingredient_data.get('name', '')
            if ingredient_name:
                google_sheets_ingredients_for_search[ingredient_name] = ingredient_id
        
        # Use the same smart search as in poster
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            user_input, google_sheets_ingredients_for_search, limit=10
        )
        
        print(f"DEBUG: Smart search for '{user_input}' in {len(google_sheets_ingredients_for_search)} Google Sheets ingredients")
        print(f"DEBUG: Found {len(search_results)} search results")
        if search_results:
            print(f"DEBUG: Top 3 results: {[r['name'] for r in search_results[:3]]}")
        else:
            print("DEBUG: No search results found - checking ingredient list:")
            print(f"DEBUG: Available ingredients: {list(google_sheets_ingredients_for_search.keys())[:10]}")
        
        # Clear search mode
        context.user_data.pop('google_sheets_search_mode', None)
        context.user_data.pop('google_sheets_search_item_index', None)
        
        if search_results:
            # Show search results for specific item
            await self._show_google_sheets_item_search_results(update, context, user_input, search_results, item_index)
        else:
            await self.ui_manager.send_temp(
                update, context, f"По запросу '{user_input}' в Google Таблицах ничего не найдено.", duration=5
            )
        
        return self.config.AWAITING_CORRECTION
    
    async def _show_google_sheets_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                               query: str, results: list, selected_line: int):
        """Show Google Sheets search results for position selection"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = f"**Результаты поиска в Google Таблицах для '{query}':**\n\n"
        
        # Create buttons for results
        keyboard = []
        for i, result in enumerate(results[:10], 1):  # Show max 10 results
            button_text = f"{i}. {self._truncate_name(result['name'], 25)}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_position_match_{selected_line}_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_google_sheets_matching")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, text, reply_markup, 'Markdown'
        )
    
    async def _show_google_sheets_item_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                    query: str, results: list, item_index: int):
        """Show Google Sheets search results for specific item"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        print(f"DEBUG: _show_google_sheets_item_search_results called with {len(results)} results for query '{query}'")
        text = f"**Результаты поиска в Google Таблицах для '{query}':**\n\n"
        
        # Save search results for callback handling
        context.user_data['google_sheets_search_results'] = results
        
        # Create buttons for results in two columns
        keyboard = []
        for i, result in enumerate(results[:10], 1):  # Show max 10 results
            button_text = f"{i}. {self._truncate_name(result['name'], 20)}"
            if i % 2 == 1:
                # Start new row
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_search_{item_index}_{i-1}")])
            else:
                # Add to existing row
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_search_{item_index}_{i-1}"))
        
        # Add back button
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_google_sheets_matching")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, text, reply_markup, 'Markdown'
        )
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name if too long"""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
