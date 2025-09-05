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
from utils.receipt_processor import ReceiptProcessor
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
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        await update.message.reply_html(
            f"Привет, {update.effective_user.mention_html()}! 👋\n\nОтправь мне фото рукописного чека для интерактивного анализа."
        )
        return self.config.AWAITING_CORRECTION
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle photo upload"""
        # Check if there's already receipt data being processed
        if context.user_data.get('receipt_data'):
            await update.message.reply_text("📋 Обнаружена новая квитанция. Заменяю предыдущую...")
            # Clear old data related to previous receipt
            self._clear_receipt_data(context)
        
        processing_message = await update.message.reply_text("Обрабатываю квитанцию")
        # Сохраняем ID сообщения для последующего удаления
        context.user_data['processing_message_id'] = processing_message.message_id
        
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
        
        # Delete user message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение пользователя: {e}")
        
        # Delete instruction message
        instruction_message_id = context.user_data.get('instruction_message_id')
        if instruction_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=instruction_message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение с инструкцией: {e}")
        
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
                    await update.message.reply_text(f"Ошибка: {message}")
                    return self.config.AWAITING_FIELD_EDIT
                item_to_edit.name = user_input
                
            elif field_to_edit in ['quantity', 'price', 'total']:
                # Parse number, considering possible separators (including decimal fractions)
                numeric_value = self.text_parser.parse_user_input_number(user_input)
                if numeric_value < 0:
                    await update.message.reply_text("Значение не может быть отрицательным. Попробуйте еще раз.")
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
            
            success_message = await update.message.reply_text(
                f"✅ Обновлено! {field_labels[field_to_edit].capitalize()}: **{new_value}** {status_icon}",
                parse_mode='Markdown'
            )
            
            # Show updated edit menu with new data
            edit_menu_message_id = context.user_data.get('edit_menu_message_id')
            await self._send_edit_menu(update, context, edit_menu_message_id)
            
            # Delete success message after 2 seconds
            await asyncio.sleep(2)
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=success_message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение об успехе: {e}")
            
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
            
            # Update report with new data
            await self.show_final_report_with_edit_button(update, context)
            return self.config.AWAITING_CORRECTION

        except (ValueError, IndexError):
            await update.message.reply_text(
                "Ошибка формата. Пожалуйста, попробуйте еще раз.\n"
                "Формат: `Название, Количество, Цена, Сумма` (4 значения через запятую)\n"
                "Пример: `Udang Kupas, 4, 150000, 600000`",
                parse_mode='Markdown'
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
                await update.message.reply_text(f"{message}\n\nПопробуйте еще раз:")
                return self.config.AWAITING_LINE_NUMBER
            
            # Delete user message
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение пользователя: {e}")
            
            # Delete instruction message
            instruction_message_id = context.user_data.get('line_number_instruction_message_id')
            if instruction_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=instruction_message_id
                    )
                except Exception as e:
                    print(f"Не удалось удалить сообщение с инструкцией: {e}")
            
            # Set line number for editing
            context.user_data['line_to_edit'] = line_number
            
            # Show edit menu for line
            await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
            
        except ValueError:
            await update.message.reply_text(
                "Неверный формат. Введите только номер строки (например: `3`):",
                parse_mode='Markdown'
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
                await update.message.reply_text(f"{message}\n\nПопробуйте еще раз:")
                return self.config.AWAITING_DELETE_LINE_NUMBER
            
            # Delete user message
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение пользователя: {e}")
            
            # Delete instruction message
            instruction_message_id = context.user_data.get('delete_line_number_instruction_message_id')
            if instruction_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=instruction_message_id
                    )
                except Exception as e:
                    print(f"Не удалось удалить сообщение с инструкцией: {e}")
            
            # Remove line from data
            success = data.remove_item(line_number)
            if success:
                # Show success message
                success_message = await update.message.reply_text(f"✅ Строка {line_number} удалена! Обновляю таблицу...")
                
                # Return to updated report
                await self.show_final_report_with_edit_button(update, context)
                
                # Delete success message
                try:
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=success_message.message_id
                    )
                except Exception as e:
                    print(f"Не удалось удалить сообщение об успехе: {e}")
            
            return self.config.AWAITING_CORRECTION
            
        except ValueError:
            await update.message.reply_text(
                "Неверный формат. Введите только номер строки (например: `3`):",
                parse_mode='Markdown'
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
        
        # Delete instruction message
        instruction_message_id = context.user_data.get('total_edit_instruction_message_id')
        if instruction_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=instruction_message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение с инструкцией: {e}")
        
        try:
            # Parse new total sum
            new_total = self.text_parser.parse_user_input_number(user_input)
            
            if new_total < 0:
                await update.message.reply_text("Итоговая сумма не может быть отрицательной. Попробуйте еще раз.")
                return self.config.AWAITING_TOTAL_EDIT
            
            # Update total sum in data
            data: ReceiptData = context.user_data.get('receipt_data')
            data.grand_total_text = str(int(new_total)) if new_total == int(new_total) else str(new_total)
            
            # Show success message
            formatted_total = self.number_formatter.format_number_with_spaces(new_total)
            success_message = await update.message.reply_text(f"✅ Итоговая сумма обновлена: **{formatted_total}**", parse_mode='Markdown')
            
            # Return to updated report
            await self.show_final_report_with_edit_button(update, context)
            
            # Delete success message
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=success_message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение об успехе: {e}")
            
            return self.config.AWAITING_CORRECTION
            
        except Exception as e:
            print(f"Ошибка при обновлении итоговой суммы: {e}")
            await update.message.reply_text("Ошибка при обновлении итоговой суммы. Попробуйте еще раз.")
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
        
        # Get current matching data
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await update.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return self.config.AWAITING_CORRECTION
        
        current_match = matching_result.matches[current_match_index]
        
        try:
            if user_input == "0":
                # Skip this ingredient
                await update.message.reply_text(f"✅ Пропущен ингредиент: {current_match.receipt_item_name}")
                await self._process_next_ingredient_match(update, context)
                
            elif user_input.startswith("search:"):
                # Search for ingredients
                query = user_input[7:].strip()
                if not query:
                    await update.message.reply_text("Введите поисковый запрос после 'search:'")
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
                        
                        await update.message.reply_text(
                            f"✅ Сопоставлено: {current_match.receipt_item_name} → {selected_suggestion['name']}"
                        )
                        await self._process_next_ingredient_match(update, context)
                        
                    else:
                        await update.message.reply_text(
                            f"Неверный номер. Введите число от 1 до {len(current_match.suggested_matches)} или 0 для пропуска."
                        )
                        return self.config.AWAITING_MANUAL_MATCH
                        
                except ValueError:
                    await update.message.reply_text(
                        "Неверный формат. Введите номер предложения, 0 для пропуска или 'search: запрос' для поиска."
                    )
                    return self.config.AWAITING_MANUAL_MATCH
                    
        except Exception as e:
            print(f"Ошибка при обработке ручного сопоставления: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")
            return self.config.AWAITING_MANUAL_MATCH
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_ingredient_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
        """Handle ingredient search"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await update.message.reply_text("Ошибка: данные сопоставления не найдены.")
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
                keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    progress_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
                # Save search results for selection
                context.user_data['search_results'] = filtered_results
            else:
                await update.message.reply_text(f"По запросу '{query}' не найдено подходящих вариантов (с вероятностью > 50%).")
        else:
            await update.message.reply_text(f"По запросу '{query}' ничего не найдено.")
        
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
        
        await update.message.reply_text(progress_text, parse_mode='Markdown')
    
    async def _show_final_ingredient_matching_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final ingredient matching result"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            await update.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return
        
        # Format final result
        final_text = self.ingredient_formatter.format_matching_table(matching_result)
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            final_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all receipt-related data from context"""
        keys_to_clear = [
            'receipt_data', 'original_data', 'line_to_edit', 'field_to_edit',
            'cached_final_report', 'table_message_id', 'edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id', 'ingredient_matching_result', 'current_match_index',
            'processing_message_id'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    async def show_final_report_with_edit_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons"""
        # Удаляем сообщение "Обрабатываю квитанцию" если оно есть
        processing_message_id = context.user_data.get('processing_message_id')
        if processing_message_id:
            try:
                if hasattr(update, 'message') and update.message:
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=processing_message_id
                    )
                elif hasattr(update, 'callback_query') and update.callback_query:
                    await context.bot.delete_message(
                        chat_id=update.callback_query.message.chat_id,
                        message_id=processing_message_id
                    )
            except Exception as e:
                print(f"Не удалось удалить сообщение об обработке: {e}")
            # Очищаем ID сообщения из контекста
            context.user_data.pop('processing_message_id', None)
        
        final_data: ReceiptData = context.user_data.get('receipt_data')
        
        if not final_data:
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text("Произошла ошибка, данные не найдены.")
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Произошла ошибка, данные не найдены.")
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
                        keyboard.append([InlineKeyboardButton(
                            f"Исправить строку {item.line_number}",
                            callback_data=f"edit_{item.line_number}"
                        )])
            
            # Add line management buttons
            keyboard.append([
                InlineKeyboardButton("➕ Добавить строку", callback_data="add_row"),
                InlineKeyboardButton("➖ Удалить строку", callback_data="delete_row")
            ])
            
            # Add total edit button
            keyboard.append([InlineKeyboardButton("💰 Редактировать Итого", callback_data="edit_total")])
            
            # Add reanalysis button
            keyboard.append([InlineKeyboardButton("🔄 Проанализировать заново", callback_data="reanalyze")])
            
            # Add ingredient matching button
            keyboard.append([InlineKeyboardButton("🔍 Сопоставить ингредиенты", callback_data="match_ingredients")])
            
            # Add general buttons
            keyboard.append([InlineKeyboardButton("🔢 Редактировать строку по номеру", callback_data="edit_line_number")])
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send report with buttons
            if hasattr(update, 'message') and update.message:
                message = await self._send_long_message_with_keyboard(update.message, final_report, reply_markup)
                # Save table message ID for subsequent editing
                if hasattr(message, 'message_id'):
                    context.user_data['table_message_id'] = message.message_id
            elif hasattr(update, 'callback_query') and update.callback_query:
                await self._send_long_message_with_keyboard_callback(update.callback_query.message, final_report, reply_markup)
        
        except Exception as e:
            print(f"Ошибка при формировании отчета: {e}")
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(f"Произошла ошибка при формировании отчета: {e}")
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(f"Произошла ошибка при формировании отчета: {e}")
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id_to_edit: int = None):
        """Send edit menu for specific line"""
        line_number = context.user_data.get('line_to_edit')
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number)
        
        if not item_to_edit:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: строка не найдена")
            elif hasattr(update, 'message') and update.message:
                await update.message.reply_text("Ошибка: строка не найдена")
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
                InlineKeyboardButton("❌ Отмена", callback_data="cancel")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Determine chat_id and message sending method
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
            reply_method = update.callback_query.message.reply_text
        elif hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
            reply_method = update.message.reply_text
        else:
            return
        
        if message_id_to_edit:
            # Edit existing message
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id_to_edit,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # Create new message
            message = await reply_method(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
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
