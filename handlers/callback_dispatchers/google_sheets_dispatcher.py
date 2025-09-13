"""
Google Sheets dispatcher for handling Google Sheets related callback actions
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from config.locales.locale_manager import get_global_locale_manager
from services.ai_service import ReceiptAnalysisServiceCompat
from services.google_sheets_service import GoogleSheetsService
from services.ingredient_matching_service import IngredientMatchingService
from models.ingredient_matching import IngredientMatchingResult
from handlers.base_callback_handler import BaseCallbackHandler
from utils.common_handlers import CommonHandlers
from utils.ingredient_storage import IngredientStorage


class GoogleSheetsDispatcher(BaseCallbackHandler):
    """Dispatcher for Google Sheets related callback actions"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat, google_sheets_handler=None):
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
                            self.locale_manager.get_text("buttons.scan_receipt", context), 
                            callback_data="start_new_receipt"
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
            
            # Get user's personal ingredients from Firestore
            from services.ingredients_manager import get_ingredients_manager
            ingredients_manager = get_ingredients_manager()
            user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
            
            # Convert user ingredients to the format expected by matching service
            # If no personal ingredients, create empty dict - menu will still open
            user_ingredients_for_matching = {}
            if user_ingredients:
                for i, ingredient_name in enumerate(user_ingredients):
                    user_ingredients_for_matching[ingredient_name] = f"user_ingredient_{i}"
            else:
                print("DEBUG: No personal ingredients found, opening matching menu with empty ingredient list")
            
            print(f"DEBUG: Using {len(user_ingredients_for_matching)} personal ingredients for Google Sheets matching")
            
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            
            saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
            if saved_data:
                matching_result, changed_indices = saved_data
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = changed_indices
            else:
                ingredient_matching_service = IngredientMatchingService()
                matching_result = ingredient_matching_service.match_ingredients(receipt_data, user_ingredients_for_matching)
                
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
        elif action.startswith("gs_select_sheet_"):
            # User selected a different sheet for preview
            sheet_id = action.replace("gs_select_sheet_", "")
            await query.answer(self.locale_manager.get_text("sheets.callback.switching_sheet", context))
            
            # Store selected sheet ID in context for upload
            context.user_data['selected_sheet_id'] = sheet_id
            print(f"DEBUG: Selected sheet ID stored in context: {sheet_id}")
            
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
            
            # Show Google Sheets preview with selected sheet
            await self.google_sheets_handler._show_google_sheets_preview(update, context, receipt_data, matching_result, sheet_id)
        elif action == "confirm_google_sheets_upload":
            # User confirmed Google Sheets upload - simplified version
            await query.answer(self.locale_manager.get_text("sheets.callback.uploading_data", context))
            
            # Get saved data
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if not pending_data:
                await query.edit_message_text("❌ Данные для загрузки не найдены. Попробуйте снова.")
                return self.config.AWAITING_CORRECTION
            
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            
            # Ensure selected_sheet_id is preserved in context for upload
            if 'selected_sheet_id' not in context.user_data:
                # If no sheet was explicitly selected, use the default sheet
                user_id = update.effective_user.id
                default_sheet = await self.google_sheets_handler._get_user_default_sheet(user_id)
                if default_sheet:
                    context.user_data['selected_sheet_id'] = default_sheet.get('doc_id')
                    print(f"DEBUG: Using default sheet ID: {default_sheet.get('doc_id')}")
                else:
                    print("DEBUG: No default sheet found, will use fallback in _execute_google_sheets_upload")
            else:
                print(f"DEBUG: Using selected sheet ID from context: {context.user_data['selected_sheet_id']}")
            
            # Execute upload with column mapping from Firestore
            await self._execute_google_sheets_upload(update, context, receipt_data, matching_result)
            
            # Clear pending data
            context.user_data.pop('pending_google_sheets_upload', None)
            return self.config.AWAITING_CORRECTION
        
        # Handle remaining actions
        return await self._handle_google_sheets_actions_continued(update, context, action)
    
    async def _handle_google_sheets_actions_continued(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle remaining Google Sheets related actions"""
        query = update.callback_query
        
        if action == "select_google_sheets_position":
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "back_to_google_sheets_matching":
            # Return to Google Sheets matching table
            await query.answer(self.locale_manager.get_text("sheets.callback.back", context))
            
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
            # Handle start new receipt - show beautiful message with emojis
            print(f"DEBUG: start_new_receipt handler called for user {update.effective_user.id}")
            await query.answer()
            
            # Clear all previous messages except anchor
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Send beautiful new receipt ready message
            new_receipt_text = self.locale_manager.get_text("welcome.new_receipt_ready", context)
            print(f"DEBUG: Sending new receipt ready message: {new_receipt_text}")
            await self.ui_manager.send_menu(update, context, new_receipt_text, None, 'Markdown')
            
            # Clear user data to prepare for new receipt
            context.user_data.clear()
            print(f"DEBUG: Cleared user data for new receipt")
            
            return self.config.AWAITING_CORRECTION
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
        """Execute actual Google Sheets upload with selected sheet"""
        try:
            # Save Google Sheets matching result to context for Excel generation
            context.user_data['google_sheets_matching_result'] = matching_result
            
            # Get selected sheet ID from context
            selected_sheet_id = context.user_data.get('selected_sheet_id')
            print(f"DEBUG: _execute_google_sheets_upload - selected_sheet_id from context: {selected_sheet_id}")
            
            if not selected_sheet_id:
                # Fallback to default sheet
                user_id = update.effective_user.id
                default_sheet = await self.google_sheets_handler._get_user_default_sheet(user_id)
                if not default_sheet:
                    error_text = self.locale_manager.get_text("sheets.callback.no_sheet_selected", context)
                    await self.ui_manager.send_menu(update, context, error_text, InlineKeyboardMarkup([]), 'Markdown')
                    return
                selected_sheet_id = default_sheet.get('doc_id')
                print(f"DEBUG: Using fallback default sheet ID: {selected_sheet_id}")
            else:
                print(f"DEBUG: Using selected sheet ID from context: {selected_sheet_id}")
            
            # Get sheet data
            from services.google_sheets_manager import get_google_sheets_manager
            sheets_manager = get_google_sheets_manager()
            sheet_data = await sheets_manager.get_user_sheet_by_id(update.effective_user.id, selected_sheet_id)
            
            if not sheet_data:
                error_text = self.locale_manager.get_text("sheets.callback.sheet_not_found", context)
                await self.ui_manager.send_menu(update, context, error_text, InlineKeyboardMarkup([]), 'Markdown')
                return
            
            # Create GoogleSheetsService instance for the selected sheet
            # Use the same approach as in _check_sheet_access for consistency
            from services.google_sheets_service import GoogleSheetsService
            sheet_service = GoogleSheetsService(
                credentials_path=self.config.GOOGLE_SHEETS_CREDENTIALS,
                spreadsheet_id=sheet_data.get('sheet_id')
            )
            
            # Show upload summary
            summary = sheet_service.get_upload_summary(receipt_data, matching_result)
            
            # Get the actual worksheet name from Google Sheets API
            configured_sheet_name = sheet_data.get('sheet_name', 'Sheet1')
            print(f"DEBUG: Using sheet_name from Firestore: {configured_sheet_name}")
            actual_worksheet_name = await self._get_actual_worksheet_name(sheet_service, configured_sheet_name)
            print(f"DEBUG: Final worksheet name for upload: {actual_worksheet_name}")
            
            # Upload data using the selected sheet's configuration with column mapping
            success, message = sheet_service.upload_receipt_data(
                receipt_data, 
                matching_result,
                actual_worksheet_name,
                column_mapping=sheet_data.get('column_mapping', {}),
                data_start_row=sheet_data.get('data_start_row', 1)
            )
            
            # If upload failed, show the error message directly
            # No need for complex JWT error handling since we're using the same credentials as in _check_sheet_access
            
            if success:
                # Save upload data for potential undo with actual worksheet name
                upload_data = {
                    'worksheet_name': actual_worksheet_name,
                    'row_count': len(receipt_data.items),
                    'timestamp': datetime.now().isoformat(),
                    'sheet_id': sheet_data.get('sheet_id'),
                    'sheet_name': sheet_data.get('friendly_name', 'Unknown'),
                    'data_start_row': sheet_data.get('data_start_row', 1)
                }
                context.user_data['last_google_sheets_upload'] = upload_data
                
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
                            self.locale_manager.get_text("sheets.callback.generate_file", context), 
                            callback_data="generate_excel_file"
                        )],
                        [InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.back_to_receipt", context), 
                            callback_data="back_to_receipt"
                        )]
                    ]),
                    'HTML'
                )
                
        except Exception as e:
            print(f"DEBUG: Error uploading to Google Sheets: {e}")
            # Escape special characters to prevent Markdown parsing errors
            error_message = str(e).replace('`', '').replace('*', '').replace('_', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
            # Additional escaping for common problematic characters
            error_message = error_message.replace('!', '').replace('@', '').replace('#', '').replace('$', '').replace('%', '').replace('^', '').replace('&', '').replace('+', '').replace('=', '').replace('{', '').replace('}', '').replace('|', '').replace('\\', '').replace(':', '').replace(';', '').replace('"', '').replace("'", '').replace('<', '').replace('>', '').replace(',', '').replace('.', '').replace('?', '').replace('/', '')
            
            await self.ui_manager.send_menu(
                update, context,
                self.locale_manager.get_text("sheets.callback.unexpected_error", context, error=error_message),
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        self.locale_manager.get_text("buttons.back_to_receipt", context), 
                        callback_data="back_to_receipt"
                    )]
                ]),
                'HTML'  # Use HTML instead of Markdown to avoid parsing issues
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
            'HTML'
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
    
    async def _get_actual_worksheet_name(self, sheet_service, configured_name: str) -> str:
        """Get the actual worksheet name from Google Sheets API"""
        try:
            # Get spreadsheet info to find the actual worksheet name
            spreadsheet = sheet_service.service.spreadsheets().get(spreadsheetId=sheet_service.spreadsheet_id).execute()
            
            print(f"DEBUG: Looking for worksheet '{configured_name}' in spreadsheet")
            print(f"DEBUG: Available sheets: {[sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]}")
            
            # Look for worksheet with configured name or similar
            for sheet in spreadsheet.get('sheets', []):
                sheet_title = sheet['properties']['title']
                print(f"DEBUG: Checking sheet: '{sheet_title}'")
                
                # Check if this is the worksheet we're looking for
                if sheet_title == configured_name:
                    print(f"DEBUG: Found exact match: '{sheet_title}'")
                    return sheet_title
            
            # If exact match not found, try case-insensitive search
            for sheet in spreadsheet.get('sheets', []):
                sheet_title = sheet['properties']['title']
                if sheet_title.lower() == configured_name.lower():
                    print(f"DEBUG: Found case-insensitive match: '{sheet_title}'")
                    return sheet_title
            
            # If still not found, return the first sheet name as fallback
            if spreadsheet.get('sheets'):
                first_sheet_name = spreadsheet['sheets'][0]['properties']['title']
                print(f"DEBUG: No match found, using first sheet: '{first_sheet_name}'")
                return first_sheet_name
            
            # Final fallback to configured name
            print(f"DEBUG: No sheets found, using configured name: '{configured_name}'")
            return configured_name
            
        except Exception as e:
            print(f"DEBUG: Error getting worksheet name: {e}")
            return configured_name
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        await self.common_handlers.send_long_message_with_keyboard(message, text, reply_markup)
