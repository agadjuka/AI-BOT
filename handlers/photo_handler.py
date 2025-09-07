"""
Photo handling for Telegram bot
"""
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.receipt import ReceiptData
from handlers.base_message_handler import BaseMessageHandler


class PhotoHandler(BaseMessageHandler):
    """Handler for photo upload and processing"""
    
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
        """Show final report with edit buttons - this is the root menu"""
        # Clean up all messages except anchor before showing final report
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
            
            # Add back button (required in every menu)
            keyboard.append([InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send report with buttons using UI manager (this becomes the single working menu)
            message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
            # Save table message ID for subsequent editing
            context.user_data['table_message_id'] = message.message_id
        
        except Exception as e:
            print(f"Ошибка при формировании отчета: {e}")
            await self.ui_manager.send_temp(
                update, context, f"Произошла ошибка при формировании отчета: {e}", duration=5
            )
