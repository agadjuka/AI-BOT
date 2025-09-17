"""
Receipt edit callback handler for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.receipt import ReceiptData, ReceiptItem
from config.locales.locale_manager import get_global_locale_manager
from handlers.input_handler import InputHandler


class ReceiptEditCallbackHandler(BaseCallbackHandler):
    """Handler for receipt editing callbacks"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.input_handler = InputHandler(config, analysis_service)
    
    async def _add_new_row(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add new row to receipt"""
        query = update.callback_query
        await query.answer()
        
        data: ReceiptData = context.user_data.get('receipt_data')
        if not data:
            await query.edit_message_text(self.locale_manager.get_text("errors.receipt_data_not_found", context))
            return
        
        # Find maximum line number
        max_line_number = data.get_max_line_number()
        new_line_number = max_line_number + 1
        
        # Create new row with empty data
        new_item = ReceiptItem(
            line_number=new_line_number,
            name=self.locale_manager.get_text("analysis.new_item_name", context),
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
        
        # Delete the receipt message before showing edit menu
        try:
            await query.delete_message()
        except Exception as e:
            print(f"DEBUG: Error deleting receipt message: {e}")
        
        # Show edit menu for new row
        await self.input_handler._send_edit_menu(update, context)
    
    async def _show_total_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show total edit menu"""
        query = update.callback_query
        await query.answer()
        
        data: ReceiptData = context.user_data.get('receipt_data', {})
        if not data:
            await query.edit_message_text(self.locale_manager.get_text("errors.receipt_data_not_found", context))
            return
        
        current_total = data.grand_total_text
        formatted_total = self.number_formatter.format_number_with_spaces(self.text_parser.parse_number_from_text(current_total))
        
        # Calculate automatic sum
        calculated_total = self.formatter.calculate_total_sum(data)
        formatted_calculated_total = self.number_formatter.format_number_with_spaces(calculated_total)
        
        editing_total_text = self.locale_manager.get_text("analysis.editing_total", context)
        current_total_text = self.locale_manager.get_text("analysis.current_total", context, total=formatted_total)
        calculated_total_text = self.locale_manager.get_text("analysis.calculated_total", context, calculated_total=formatted_calculated_total)
        choose_action_text = self.locale_manager.get_text("analysis.choose_action", context)
        
        text = editing_total_text
        text += current_total_text
        text += calculated_total_text
        text += choose_action_text
        
        keyboard = [
            [
                InlineKeyboardButton(self.locale_manager.get_text("buttons.auto_calculate_total", context), callback_data="auto_calculate_total"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.manual_edit_total", context), callback_data="manual_edit_total")
            ],
            [
                InlineKeyboardButton(self.locale_manager.get_text("buttons.cancel", context), callback_data="cancel")
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
            await query.edit_message_text(self.locale_manager.get_text("errors.receipt_data_not_found", context))
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
            print(f"Failed to delete total edit menu message: {e}")
        
        # Show success message
        formatted_total = self.number_formatter.format_number_with_spaces(calculated_total)
        await self.ui_manager.send_temp(
            update, context, self.locale_manager.get_text("status.total_auto_calculated", context, total=formatted_total), duration=2
        )
    
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delegate to input handler"""
        await self.input_handler._send_edit_menu(update, context)
    
    async def _show_final_report_with_edit_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons (for callback query)"""
        final_data: ReceiptData = context.user_data.get('receipt_data')
        
        if not final_data:
            if hasattr(update, 'callback_query') and update.callback_query:
                await self.ui_manager.send_temp(
                    update, context,
                    self.locale_manager.get_text("errors.receipt_data_not_found", context) + "\n\n" +
                    "Try uploading the receipt again.",
                    duration=5
                )
            return

        try:
            # Automatically update statuses of all elements
            final_data = self.processor.auto_update_all_statuses(final_data)
            context.user_data['receipt_data'] = final_data
            
            # Check if there are errors
            has_errors = not self.processor.check_all_items_confirmed(final_data)
            
            # Create aligned table programmatically based on user's display mode
            from services.user_service import get_user_service
            user_service = get_user_service()
            user_id = update.effective_user.id
            display_mode = await user_service.get_user_display_mode(user_id)
            
            if display_mode == "desktop":
                aligned_table = self.formatter.format_aligned_table_desktop(final_data, context)
            else:
                aligned_table = self.formatter.format_aligned_table_mobile(final_data, context)
            
            # Calculate total sum
            calculated_total = self.formatter.calculate_total_sum(final_data)
            receipt_total = self.text_parser.parse_number_from_text(final_data.grand_total_text)
            
            # Form final report
            final_report = ""
            
            # Add red marker if there are errors
            if has_errors:
                final_report += self.locale_manager.get_text("analysis.errors_found", context)
            
            final_report += f"```\n{aligned_table}\n```\n\n"
            
            if abs(calculated_total - receipt_total) < 0.01:
                final_report += self.locale_manager.get_text("analysis.total_matches", context)
            else:
                difference = abs(calculated_total - receipt_total)
                final_report += self.locale_manager.get_text("analysis.total_mismatch", context, difference=self.number_formatter.format_number_with_spaces(difference))
            
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
                    is_unreadable = item_name == "???" or item_name == "**unrecognized**"
                    
                    # If there are calculation errors, unreadable data or status not confirmed
                    if status != 'confirmed' or has_calculation_error or is_unreadable:
                        fix_buttons.append(InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.fix_line", context, line_number=item.line_number),
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
                InlineKeyboardButton(self.locale_manager.get_text("buttons.add_row", context), callback_data="add_row"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.delete_row", context), callback_data="delete_row")
            ])
            
            # Add edit line by number button under add/delete buttons
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_line_number", context), callback_data="edit_line_number")])
            
            # Add total edit and reanalysis buttons in one row
            keyboard.append([
                InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_total", context), callback_data="edit_total"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.reanalyze", context), callback_data="reanalyze")
            ])
            
            # Add Google Sheets upload button
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("buttons.upload_to_google_sheets", context), callback_data="upload_to_google_sheets")])
            
            # Add file generation button
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("buttons.generate_supply_file", context), callback_data="generate_supply_file")])
            
            # Add back button (required in every menu)
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("buttons.back_to_receipt", context), callback_data="back_to_receipt")])
            
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
            print(f"Error forming report: {e}")
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(self.locale_manager.get_text("errors.report_formation_error", context) + f": {e}")
    
