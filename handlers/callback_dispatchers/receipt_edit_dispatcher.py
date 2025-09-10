"""
Receipt edit dispatcher for Telegram bot
"""
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from models.receipt import ReceiptData
from handlers.base_callback_handler import BaseCallbackHandler
from handlers.receipt_edit_callback_handler import ReceiptEditCallbackHandler
from config.locales.locale_manager import get_global_locale_manager


class ReceiptEditDispatcher(BaseCallbackHandler):
    """Dispatcher for receipt edit related actions"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        
        # Initialize specialized handler
        self.receipt_edit_handler = ReceiptEditCallbackHandler(config, analysis_service)
    
    async def _handle_receipt_edit_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle receipt edit related actions"""
        if action == "add_row":
            await self.receipt_edit_handler._add_new_row(update, context)
        elif action == "edit_total":
            await self.receipt_edit_handler._show_total_edit_menu(update, context)
        elif action == "auto_calculate_total":
            await self.receipt_edit_handler._auto_calculate_total(update, context)
        elif action == "finish_editing":
            # Use photo_handler method which has proper localization
            from handlers.photo_handler import PhotoHandler
            photo_handler = PhotoHandler(self.config, self.analysis_service)
            await photo_handler.show_final_report_with_edit_button(update, context)
        elif action == "edit_receipt":
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action == "back_to_edit":
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action.startswith("edit_item_"):
            # Handle "edit_item_X" pattern
            item_number = int(action.split("_")[-1])
            
            context.user_data['line_to_edit'] = item_number
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action.startswith("edit_") and action != "edit_line_number" and not action.startswith("edit_google_sheets_"):
            # Handle "edit_X" pattern (but not edit_line_number or Google Sheets actions)
            item_number = int(action.split("_")[-1])
            
            context.user_data['line_to_edit'] = item_number
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action.startswith("delete_item_"):
            item_number = int(action.split("_")[-1])
            context.user_data['deleting_item'] = item_number
            await update.callback_query.edit_message_text(
                self.locale_manager.get_text("analysis.deleting_item_confirmation", context, item_number=item_number)
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        elif action == "delete_row":
            await self.ui_manager.send_temp(
                update, context,
                self.locale_manager.get_text("analysis.deleting_line", context),
                duration=30
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        elif action == "edit_line_number":
            await self.ui_manager.send_temp(
                update, context,
                self.locale_manager.get_text("analysis.editing_line_input", context),
                duration=30
            )
            return self.config.AWAITING_LINE_NUMBER
        elif action == "manual_edit_total":
            await self.ui_manager.send_temp(
                update, context,
                self.locale_manager.get_text("analysis.editing_total_input", context),
                duration=30
            )
            return self.config.AWAITING_TOTAL_EDIT
        elif action == "reanalyze":
            await update.callback_query.answer(self.locale_manager.get_text("status.analyzing_receipt", context))
            
            await self.ui_manager.send_temp(
                update, context,
                self.locale_manager.get_text("status.processing_receipt", context),
                duration=10
            )
            
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            self._clear_receipt_data(context)
            
            try:
                analysis_data = await self.analysis_service.analyze_receipt(self.config.PHOTO_FILE_NAME)
                receipt_data = ReceiptData.from_dict(analysis_data)
                
                is_valid, message = self.validator.validate_receipt_data(receipt_data)
                if not is_valid:
                    print(f"Validation warning: {message}")
                
                context.user_data['receipt_data'] = receipt_data
                context.user_data['original_data'] = ReceiptData.from_dict(receipt_data.to_dict())
                
                from handlers.photo_handler import PhotoHandler
                photo_handler = PhotoHandler(self.config, self.analysis_service)
                await photo_handler.show_final_report_with_edit_button(update, context)
                return self.config.AWAITING_CORRECTION
                
            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
                print(f"JSON parsing error or data structure from Gemini: {e}")
                await update.callback_query.message.reply_text(self.locale_manager.get_text("errors.parsing_error", context))
                return self.config.AWAITING_CORRECTION
        elif action == "back_to_receipt":
            try:
                await update.callback_query.delete_message()
            except Exception as e:
                print(f"DEBUG: Error deleting message: {e}")
            
            original_data = context.user_data.get('original_data')
            if original_data:
                context.user_data['receipt_data'] = ReceiptData.from_dict(original_data.to_dict())
            else:
                receipt_data = context.user_data.get('receipt_data')
                if not receipt_data:
                    await update.callback_query.edit_message_text(self.locale_manager.get_text("errors.receipt_data_not_found", context))
                    return self.config.AWAITING_CORRECTION
            
            await self.ui_manager.back_to_receipt(update, context)
            # Use photo_handler method which has proper localization
            from handlers.photo_handler import PhotoHandler
            photo_handler = PhotoHandler(self.config, self.analysis_service)
            await photo_handler.show_final_report_with_edit_button(update, context)
        elif action == "back_to_main_menu":
            await update.callback_query.edit_message_text(
                self.locale_manager.get_text("welcome.main_menu", context)
            )
            return self.config.AWAITING_CORRECTION
        elif action.startswith("field_"):
            parts = action.split("_")
            if len(parts) >= 3:
                line_number = int(parts[1])
                field_name = parts[2]
                context.user_data['field_to_edit'] = field_name
                context.user_data['line_to_edit'] = line_number
                
                # Save the current edit menu message ID before showing input request
                if hasattr(update, 'callback_query') and update.callback_query:
                    context.user_data['edit_menu_message_id'] = update.callback_query.message.message_id
                    print(f"DEBUG: Saved edit_menu_message_id = {update.callback_query.message.message_id}")
                
                field_name_display = self.locale_manager.get_text(f"analysis.field_display_names.{field_name}", context)
                temp_message = await self.ui_manager.send_temp(
                    update, context,
                    self.locale_manager.get_text("analysis.field_edit_input", context, 
                                          field_name=field_name_display, line_number=line_number),
                    duration=30
                )
                
                if 'messages_to_cleanup' not in context.user_data:
                    context.user_data['messages_to_cleanup'] = []
                context.user_data['messages_to_cleanup'].append(temp_message.message_id)
                return self.config.AWAITING_FIELD_EDIT
        elif action.startswith("apply_"):
            line_number = int(action.split("_")[-1])
            context.user_data['applying_changes'] = line_number
            
            current_data = context.user_data.get('receipt_data')
            if current_data:
                context.user_data['original_data'] = ReceiptData.from_dict(current_data.to_dict())
            
            context.user_data.pop('field_to_edit', None)
            context.user_data.pop('line_to_edit', None)
            
            # Use photo_handler method which has proper localization
            from handlers.photo_handler import PhotoHandler
            photo_handler = PhotoHandler(self.config, self.analysis_service)
            await photo_handler.show_final_report_with_edit_button(update, context)
            return self.config.AWAITING_CORRECTION
        
        return self.config.AWAITING_CORRECTION
