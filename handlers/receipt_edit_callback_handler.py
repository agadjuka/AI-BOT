"""
Receipt edit callback handler for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.receipt import ReceiptData, ReceiptItem


class ReceiptEditCallbackHandler(BaseCallbackHandler):
    """Handler for receipt editing callbacks"""
    
    async def _add_new_row(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add new row to receipt"""
        query = update.callback_query
        await query.answer()
        
        data: ReceiptData = context.user_data.get('receipt_data')
        if not data:
            await query.edit_message_text("❌ Данные чека не найдены")
            return
        
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
        
        # Update original_data to reflect the changes
        if context.user_data.get('original_data'):
            context.user_data['original_data'].add_item(new_item)
        
        # Automatically match ingredient for the new item
        await self._auto_match_ingredient_for_new_item(update, context, new_item, data)
        
        # Set new row for editing
        context.user_data['line_to_edit'] = new_line_number
        
        # Show edit menu for new row
        await self._send_edit_menu(update, context)
    
    async def _show_total_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show total edit menu"""
        query = update.callback_query
        await query.answer()
        
        data: ReceiptData = context.user_data.get('receipt_data', {})
        if not data:
            await query.edit_message_text("❌ Данные чека не найдены")
            return
        
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
        
        # Send message and save message ID
        message = await reply_method(text, reply_markup=reply_markup, parse_mode='Markdown')
        context.user_data['total_edit_menu_message_id'] = message.message_id
    
    async def _auto_calculate_total(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Automatically calculate total based on all line sums"""
        query = update.callback_query
        await query.answer()
        
        data: ReceiptData = context.user_data.get('receipt_data', {})
        if not data:
            await query.edit_message_text("❌ Данные чека не найдены")
            return
        
        # Calculate total sum of all positions
        calculated_total = self.formatter.calculate_total_sum(data)
        
        # Update total sum in data
        data.grand_total_text = str(int(calculated_total)) if calculated_total == int(calculated_total) else str(calculated_total)
        
        # Update original_data to reflect the changes
        if context.user_data.get('original_data'):
            context.user_data['original_data'].grand_total_text = data.grand_total_text
        
        # Update ingredient matching after total change
        await self._update_ingredient_matching_after_data_change(update, context, data, "total_change")
        
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
        await self.ui_manager.send_temp(
            update, context, f"✅ Итого автоматически рассчитано: **{formatted_total}**", duration=2
        )
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id_to_edit: int = None):
        """Send edit menu for specific line"""
        line_number = context.user_data.get('line_to_edit')
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number)
        
        if not item_to_edit:
            if hasattr(update, 'callback_query') and update.callback_query:
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
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Determine chat_id and message sending method
        if hasattr(update, 'callback_query') and update.callback_query:
            # For callback queries, send new message to preserve receipt menu
            try:
                await update.callback_query.message.reply_text(
                    text, reply_markup=reply_markup, parse_mode='Markdown'
                )
            except Exception as e:
                print(f"DEBUG: Error editing message: {e}")
                # If couldn't edit, send new message
                message = await update.callback_query.message.reply_text(
                    text, reply_markup=reply_markup, parse_mode='Markdown'
                )
                context.user_data['edit_menu_message_id'] = message.message_id
        elif hasattr(update, 'message') and update.message:
            # For regular messages, create new message
            message = await self.ui_manager.send_menu(
                update, context, text, reply_markup, 'Markdown'
            )
            context.user_data['edit_menu_message_id'] = message.message_id
        else:
            return
    
    async def _show_final_report_with_edit_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons (for callback query)"""
        final_data: ReceiptData = context.user_data.get('receipt_data')
        
        if not final_data:
            if hasattr(update, 'callback_query') and update.callback_query:
                await self.ui_manager.send_temp(
                    update, context,
                    "❌ **Данные чека не найдены**\n\n"
                    "Попробуйте загрузить чек заново.",
                    duration=5
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
                            callback_data=f"edit_item_{item.line_number}"
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
            
            # Use UI manager to send/update the single working menu
            working_menu_id = self.ui_manager.get_working_menu_id(context)
            
            if working_menu_id:
                # Try to edit existing working menu message
                success = await self.ui_manager.edit_menu(
                    update, context, working_menu_id, final_report, reply_markup
                )
                if not success:
                    # If couldn't edit, send new message (replaces working menu)
                    message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
            else:
                # If no working menu, send new message (becomes working menu)
                message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
        
        except Exception as e:
            print(f"Ошибка при формировании отчета: {e}")
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(f"Произошла ошибка при формировании отчета: {e}")
    
