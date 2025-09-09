"""
Refactored callback handlers for Telegram bot - dispatcher only
"""
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisService
from services.google_sheets_service import GoogleSheetsService
from handlers.base_callback_handler import BaseCallbackHandler
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
        
        # Initialize specialized handlers for dispatchers
        self.ingredient_matching_handler = IngredientMatchingCallbackHandler(config, analysis_service)
        self.google_sheets_handler = GoogleSheetsCallbackHandler(config, analysis_service)
        self.file_generation_handler = FileGenerationCallbackHandler(config, analysis_service)
        
        # Initialize dispatchers
        self.receipt_edit_dispatcher = ReceiptEditDispatcher(config, analysis_service)
        self.ingredient_matching_dispatcher = IngredientMatchingDispatcher(config, analysis_service, self.ingredient_matching_handler, self.file_generation_handler)
        self.google_sheets_dispatcher = GoogleSheetsDispatcher(config, analysis_service, self.google_sheets_handler)
        self.file_generation_dispatcher = FileGenerationDispatcher(config, analysis_service, self.google_sheets_handler, self.ingredient_matching_handler)
    
    async def handle_correction_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle correction choice callback - main dispatcher"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        # Route to appropriate handler based on action
        if action in ["add_row", "edit_total", "auto_calculate_total", "finish_editing", "edit_receipt", 
                     "back_to_edit", "delete_row", "edit_line_number", "manual_edit_total", "reanalyze", 
                     "back_to_receipt", "back_to_main_menu"] or action.startswith("field_") or action.startswith("apply_") or action.startswith("edit_item_") or action.startswith("edit_") or action.startswith("delete_item_"):
            return await self.receipt_edit_dispatcher._handle_receipt_edit_actions(update, context, action)
        
        elif action in ["ingredient_matching", "manual_matching", "position_selection", "match_item_", 
                       "select_item_", "select_suggestion_", "next_item", "skip_item", "show_matching_table",
                       "manual_match_ingredients", "rematch_ingredients", "apply_matching_changes",
                       "select_position_for_matching", "back_to_matching_overview", "search_ingredient",
                       "skip_ingredient", "next_ingredient_match", "confirm_back_without_changes",
                       "cancel_back"]:
            return await self.ingredient_matching_dispatcher._handle_ingredient_matching_actions(update, context, action)
        
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
