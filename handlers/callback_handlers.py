"""
Refactored callback handlers for Telegram bot
"""
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisService
from services.google_sheets_service import GoogleSheetsService
from models.receipt import ReceiptData
from handlers.base_callback_handler import BaseCallbackHandler
from handlers.receipt_edit_callback_handler import ReceiptEditCallbackHandler
from handlers.callback_dispatchers.receipt_edit_dispatcher import ReceiptEditDispatcher
from handlers.callback_dispatchers.ingredient_matching_dispatcher import IngredientMatchingDispatcher
from handlers.callback_dispatchers.google_sheets_dispatcher import GoogleSheetsDispatcher
from handlers.callback_dispatchers.file_generation_dispatcher import FileGenerationDispatcher
from handlers.ingredient_matching_callback_handler import IngredientMatchingCallbackHandler
from handlers.google_sheets_callback_handler import GoogleSheetsCallbackHandler
from handlers.file_generation_callback_handler import FileGenerationCallbackHandler


class CallbackHandlers(BaseCallbackHandler):
    """Main callback handlers coordinator - refactored version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        super().__init__(config, analysis_service)
        
        # Initialize services
        self.google_sheets_service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        # Initialize specialized handlers
        self.receipt_edit_handler = ReceiptEditCallbackHandler(config, analysis_service)
        self.receipt_edit_dispatcher = ReceiptEditDispatcher(config, analysis_service)
        self.ingredient_matching_handler = IngredientMatchingCallbackHandler(config, analysis_service)
        self.ingredient_matching_dispatcher = IngredientMatchingDispatcher(config, analysis_service, self.ingredient_matching_handler, None)
        self.google_sheets_handler = GoogleSheetsCallbackHandler(config, analysis_service)
        self.google_sheets_dispatcher = GoogleSheetsDispatcher(config, analysis_service, self.google_sheets_handler)
        self.file_generation_handler = FileGenerationCallbackHandler(config, analysis_service)
        self.file_generation_dispatcher = FileGenerationDispatcher(config, analysis_service, self.google_sheets_handler, self.ingredient_matching_handler)
        
        # Update dispatcher with file generation handler reference
        self.ingredient_matching_dispatcher.file_generation_handler = self.file_generation_handler
    
    async def handle_correction_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle correction choice callback - main dispatcher"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        # Route to appropriate handler based on action
        if action in ["add_row", "edit_total", "auto_calculate_total", "finish_editing", "edit_receipt", 
                     "back_to_edit", "delete_row", "edit_line_number", "manual_edit_total", "reanalyze", 
                     "back_to_receipt", "back_to_main_menu"] or action.startswith("field_") or action.startswith("apply_") or action.startswith("edit_item_") or action.startswith("delete_item_"):
            return await self.receipt_edit_dispatcher._handle_receipt_edit_actions(update, context, action)
        
        elif action in ["ingredient_matching", "manual_matching", "position_selection", "match_item_", 
                       "select_item_", "select_suggestion_", "next_item", "skip_item", "show_matching_table",
                       "manual_match_ingredients", "rematch_ingredients", "apply_matching_changes",
                       "select_position_for_matching", "back_to_matching_overview", "search_ingredient",
                       "skip_ingredient", "next_ingredient_match", "confirm_back_without_changes",
                       "cancel_back"]:
            return await self._handle_ingredient_matching_actions(update, context, action)
        
        elif action in ["google_sheets_matching", "gs_upload", "upload_to_google_sheets", "gs_show_table",
                       "edit_google_sheets_matching", "preview_google_sheets_upload", "confirm_google_sheets_upload",
                       "select_google_sheets_position", "back_to_google_sheets_matching",
                       "back_to_google_sheets_preview", "undo_google_sheets_upload", "generate_excel_file",
                       "gs_skip_item", "gs_next_item", "skip_ingredient", "next_ingredient_match"] or action.startswith("edit_google_sheets_item_") or action.startswith("select_google_sheets_line_") or action.startswith("select_google_sheets_suggestion_") or action.startswith("search_google_sheets_ingredient_") or action.startswith("select_google_sheets_search_") or action.startswith("select_google_sheets_position_match_"):
            return await self.google_sheets_dispatcher._handle_google_sheets_actions(update, context, action)
        
        elif action in ["generate_supply_file", "generate_poster_file", "generate_google_sheets_file",
                       "generate_file_xlsx", "generate_file_from_table", "match_ingredients"]:
            return await self.file_generation_dispatcher._handle_file_generation_actions(update, context, action)
        
        elif action == "finish":
            await query.answer("Отчет уже готов!")
            return self.config.AWAITING_CORRECTION
        
        elif action == "cancel":
            return await self._cancel(update, context)
        
        elif action == "analyze_receipt":
            await update.callback_query.edit_message_text(
                "📸 Анализ чека\n\n"
                "Отправьте фото чека для анализа:"
            )
            return self.config.AWAITING_CORRECTION
        
        elif action == "noop":
            await query.answer()
            return self.config.AWAITING_CORRECTION
        
        else:
            await query.answer("Неизвестное действие")
            return self.config.AWAITING_CORRECTION
    
    
    async def _handle_ingredient_matching_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle ingredient matching related actions"""
        return await self.ingredient_matching_dispatcher._handle_ingredient_matching_actions(update, context, action)
    
    
    
    
    async def _cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current operation"""
        query = update.callback_query
        await query.answer()
        
        # Clear all data
        self._clear_receipt_data(context)
        
        # Show start message - avoid circular import
        await query.edit_message_text(
            "❌ Операция отменена\n\n"
            "Используйте /start для начала новой работы."
        )
        
        return self.config.AWAITING_CORRECTION
    
    
    async def _show_upload_success_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      summary: str, message: str):
        """Show the new upload success page interface"""
        # Clean up all messages except anchor first
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        # Create success message with only the header
        success_text = "✅ **Данные успешно загружены в Google Sheets!**"
        
        # Create new button layout
        keyboard = [
            [InlineKeyboardButton("↩️ Отменить загрузку", callback_data="undo_google_sheets_upload")],
            [InlineKeyboardButton("📄 Сгенерировать файл", callback_data="generate_excel_file")],
            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
            [InlineKeyboardButton("📸 Загрузить новый чек", callback_data="start_new_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context,
            success_text,
            reply_markup,
            'Markdown'
        )
    
    async def _handle_undo_google_sheets_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle undo Google Sheets upload"""
        try:
            # Get last upload data
            last_upload = context.user_data.get('last_google_sheets_upload')
            if not last_upload:
                await update.callback_query.edit_message_text(
                    "❌ **Нет данных о последней загрузке для отмены**\n\n"
                    "Информация о последней загрузке не найдена.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            # Get upload details
            worksheet_name = last_upload.get('worksheet_name', 'Receipts')
            row_count = last_upload.get('row_count', 0)
            
            if row_count <= 0:
                await update.callback_query.edit_message_text(
                    "❌ **Нет данных для отмены**\n\n"
                    "Количество строк для отмены равно нулю.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            # Attempt to delete the uploaded rows
            success, message = self.google_sheets_service.delete_last_uploaded_rows(worksheet_name, row_count)
            
            if success:
                # Clear the last upload data
                context.user_data.pop('last_google_sheets_upload', None)
                
                # Get the data for preview
                pending_data = context.user_data.get('pending_google_sheets_upload')
                if pending_data:
                    receipt_data = pending_data['receipt_data']
                    matching_result = pending_data['matching_result']
                    
                    # Show regular preview (same as before upload)
                    await self.google_sheets_dispatcher._show_google_sheets_preview(update, context, receipt_data, matching_result)
                else:
                    # Fallback if no pending data
                    await update.callback_query.edit_message_text(
                        f"✍️ **Загрузка успешно отменена!**\n\n"
                        f"📊 **Отменено строк:** {row_count}\n"
                        f"📋 **Лист:** {worksheet_name}\n"
                        f"🕒 **Время отмены:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"Данные были удалены из Google Sheets.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
                            [InlineKeyboardButton("📸 Загрузить новый чек", callback_data="start_new_receipt")]
                        ]),
                        parse_mode='Markdown'
                    )
            else:
                # Show error message
                await update.callback_query.edit_message_text(
                    f"❌ **Ошибка отмены загрузки**\n\n"
                    f"Не удалось отменить загрузку: {message}\n\n"
                    f"Попробуйте удалить данные вручную в Google Sheets.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
                        [InlineKeyboardButton("🔄 Попробовать снова", callback_data="undo_google_sheets_upload")]
                    ]),
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            print(f"DEBUG: Error in undo Google Sheets upload: {e}")
            await update.callback_query.edit_message_text(
                f"❌ **Произошла ошибка при отмене загрузки**\n\n"
                f"Неожиданная ошибка: {str(e)}\n\n"
                f"Попробуйте удалить данные вручную в Google Sheets.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
                ]),
                parse_mode='Markdown'
            )
        
        return self.config.AWAITING_CORRECTION
