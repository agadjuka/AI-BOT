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
            # Delete the user's input message first
            try:
                if hasattr(update, 'message') and update.message:
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=update.message.message_id
                    )
            except Exception as e:
                print(f"DEBUG: Error deleting user input message: {e}")
            
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
                    # Delete the input request message and cleanup messages
                    try:
                        # Delete all messages from messages_to_cleanup
                        messages_to_cleanup = context.user_data.get('messages_to_cleanup', [])
                        for message_id in messages_to_cleanup:
                            try:
                                await context.bot.delete_message(
                                    chat_id=update.message.chat_id,
                                    message_id=message_id
                                )
                            except:
                                pass
                        context.user_data['messages_to_cleanup'] = []
                        
                        # Delete the input request message
                        input_request_message_id = context.user_data.get('input_request_message_id')
                        if input_request_message_id:
                            try:
                                await context.bot.delete_message(
                                    chat_id=update.message.chat_id,
                                    message_id=input_request_message_id
                                )
                                context.user_data['input_request_message_id'] = None
                            except:
                                pass
                    except:
                        pass
                    
                    error_message = self.locale_manager.get_text("errors.field_edit_error", context, error=message)
                    await self.ui_manager.send_temp(
                        update, context, error_message, duration=5
                    )
                    # Show edit menu again after error
                    edit_menu_message_id = context.user_data.get('edit_menu_message_id')
                    if edit_menu_message_id:
                        await self._send_edit_menu(update, context, edit_menu_message_id)
                    return self.config.AWAITING_FIELD_EDIT
                item_to_edit.name = user_input
                
            elif field_to_edit in ['quantity', 'price', 'total']:
                # Parse number, considering possible separators (including decimal fractions)
                numeric_value = self.text_parser.parse_user_input_number(user_input)
                if numeric_value < 0:
                    # Delete the input request message and cleanup messages
                    try:
                        # Delete all messages from messages_to_cleanup
                        messages_to_cleanup = context.user_data.get('messages_to_cleanup', [])
                        for message_id in messages_to_cleanup:
                            try:
                                await context.bot.delete_message(
                                    chat_id=update.message.chat_id,
                                    message_id=message_id
                                )
                            except:
                                pass
                        context.user_data['messages_to_cleanup'] = []
                        
                        # Delete the input request message
                        input_request_message_id = context.user_data.get('input_request_message_id')
                        if input_request_message_id:
                            try:
                                await context.bot.delete_message(
                                    chat_id=update.message.chat_id,
                                    message_id=input_request_message_id
                                )
                                context.user_data['input_request_message_id'] = None
                            except:
                                pass
                    except:
                        pass
                    
                    error_message = self.locale_manager.get_text("validation.negative_value", context)
                    await self.ui_manager.send_temp(
                        update, context, error_message, duration=5
                    )
                    # Show edit menu again after error
                    edit_menu_message_id = context.user_data.get('edit_menu_message_id')
                    if edit_menu_message_id:
                        await self._send_edit_menu(update, context, edit_menu_message_id)
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
            
            # Clean up the input request messages after successful update
            try:
                # Delete all messages from messages_to_cleanup (including "Editing quantity for line" messages)
                messages_to_cleanup = context.user_data.get('messages_to_cleanup', [])
                print(f"DEBUG: Cleaning up {len(messages_to_cleanup)} messages after successful update: {messages_to_cleanup}")
                for message_id in messages_to_cleanup:
                    try:
                        await context.bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=message_id
                        )
                        print(f"DEBUG: Successfully deleted message {message_id}")
                    except Exception as e:
                        print(f"DEBUG: Failed to delete message {message_id}: {e}")
                
                # Clear the cleanup list after deletion
                context.user_data['messages_to_cleanup'] = []
                
                # Also try to delete the input request message
                input_request_message_id = context.user_data.get('input_request_message_id')
                if input_request_message_id:
                    try:
                        await context.bot.delete_message(
                            chat_id=update.message.chat_id,
                            message_id=input_request_message_id
                        )
                        print(f"DEBUG: Successfully deleted input request message {input_request_message_id}")
                        # Clear the stored message ID
                        context.user_data['input_request_message_id'] = None
                    except Exception as e:
                        print(f"DEBUG: Failed to delete input request message {input_request_message_id}: {e}")
                
            except Exception as e:
                print(f"DEBUG: Error cleaning up messages after update: {e}")
            
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
    
    async def handle_column_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle column input for mapping editor"""
        user_input = update.message.text.strip().upper()
        
        # Store the message ID of the request message to delete it later
        request_message_id = context.user_data.get('mapping_request_message_id')
        
        # Delete user message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"DEBUG: Failed to delete user message: {e}")
        
        # Delete request message if it exists
        if request_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=request_message_id
                )
                context.user_data.pop('mapping_request_message_id', None)
            except Exception as e:
                print(f"DEBUG: Failed to delete request message: {e}")
        
        # Validate input
        if not self._is_valid_column_input(user_input):
            error_message = self.locale_manager.get_text("add_sheet.mapping_editor.errors.invalid_column", context, update=update)
            await self.ui_manager.send_temp(
                update, context, error_message, duration=5
            )
            return self.config.AWAITING_COLUMN_INPUT
        
        # Get field to edit and current mapping
        field_to_edit = context.user_data.get('field_to_edit')
        column_mapping = context.user_data.get('column_mapping', {})
        
        if not field_to_edit:
            error_message = self.locale_manager.get_text("add_sheet.mapping_editor.errors.no_field_selected", context, update=update)
            await self.ui_manager.send_temp(
                update, context, error_message, duration=5
            )
            return self.config.EDIT_MAPPING
        
        # Update mapping
        if user_input == '-':
            # Remove field from mapping
            column_mapping.pop(field_to_edit, None)
        else:
            # Check if column is already used by another field
            for existing_field, existing_column in column_mapping.items():
                if existing_field != field_to_edit and existing_column == user_input:
                    # Clear the old field's mapping
                    column_mapping.pop(existing_field, None)
            
            # Set new column for current field
            column_mapping[field_to_edit] = user_input
        
        # Save updated mapping
        context.user_data['column_mapping'] = column_mapping
        
        # Clear field_to_edit
        context.user_data.pop('field_to_edit', None)
        
        # Return to mapping editor (this will edit the original message)
        return await self._show_mapping_editor(update, context)
    
    
    def _is_valid_column_input(self, user_input: str) -> bool:
        """Validate column input (A-Z, AA-ZZ, etc. or -)"""
        if user_input == '-':
            return True
        
        # Check if it's a valid Excel column reference
        import re
        pattern = r'^[A-Z]+$'
        return bool(re.match(pattern, user_input))
    
    async def handle_sheet_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle sheet name input for mapping editor"""
        user_input = update.message.text.strip()
        
        # Store the message ID of the request message to delete it later
        request_message_id = context.user_data.get('sheet_name_request_message_id')
        
        # Delete user message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"DEBUG: Failed to delete user message: {e}")
        
        # Delete request message if it exists
        if request_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=request_message_id
                )
                context.user_data.pop('sheet_name_request_message_id', None)
            except Exception as e:
                print(f"DEBUG: Failed to delete request message: {e}")
        
        # Validate input - basic validation (not empty)
        if not user_input:
            error_message = "❌ Название листа не может быть пустым."
            await self.ui_manager.send_temp(
                update, context, error_message, duration=5
            )
            return self.config.AWAITING_SHEET_NAME_INPUT
        
        # Update sheet name in FSM state
        context.user_data['sheet_name'] = user_input
        
        # Return to mapping editor (this will edit the original message)
        return await self._show_mapping_editor(update, context)
    
    async def _show_mapping_editor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show mapping editor interface - delegate to callback handler"""
        from handlers.callback_handlers import CallbackHandlers
        callback_handler = CallbackHandlers(self.config, self.analysis_service)
        
        # Always use the main message for editing
        return await callback_handler._show_mapping_editor(update, context)