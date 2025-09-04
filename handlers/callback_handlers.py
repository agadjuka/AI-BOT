"""
Callback handlers for Telegram bot
"""
import asyncio
import json
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from models.receipt import ReceiptData, ReceiptItem
from services.ai_service import ReceiptAnalysisService
from utils.formatters import ReceiptFormatter, NumberFormatter, TextParser
from utils.receipt_processor import ReceiptProcessor
from validators.receipt_validator import ReceiptValidator


class CallbackHandlers:
    """Handlers for Telegram callback queries"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.formatter = ReceiptFormatter()
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
        self.processor = ReceiptProcessor()
        self.validator = ReceiptValidator()
    
    async def handle_correction_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle correction choice callback"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        if action == "finish":
            # "finish" button no longer needed as report is already shown
            await query.answer("Отчет уже готов!")
            return self.config.AWAITING_CORRECTION
        
        if action == "add_row":
            # Add new row
            await self._add_new_row(update, context)
            return self.config.AWAITING_FIELD_EDIT
        
        if action == "delete_row":
            # Request line number for deletion
            instruction_message = await query.message.reply_text(
                "Введите номер строки для удаления:\n\n"
                "Например: `3` (для удаления строки 3)",
                parse_mode='Markdown'
            )
            # Save instruction message ID for subsequent deletion
            context.user_data['delete_line_number_instruction_message_id'] = instruction_message.message_id
            return self.config.AWAITING_DELETE_LINE_NUMBER
        
        if action == "edit_total":
            # Show total edit menu
            await self._show_total_edit_menu(update, context)
            return self.config.AWAITING_CORRECTION
        
        if action == "auto_calculate_total":
            # Automatically calculate total
            await self._auto_calculate_total(update, context)
            return self.config.AWAITING_CORRECTION
        
        if action == "manual_edit_total":
            # Request new total sum manually
            current_total = context.user_data.get('receipt_data', {}).grand_total_text
            formatted_total = self.number_formatter.format_number_with_spaces(self.text_parser.parse_number_from_text(current_total))
            
            instruction_message = await query.message.reply_text(
                f"Текущая итоговая сумма: **{formatted_total}**\n\n"
                "Введите новую итоговую сумму:",
                parse_mode='Markdown'
            )
            # Save instruction message ID for subsequent deletion
            context.user_data['total_edit_instruction_message_id'] = instruction_message.message_id
            return self.config.AWAITING_TOTAL_EDIT
        
        if action == "edit_line_number":
            # Request line number for editing
            instruction_message = await query.message.reply_text(
                "Введите номер строки для редактирования:\n\n"
                "Например: `3` (для редактирования строки 3)",
                parse_mode='Markdown'
            )
            # Save instruction message ID for subsequent deletion
            context.user_data['line_number_instruction_message_id'] = instruction_message.message_id
            return self.config.AWAITING_LINE_NUMBER
        
        if action == "reanalyze":
            # Delete old report
            await query.answer("🔄 Анализирую фото заново...")
            
            # Delete report message
            try:
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение с отчетом: {e}")
            
            # Clear all old data
            self._clear_receipt_data(context)
            
            # Send photo to Gemini again
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
                
                # Show new report
                await self._show_final_report_with_edit_button_callback(update, context)
                return self.config.AWAITING_CORRECTION
                
            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
                print(f"Ошибка парсинга JSON или структуры данных от Gemini: {e}")
                await query.message.reply_text("Не удалось распознать структуру чека. Попробуйте сделать фото более четким.")
                return self.config.AWAITING_CORRECTION
        
        if action == "cancel":
            # Check if we're in edit menu
            if context.user_data.get('line_to_edit'):
                # Delete edit menu message
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id
                    )
                except Exception as e:
                    print(f"Не удалось удалить сообщение меню редактирования: {e}")
                
                # Return to updated report
                await self._show_final_report_with_edit_button_callback(update, context)
                return self.config.AWAITING_CORRECTION
            else:
                # Regular cancellation
                await self._cancel(update, context)
                return self.config.AWAITING_CORRECTION
        
        if action.startswith("edit_"):
            line_number_to_edit = int(action.split('_')[1])
            context.user_data['line_to_edit'] = line_number_to_edit
            await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
        
        if action.startswith("field_"):
            # Handle field selection for editing
            parts = action.split('_')
            line_number = int(parts[1])
            field_name = parts[2]
            
            context.user_data['line_to_edit'] = line_number
            context.user_data['field_to_edit'] = field_name
            
            data: ReceiptData = context.user_data['receipt_data']
            item_to_edit = data.get_item(line_number)
            
            field_labels = {
                'name': 'название товара',
                'quantity': 'количество',
                'price': 'цену за единицу',
                'total': 'сумму'
            }
            
            current_value = getattr(item_to_edit, field_name, '')
            if field_name in ['quantity', 'price', 'total'] and isinstance(current_value, (int, float)):
                current_value = self.number_formatter.format_number_with_spaces(current_value)
            
            instruction_message = await query.message.reply_text(
                f"Редактируете строку {line_number}\n"
                f"Текущее {field_labels[field_name]}: **{current_value}**\n\n"
                f"Введите новое {field_labels[field_name]}:",
                parse_mode='Markdown'
            )
            
            context.user_data['instruction_message_id'] = instruction_message.message_id
            return self.config.AWAITING_FIELD_EDIT
        
        if action.startswith("apply_"):
            line_number = int(action.split('_')[1])
            
            # Automatically update item status before applying
            data: ReceiptData = context.user_data.get('receipt_data', {})
            item_to_apply = data.get_item(line_number)
            if item_to_apply:
                item_to_apply = self.processor.auto_update_item_status(item_to_apply)
            
            # Delete edit menu message
            try:
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение меню редактирования: {e}")
            
            # Show message about applying changes
            status_message = await query.message.reply_text("✅ Изменения применены! Обновляю таблицу...")
            
            # Apply changes and return to updated report
            await self._show_final_report_with_edit_button_callback(update, context)
            
            # Delete status message
            try:
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=status_message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить сообщение о применении изменений: {e}")
            
            return self.config.AWAITING_CORRECTION
        
        # Handle old format for compatibility
        line_number_to_edit = int(action.split('_')[1])
        context.user_data['line_to_edit'] = line_number_to_edit
        
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number_to_edit)
        
        instruction_message = await query.message.reply_text(
            f"Вы исправляете строку: **{item_to_edit.name}**.\n\n"
            "Введите правильные данные в формате:\n"
            "`Название, Количество, Цена за единицу, Сумма`\n\n"
            "Пример: `Udang Kupas, 4, 150000, 600000`",
            parse_mode='Markdown'
        )
        
        # Save instruction message ID for subsequent deletion
        context.user_data['instruction_message_id'] = instruction_message.message_id
        
        return self.config.AWAITING_INPUT
    
    async def _add_new_row(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add new row to table"""
        data: ReceiptData = context.user_data.get('receipt_data')
        
        # Find maximum line number
        max_line_number = data.get_max_line_number()
        new_line_number = max_line_number + 1
        
        # Create new row with empty data
        new_item = ReceiptItem(
            line_number=new_line_number,
            name='Новый товар',
            quantity=1.0,
            price=0.0,
            total=0.0,
            status='needs_review',
            auto_calculated=False
        )
        
        # Add new row to data
        data.add_item(new_item)
        
        # Set new row for editing
        context.user_data['line_to_edit'] = new_line_number
        
        # Show edit menu for new row
        await self._send_edit_menu(update, context)
    
    async def _show_total_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show total edit menu"""
        data: ReceiptData = context.user_data.get('receipt_data', {})
        current_total = data.grand_total_text
        formatted_total = self.number_formatter.format_number_with_spaces(self.text_parser.parse_number_from_text(current_total))
        
        # Calculate automatic sum
        calculated_total = self.formatter.calculate_total_sum(data)
        formatted_calculated_total = self.number_formatter.format_number_with_spaces(calculated_total)
        
        text = f"**Редактирование итого:**\n\n"
        text += f"💰 **Текущая итоговая сумма:** {formatted_total}\n"
        text += f"🧮 **Автоматически рассчитанная сумма:** {formatted_calculated_total}\n\n"
        text += "Выберите действие:"
        
        keyboard = [
            [
                InlineKeyboardButton("🧮 Рассчитать автоматически", callback_data="auto_calculate_total"),
                InlineKeyboardButton("✏️ Ввести вручную", callback_data="manual_edit_total")
            ],
            [
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
        
        message = await reply_method(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Save message ID for subsequent deletion
        context.user_data['total_edit_menu_message_id'] = message.message_id
    
    async def _auto_calculate_total(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Automatically calculate total based on all line sums"""
        data: ReceiptData = context.user_data.get('receipt_data', {})
        
        # Calculate total sum of all positions
        calculated_total = self.formatter.calculate_total_sum(data)
        
        # Update total sum in data
        data.grand_total_text = str(int(calculated_total)) if calculated_total == int(calculated_total) else str(calculated_total)
        
        # Delete total edit menu message
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=context.user_data.get('total_edit_menu_message_id')
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение с меню редактирования итого: {e}")
        
        # Show success message
        formatted_total = self.number_formatter.format_number_with_spaces(calculated_total)
        success_message = await update.callback_query.message.reply_text(
            f"✅ Итого автоматически рассчитано: **{formatted_total}**", 
            parse_mode='Markdown'
        )
        
        # Return to updated report
        await self._show_final_report_with_edit_button_callback(update, context)
        
        # Delete success message
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=success_message.message_id
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение об успехе: {e}")
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id_to_edit: int = None):
        """Send edit menu for specific line"""
        line_number = context.user_data.get('line_to_edit')
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number)
        
        if not item_to_edit:
            await update.callback_query.message.reply_text("Ошибка: строка не найдена")
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
    
    async def _show_final_report_with_edit_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons (for callback query)"""
        final_data: ReceiptData = context.user_data.get('receipt_data')
        
        if not final_data:
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
                    
                    if quantity > 0 and price > 0 and total > 0:
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
            
            # Add general buttons
            keyboard.append([InlineKeyboardButton("🔢 Редактировать строку по номеру", callback_data="edit_line_number")])
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Check if there's saved table message
            table_message_id = context.user_data.get('table_message_id')
            
            if table_message_id:
                try:
                    # Edit existing table message
                    await context.bot.edit_message_text(
                        chat_id=update.callback_query.message.chat_id,
                        message_id=table_message_id,
                        text=final_report,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Не удалось отредактировать сообщение с таблицей: {e}")
                    # If couldn't edit, send new message
                    await self._send_long_message_with_keyboard_callback(update.callback_query.message, final_report, reply_markup)
            else:
                # If no saved ID, send new message
                await self._send_long_message_with_keyboard_callback(update.callback_query.message, final_report, reply_markup)
        
        except Exception as e:
            print(f"Ошибка при формировании отчета: {e}")
            await update.callback_query.message.reply_text(f"Произошла ошибка при формировании отчета: {e}")
    
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
    
    async def _cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancellation"""
        # Handle both regular message and callback query
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text("Операция отменена.")
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.edit_text("Операция отменена.")
        
        context.user_data.clear()
        return self.config.AWAITING_CORRECTION
    
    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all receipt-related data from context"""
        keys_to_clear = [
            'receipt_data', 'original_data', 'line_to_edit', 'field_to_edit',
            'cached_final_report', 'table_message_id', 'edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
