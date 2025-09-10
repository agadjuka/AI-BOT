"""
User input handling for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.receipt import ReceiptData
from handlers.base_message_handler import BaseMessageHandler
from handlers.google_sheets_input_handler import GoogleSheetsInputHandler
from utils.common_handlers import CommonHandlers
from config.locales.locale_manager import get_global_locale_manager


class InputHandler(BaseMessageHandler):
    """Handler for user text input processing"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.google_sheets_input_handler = GoogleSheetsInputHandler(config, analysis_service)
        self.common_handlers = CommonHandlers(config, analysis_service)
    
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
            print(f"DEBUG: Failed to delete user message: {e}")
        
        # Check for Google Sheets ingredient search
        if context.user_data.get('awaiting_google_sheets_ingredient_name'):
            return await self._handle_google_sheets_ingredient_search(update, context, user_input)
        
        # Check for Google Sheets search mode
        if context.user_data.get('google_sheets_search_mode'):
            print(f"DEBUG: Google Sheets search mode detected for input: '{user_input}'")
            return await self.google_sheets_input_handler._handle_google_sheets_search(update, context, user_input)
        
        if field_to_edit:
            # Edit specific field
            return await self._handle_field_edit(update, context, user_input, line_number, field_to_edit)
        else:
            # No field specified - show error
            error_message = self.locale_manager.get_text("errors.field_not_specified", context)
            await self.ui_manager.send_temp(
                update, context,
                error_message,
                duration=5
            )
            return self.config.AWAITING_FIELD_EDIT
    
    async def _handle_field_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                user_input: str, line_number: int, field_to_edit: str) -> int:
        """Handle field-specific editing"""
        try:
            # Clean up the input request message
            try:
                # Find and delete the message that asked for input
                if hasattr(update, 'message') and update.message:
                    # Delete the user's input message
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=update.message.message_id
                    )
                
                # Try to delete the input request message (the one with "Enter new value:")
                # This is usually the last message from the bot
                if context.user_data.get('last_bot_message_id'):
                    try:
                        await context.bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=context.user_data['last_bot_message_id']
                        )
                    except:
                        pass  # Message might already be deleted
            except Exception as e:
                print(f"DEBUG: Error cleaning up messages: {e}")
            
            data: ReceiptData = context.user_data['receipt_data']
            item_to_edit = data.get_item(line_number)
            
            if not item_to_edit:
                error_message = self.locale_manager.get_text("errors.line_not_found", context)
                await update.message.reply_text(error_message)
                return self.config.AWAITING_FIELD_EDIT
            
            # Process input based on field type
            if field_to_edit == 'name':
                field_name = self.locale_manager.get_text("analysis.field_display_names.name", context)
                is_valid, message = self.validator.validate_text_input(user_input, field_name)
                if not is_valid:
                    error_message = self.locale_manager.get_text("errors.field_edit_error", context, error=message)
                    await self.ui_manager.send_temp(
                        update, context, error_message, duration=5
                    )
                    return self.config.AWAITING_FIELD_EDIT
                item_to_edit.name = user_input
                
            elif field_to_edit in ['quantity', 'price', 'total']:
                # Parse number, considering possible separators (including decimal fractions)
                numeric_value = self.text_parser.parse_user_input_number(user_input)
                if numeric_value < 0:
                    error_message = self.locale_manager.get_text("validation.negative_value", context)
                    await self.ui_manager.send_temp(
                        update, context, error_message, duration=5
                    )
                    return self.config.AWAITING_FIELD_EDIT
                
                setattr(item_to_edit, field_to_edit, numeric_value)
                
                # If changed quantity or price, recalculate sum automatically
                if field_to_edit in ['quantity', 'price']:
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
                'name': self.locale_manager.get_text('analysis.field_display_names.name', context),
                'quantity': self.locale_manager.get_text('analysis.field_display_names.quantity', context),
                'price': self.locale_manager.get_text('analysis.field_display_names.price', context),
                'total': self.locale_manager.get_text('analysis.field_display_names.total', context)
            }
            
            new_value = getattr(item_to_edit, field_to_edit, '')
            if field_to_edit in ['quantity', 'price', 'total'] and isinstance(new_value, (int, float)):
                new_value = self.number_formatter.format_number_with_spaces(new_value)
            
            # Update the existing edit menu message with new data
            edit_menu_message_id = context.user_data.get('edit_menu_message_id')
            print(f"DEBUG: edit_menu_message_id = {edit_menu_message_id}")
            if edit_menu_message_id:
                # Edit existing message instead of creating new one
                await self._send_edit_menu(update, context, edit_menu_message_id)
            else:
                print("DEBUG: No edit_menu_message_id found, creating new message")
                # Create new message if no ID found
                await self._send_edit_menu(update, context)
            
            return self.config.AWAITING_FIELD_EDIT
            
        except Exception as e:
            print(f"DEBUG: Error editing field: {e}")
            # Update the existing edit menu message even on error
            edit_menu_message_id = context.user_data.get('edit_menu_message_id')
            if edit_menu_message_id:
                # Edit existing message instead of creating new one
                await self._send_edit_menu(update, context, edit_menu_message_id)
            else:
                # Create new message if no ID found
                await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
    
    
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
                    update, context, f"{message}\n\n{self.locale_manager.get_text('validation.try_again', context)}", duration=10
                )
                return self.config.AWAITING_LINE_NUMBER
            
            # Delete user message
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"DEBUG: Failed to delete user message: {e}")
            
            
            # Set line number for editing
            context.user_data['line_to_edit'] = line_number
            
            # Show edit menu for line
            await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
            
        except ValueError:
            error_message = self.locale_manager.get_text("validation.invalid_line_format", context)
            await self.ui_manager.send_temp(
                update, context, error_message, duration=10
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
                    update, context, f"{message}\n\n{self.locale_manager.get_text('validation.try_again', context)}", duration=10
                )
                return self.config.AWAITING_DELETE_LINE_NUMBER
            
            # Delete user message
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"DEBUG: Failed to delete user message: {e}")
            
            
            # Remove line from data
            success = data.remove_item(line_number)
            if success:
                # Update original_data to reflect the changes
                if context.user_data.get('original_data'):
                    context.user_data['original_data'].remove_item(line_number)
                
                # Update ingredient matching after line deletion
                await self._update_ingredient_matching_after_deletion(update, context, data, line_number)
                
                # Show success message
                success_message = self.locale_manager.get_text("status.line_deleted", context, line_number=line_number)
                await self.ui_manager.send_temp(
                    update, context, success_message, duration=2
                )
                
                # Return to updated report
                await self.show_final_report_with_edit_button(update, context)
            
            return self.config.AWAITING_CORRECTION
            
        except ValueError:
            error_message = self.locale_manager.get_text("validation.invalid_line_format", context)
            await self.ui_manager.send_temp(
                update, context, error_message, duration=10
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
            print(f"DEBUG: Failed to delete user message: {e}")
        
        
        try:
            # Parse new total sum
            new_total = self.text_parser.parse_user_input_number(user_input)
            
            if new_total < 0:
                error_message = self.locale_manager.get_text("validation.negative_total", context)
                await self.ui_manager.send_temp(
                    update, context, error_message, duration=5
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
            success_message = self.locale_manager.get_text("status.total_updated", context, total=formatted_total)
            await self.ui_manager.send_temp(
                update, context, success_message, duration=2
            )
            
            # Return to updated report
            await self.show_final_report_with_edit_button(update, context)
            
            return self.config.AWAITING_CORRECTION
            
        except Exception as e:
            print(f"DEBUG: Error updating total amount: {e}")
            error_message = self.locale_manager.get_text("errors.total_update_retry", context)
            await self.ui_manager.send_temp(
                update, context, error_message, duration=5
            )
            return self.config.AWAITING_TOTAL_EDIT
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id_to_edit: int = None):
        """Send edit menu for specific line - this becomes the single working menu"""
        line_number = context.user_data.get('line_to_edit')
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number)
        
        if not item_to_edit:
            error_message = self.locale_manager.get_text("errors.line_not_found", context)
            await self.ui_manager.send_temp(
                update, context, error_message, duration=5
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
        
        editing_line_text = self.locale_manager.get_text("analysis.editing_line", context, line_number=line_number, status_icon=status_icon)
        field_name_text = self.locale_manager.get_text("analysis.field_name", context, name=name)
        field_quantity_text = self.locale_manager.get_text("analysis.field_quantity", context, quantity=quantity)
        field_price_text = self.locale_manager.get_text("analysis.field_price", context, price=price)
        field_total_text = self.locale_manager.get_text("analysis.field_total", context, total=total)
        choose_field_text = self.locale_manager.get_text("analysis.choose_field", context)
        auto_calculated_text = self.locale_manager.get_text("analysis.auto_calculated", context)
        
        text = editing_line_text
        text += field_name_text
        text += field_quantity_text
        text += field_price_text
        
        # Show sum with note about whether it was automatically calculated
        if is_auto_calculated:
            text += f"💵 **{self.locale_manager.get_text('analysis.field_display_names.total', context)}:** {total} {auto_calculated_text}\n\n"
        else:
            text += field_total_text
        
        text += choose_field_text
        
        keyboard = [
            [
                InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_name", context), callback_data=f"field_{line_number}_name"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_quantity", context), callback_data=f"field_{line_number}_quantity"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_price", context), callback_data=f"field_{line_number}_price")
            ],
            [
                InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_total_field", context), callback_data=f"field_{line_number}_total"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.apply_changes", context), callback_data=f"apply_{line_number}"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.back_to_receipt", context), callback_data="back_to_receipt")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if message_id_to_edit:
            # Edit existing working menu message
            success = await self.ui_manager.edit_menu(
                update, context, message_id_to_edit, text, reply_markup, 'Markdown'
            )
            if not success:
                # If couldn't edit, send new message (replaces working menu)
                message = await self.ui_manager.send_menu(
                    update, context, text, reply_markup, 'Markdown'
                )
        else:
            # Create new working menu message
            message = await self.ui_manager.send_menu(
                update, context, text, reply_markup, 'Markdown'
            )
    
    async def show_final_report_with_edit_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons - this is the root menu"""
        # This method will be implemented in the main handler
        # For now, delegate to photo handler
        from handlers.photo_handler import PhotoHandler
        photo_handler = PhotoHandler(self.config, self.analysis_service)
        return await photo_handler.show_final_report_with_edit_button(update, context)
    
    async def _update_ingredient_matching_after_data_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                           receipt_data: ReceiptData, change_type: str = "general") -> None:
        """Update ingredient matching after any data change"""
        # This method will be implemented in the main handler
        # For now, just log the change
        print(f"DEBUG: Ingredient matching update needed after {change_type}")
        pass
    
    async def _update_ingredient_matching_after_deletion(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       receipt_data: ReceiptData, deleted_line_number: int) -> None:
        """Update ingredient matching after line deletion"""
        # This method will be implemented in the main handler
        # For now, just log the change
        print(f"DEBUG: Ingredient matching update needed after deletion of line {deleted_line_number}")
        pass
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name if too long"""
        return self.common_handlers.truncate_name(name, max_length)
