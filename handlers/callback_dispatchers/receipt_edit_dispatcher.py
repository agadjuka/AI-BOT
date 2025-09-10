"""
Receipt edit dispatcher for Telegram bot
"""
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisService
from models.receipt import ReceiptData
from handlers.base_callback_handler import BaseCallbackHandler
from handlers.receipt_edit_callback_handler import ReceiptEditCallbackHandler


class ReceiptEditDispatcher(BaseCallbackHandler):
    """Dispatcher for receipt edit related actions"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        super().__init__(config, analysis_service)
        
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
            await self.receipt_edit_handler._show_final_report_with_edit_button_callback(update, context)
        elif action == "edit_receipt":
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action == "back_to_edit":
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action.startswith("edit_item_") or action.startswith("edit_"):
            # Skip Google Sheets actions
            if action.startswith("edit_google_sheets_"):
                return self.config.AWAITING_CORRECTION
            
            # Handle both "edit_item_X" and "edit_X" patterns
            if action.startswith("edit_item_"):
                item_number = int(action.split("_")[-1])
            else:  # action.startswith("edit_")
                item_number = int(action.split("_")[-1])
            
            context.user_data['line_to_edit'] = item_number
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action.startswith("delete_item_"):
            item_number = int(action.split("_")[-1])
            context.user_data['deleting_item'] = item_number
            await update.callback_query.edit_message_text(
                f"🗑️ Удаление позиции {item_number}\n\n"
                "Подтвердите удаление (да/нет):"
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        elif action == "delete_row":
            await self.ui_manager.send_temp(
                update, context,
                "🗑️ Удаление строки\n\n"
                "Введите номер строки для удаления:",
                duration=30
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        elif action == "edit_line_number":
            await self.ui_manager.send_temp(
                update, context,
                "✏️ Редактирование строки\n\n"
                "Введите номер строки для редактирования:",
                duration=30
            )
            return self.config.AWAITING_LINE_NUMBER
        elif action == "manual_edit_total":
            await self.ui_manager.send_temp(
                update, context,
                "💰 Редактирование общей суммы\n\n"
                "Введите новую общую сумму:",
                duration=30
            )
            return self.config.AWAITING_TOTAL_EDIT
        elif action == "reanalyze":
            await update.callback_query.answer("🔄 Анализирую фото заново...")
            
            await self.ui_manager.send_temp(
                update, context,
                "🔄 Обрабатываю квитанцию...",
                duration=10
            )
            
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            self._clear_receipt_data(context)
            
            try:
                analysis_data = self.analysis_service.analyze_receipt(self.config.PHOTO_FILE_NAME)
                receipt_data = ReceiptData.from_dict(analysis_data)
                
                is_valid, message = self.validator.validate_receipt_data(receipt_data)
                if not is_valid:
                    print(f"Предупреждение валидации: {message}")
                
                context.user_data['receipt_data'] = receipt_data
                context.user_data['original_data'] = ReceiptData.from_dict(receipt_data.to_dict())
                
                from handlers.photo_handler import PhotoHandler
                photo_handler = PhotoHandler(self.config, self.analysis_service)
                await photo_handler.show_final_report_with_edit_button(update, context)
                return self.config.AWAITING_CORRECTION
                
            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
                print(f"Ошибка парсинга JSON или структуры данных от Gemini: {e}")
                await update.callback_query.message.reply_text("Не удалось распознать структуру чека. Попробуйте сделать фото более четким.")
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
                    await update.callback_query.edit_message_text("❌ Данные чека не найдены")
                    return self.config.AWAITING_CORRECTION
            
            await self.ui_manager.back_to_receipt(update, context)
            await self.receipt_edit_handler._show_final_report_with_edit_button_callback(update, context)
        elif action == "back_to_main_menu":
            await update.callback_query.edit_message_text(
                "🏠 Главное меню\n\n"
                "Используйте /start для начала новой работы."
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
                
                field_display_names = {
                    'name': 'название товара',
                    'quantity': 'количество',
                    'price': 'цену',
                    'total': 'сумму'
                }
                
                field_name_display = field_display_names.get(field_name, field_name)
                temp_message = await self.ui_manager.send_temp(
                    update, context,
                    f"✏️ Редактирование {field_name_display} для строки {line_number}\n\n"
                    f"Введите новое значение:",
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
            
            await self.receipt_edit_handler._show_final_report_with_edit_button_callback(update, context)
            return self.config.AWAITING_CORRECTION
        
        return self.config.AWAITING_CORRECTION
