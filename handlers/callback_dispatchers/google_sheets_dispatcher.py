"""
Google Sheets dispatcher for handling Google Sheets related callback actions
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from config.locales.locale_manager import get_global_locale_manager
from services.ai_service import ReceiptAnalysisService
from services.google_sheets_service import GoogleSheetsService
from services.ingredient_matching_service import IngredientMatchingService
from models.ingredient_matching import IngredientMatchingResult
from handlers.base_callback_handler import BaseCallbackHandler
from utils.common_handlers import CommonHandlers
from utils.ingredient_storage import IngredientStorage


class GoogleSheetsDispatcher(BaseCallbackHandler):
    """Dispatcher for Google Sheets related callback actions"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService, google_sheets_handler=None):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        
        # Initialize services
        self.google_sheets_service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        self.ingredient_storage = IngredientStorage()
        self.common_handlers = CommonHandlers(config, analysis_service)
        self.google_sheets_handler = google_sheets_handler
        
        # ui_manager is already initialized in BaseCallbackHandler
    
    async def _ensure_google_sheets_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Ensure Google Sheets ingredients are loaded, load them if necessary"""
        return await self.common_handlers.ensure_ingredients_loaded(context, "google_sheets")
    
    async def _handle_google_sheets_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle Google Sheets related actions - EXACT COPY from original callback_handlers.py"""
        query = update.callback_query
        
        if action == "google_sheets_matching":
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context)
        elif action.startswith("gs_page_"):
            page = int(action.split("_")[-1])
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context, page)
        elif action in ["gs_manual_matching", "gs_position_selection"]:
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action in ["gs_upload", "upload_to_google_sheets"]:
            query = update.callback_query
            await query.answer(self.locale_manager.get_text("sheets.callback.uploading_data", context))
            
            receipt_data = context.user_data.get('receipt_data')
            if not receipt_data:
                await query.edit_message_text(
                    self.locale_manager.get_text("sheets.no_data_for_upload", context),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.analyze_receipt", context), 
                            callback_data="analyze_receipt"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.back_to_main_menu", context), 
                            callback_data="back_to_main_menu"
                        )]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            if not await self._ensure_google_sheets_ingredients_loaded(context):
                await query.edit_message_text(
                    self.locale_manager.get_text("sheets.callback.upload_error", context, 
                        message=self.locale_manager.get_text("sheets.callback.dictionary_not_loaded", context)),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.upload_to_google_sheets", context), 
                            callback_data="upload_to_google_sheets"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.back_to_receipt", context), 
                            callback_data="back_to_receipt"
                        )]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
            
            google_sheets_ingredients_for_matching = {}
            for ingredient_id, ingredient_data in google_sheets_ingredients.items():
                ingredient_name = ingredient_data.get('name', '')
                if ingredient_name:
                    google_sheets_ingredients_for_matching[ingredient_name] = ingredient_id
            
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            
            saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
            if saved_data:
                matching_result, changed_indices = saved_data
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = changed_indices
            else:
                ingredient_matching_service = IngredientMatchingService()
                matching_result = ingredient_matching_service.match_ingredients(receipt_data, google_sheets_ingredients_for_matching)
                
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = set()
            
            context.user_data['pending_google_sheets_upload'] = {
                'receipt_data': receipt_data,
                'matching_result': matching_result
            }
            
            # Save Google Sheets matching result to context for Excel generation
            context.user_data['google_sheets_matching_result'] = matching_result
            
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context, receipt_data, matching_result)
        elif action == "gs_show_table":
            matching_result = context.user_data.get('ingredient_matching_result')
            receipt_data = context.user_data.get('receipt_data')
            if matching_result:
                await self.google_sheets_handler._show_google_sheets_matching_table(update, context, receipt_data, matching_result)
        elif action.startswith("gs_select_item_"):
            item_index = int(action.split("_")[-1])
            context.user_data['current_gs_matching_item'] = item_index
            await self.google_sheets_handler._show_google_sheets_manual_matching_for_item(update, context, item_index)
        elif action.startswith("gs_select_suggestion_"):
            suggestion_number = int(action.split("_")[-1])
            await self.google_sheets_handler._handle_google_sheets_suggestion_selection(update, context, suggestion_number)
        elif action == "gs_next_item":
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "preview_google_sheets_upload":
            # User wants to preview Google Sheets upload
            await query.answer(self.locale_manager.get_text("sheets.callback.preview", context))
            
            # Get pending data
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if not pending_data:
                await query.edit_message_text(
                    self.locale_manager.get_text("sheets.callback.preview_data_not_found", context),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.upload_to_google_sheets", context), 
                            callback_data="upload_to_google_sheets"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.back_to_receipt", context), 
                            callback_data="back_to_receipt"
                        )]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            
            # Show Google Sheets preview
            await self.google_sheets_handler._show_google_sheets_preview(update, context, receipt_data, matching_result)
        elif action == "confirm_google_sheets_upload":
            # User confirmed Google Sheets upload
            await query.answer(self.locale_manager.get_text("sheets.callback.uploading_data", context))
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Get saved data
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if not pending_data:
                await self.ui_manager.send_menu(
                    update, context,
                    self.locale_manager.get_text("sheets.callback.upload_error", context, 
                        message=self.locale_manager.get_text("sheets.callback.receipt_data_not_found", context)),
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.upload_to_google_sheets", context), 
                            callback_data="upload_to_google_sheets"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.back_to_receipt", context), 
                            callback_data="back_to_receipt"
                        )]
                    ]),
                    'Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            
            # Execute actual upload
            await self._execute_google_sheets_upload(update, context, receipt_data, matching_result)
            
            # Clear pending data
            context.user_data.pop('pending_google_sheets_upload', None)
            return self.config.AWAITING_CORRECTION
        elif action == "select_google_sheets_position":
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "back_to_google_sheets_matching":
            # Return to Google Sheets matching table
            await query.answer(self.locale_manager.get_text("sheets.callback.back", context))
            
            # Delete the current message (position selection interface) to make it disappear
            try:
                await query.delete_message()
            except Exception as e:
                print(f"DEBUG: Error deleting message: {e}")
            
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if pending_data:
                await self.google_sheets_handler._show_google_sheets_matching_table(update, context, 
                    pending_data['receipt_data'], pending_data['matching_result'])
        elif action == "edit_google_sheets_matching":
            # User wants to edit Google Sheets matching
            await query.answer(self.locale_manager.get_text("sheets.callback.edit_matching", context))
            
            # Get pending data
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if not pending_data:
                await query.edit_message_text(
                    self.locale_manager.get_text("sheets.callback.upload_error", context, 
                        message=self.locale_manager.get_text("sheets.callback.matching_data_not_found", context)),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.upload_to_google_sheets", context), 
                            callback_data="upload_to_google_sheets"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.back_to_receipt", context), 
                            callback_data="back_to_receipt"
                        )]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            
            # Show Google Sheets matching table
            await self.google_sheets_handler._show_google_sheets_matching_table(update, context, receipt_data, matching_result)
        elif action == "back_to_google_sheets_preview":
            # Return to Google Sheets preview
            await query.answer(self.locale_manager.get_text("sheets.callback.back", context))
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if pending_data:
                receipt_data = pending_data['receipt_data']
                matching_result = pending_data['matching_result']
                await self.google_sheets_handler._show_google_sheets_preview(update, context, receipt_data, matching_result)
        elif action == "undo_google_sheets_upload":
            # Handle undo upload
            await query.answer(self.locale_manager.get_text("sheets.callback.undo_upload", context))
            await self.google_sheets_handler._handle_undo_google_sheets_upload(update, context)
        elif action == "start_new_receipt":
            # Handle start new receipt
            await update.callback_query.edit_message_text(self.locale_manager.get_text("welcome.analyze_receipt", context))
        elif action == "generate_excel_file":
            # Generate Excel file
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                await self.google_sheets_handler._generate_excel_file(update, context)
            else:
                await update.callback_query.edit_message_text(self.locale_manager.get_text("sheets.callback.matching_results_not_found", context))
        elif action.startswith("edit_google_sheets_item_"):
            # User wants to edit specific Google Sheets item
            item_index = int(action.split("_")[4])
            await query.answer(self.locale_manager.get_text("sheets.callback.edit_matching", context))
            await self.google_sheets_handler._show_google_sheets_manual_matching_for_item(update, context, item_index)
        elif action.startswith("select_google_sheets_line_"):
            # User selected a line for Google Sheets matching
            line_number = int(action.split("_")[4])
            item_index = line_number - 1  # Convert to 0-based index
            await query.answer(self.locale_manager.get_text("matching.callback.line_selected", context, line_number=line_number))
            
            # Delete the current message (position selection interface) to make it disappear
            try:
                await query.delete_message()
            except Exception as e:
                print(f"DEBUG: Error deleting message: {e}")
            
            await self.google_sheets_handler._show_google_sheets_manual_matching_for_item(update, context, item_index)
        elif action.startswith("select_google_sheets_suggestion_"):
            # User selected a suggestion for Google Sheets matching
            parts = action.split("_")
            item_index = int(parts[4])
            suggestion_index = int(parts[5])
            await query.answer(self.locale_manager.get_text("matching.callback.matched_successfully", context, 
                receipt_item="", ingredient_name=""))
            await self.google_sheets_handler._handle_google_sheets_suggestion_selection(update, context, item_index, suggestion_index)
        elif action.startswith("search_google_sheets_ingredient_"):
            # User wants to search for Google Sheets ingredient
            item_index = int(action.split("_")[4])
            await query.answer(self.locale_manager.get_text("sheets.callback.search", context))
            
            print(f"DEBUG: search_google_sheets_ingredient_{item_index} button pressed")
            print(f"DEBUG: Setting google_sheets_search_mode = True for item_index = {item_index}")
            
            # Set search mode - use the correct flag for ingredient search
            context.user_data['google_sheets_search_mode'] = True
            context.user_data['google_sheets_search_item_index'] = item_index
            
            print(f"DEBUG: Flags set - google_sheets_search_mode: {context.user_data.get('google_sheets_search_mode')}")
            print(f"DEBUG: Flags set - google_sheets_search_item_index: {context.user_data.get('google_sheets_search_item_index')}")
            
            await self.ui_manager.send_temp(
                update, context, 
                self.locale_manager.get_text("matching.callback.search_ingredient", context), 
                duration=10
            )
            return self.config.AWAITING_CORRECTION
        elif action.startswith("select_google_sheets_search_"):
            # User selected a search result for Google Sheets matching
            parts = action.split("_")
            item_index = int(parts[4])
            result_index = int(parts[5])
            await query.answer(self.locale_manager.get_text("matching.callback.matched_successfully", context, 
                receipt_item="", ingredient_name=""))
            await self.google_sheets_handler._handle_google_sheets_search_selection(update, context, item_index, result_index)
        elif action.startswith("select_google_sheets_position_match_"):
            # User selected a position match from search results
            parts = action.split("_")
            selected_line = int(parts[4])
            result_index = int(parts[5]) - 1
            await query.answer(self.locale_manager.get_text("matching.callback.matched_successfully", context, 
                receipt_item="", ingredient_name=""))
            await self.google_sheets_handler._handle_google_sheets_suggestion_selection(update, context, result_index)
        elif action in ["gs_skip_item", "skip_ingredient"]:
            await query.answer(self.locale_manager.get_text("matching.callback.skip_item", context))
            await self.google_sheets_handler._handle_skip_item(update, context)
        elif action in ["gs_next_item", "next_ingredient_match"]:
            await query.answer(self.locale_manager.get_text("matching.callback.next_position", context))
            await self.google_sheets_handler._handle_next_item(update, context)
        
        return self.config.AWAITING_CORRECTION
    
    async def _execute_google_sheets_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                          receipt_data, matching_result):
        """Execute actual Google Sheets upload - EXACT COPY from original callback_handlers.py"""
        try:
            # Save Google Sheets matching result to context for Excel generation
            context.user_data['google_sheets_matching_result'] = matching_result
            
            # Show upload summary
            summary = self.google_sheets_service.get_upload_summary(receipt_data, matching_result)
            
            # Upload data
            success, message = self.google_sheets_service.upload_receipt_data(
                receipt_data, 
                matching_result,
                self.config.GOOGLE_SHEETS_WORKSHEET_NAME
            )
            
            if success:
                # Save upload data for potential undo
                context.user_data['last_google_sheets_upload'] = {
                    'worksheet_name': self.config.GOOGLE_SHEETS_WORKSHEET_NAME,
                    'row_count': len(receipt_data.items),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Show new success page interface
                await self._show_upload_success_page(update, context, summary, message)
            else:
                # Show error message
                error_text = self.locale_manager.get_text("sheets.callback.upload_error", context, message=message)
                await self.ui_manager.send_menu(
                    update, context,
                    error_text,
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.reanalyze", context), 
                            callback_data="upload_to_google_sheets"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.generate_supply_file", context), 
                            callback_data="generate_file_from_table"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.back_to_receipt", context), 
                            callback_data="back_to_receipt"
                        )]
                    ]),
                    'Markdown'
                )
                
        except Exception as e:
            print(f"DEBUG: Error uploading to Google Sheets: {e}")
            await self.ui_manager.send_menu(
                update, context,
                self.locale_manager.get_text("sheets.callback.unexpected_error", context, error=str(e)),
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        self.locale_manager.get_text("buttons.back_to_receipt", context), 
                        callback_data="back_to_receipt"
                    )]
                ]),
                'Markdown'
            )
    
    async def _show_upload_success_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      summary: str, message: str):
        """Show upload success page - EXACT COPY from original callback_handlers.py"""
        # Clean up all messages except anchor first
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        # Create success message with only the header
        success_text = self.locale_manager.get_text("sheets.callback.data_successfully_uploaded", context)
        
        # Create new button layout
        keyboard = [
            [InlineKeyboardButton(
                self.locale_manager.get_text("sheets.callback.undo_upload", context), 
                callback_data="undo_google_sheets_upload"
            )],
            [InlineKeyboardButton(
                self.locale_manager.get_text("sheets.callback.generate_file", context), 
                callback_data="generate_excel_file"
            )],
            [InlineKeyboardButton(
                self.locale_manager.get_text("sheets.callback.back_to_receipt_button", context), 
                callback_data="back_to_receipt"
            )],
            [InlineKeyboardButton(
                self.locale_manager.get_text("sheets.callback.upload_new_receipt", context), 
                callback_data="start_new_receipt"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context,
            success_text,
            reply_markup,
            'Markdown'
        )
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name to max length"""
        return self.common_handlers.truncate_name(name, max_length)
    
    def _get_google_sheets_status_emoji(self, match_status) -> str:
        """Get emoji for Google Sheets match status"""
        status_emojis = {
            'exact': '✅',
            'partial': '⚠️',
            'no_match': '❌'
        }
        return status_emojis.get(match_status.value, '❓')
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        await self.common_handlers.send_long_message_with_keyboard(message, text, reply_markup)