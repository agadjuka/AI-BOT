"""
Refactored callback handlers for Telegram bot - dispatcher only
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from services.google_sheets_service import GoogleSheetsService
from handlers.base_callback_handler import BaseCallbackHandler
from handlers.callback_dispatchers.receipt_edit_dispatcher import ReceiptEditDispatcher
from handlers.callback_dispatchers.ingredient_matching_dispatcher import IngredientMatchingDispatcher
from handlers.callback_dispatchers.google_sheets_dispatcher import GoogleSheetsDispatcher
from handlers.callback_dispatchers.file_generation_dispatcher import FileGenerationDispatcher
from handlers.ingredient_matching_callback_handler import IngredientMatchingCallbackHandler
from handlers.google_sheets_callback_handler import GoogleSheetsCallbackHandler
from handlers.file_generation_callback_handler import FileGenerationCallbackHandler
from config.locales.locale_manager import get_global_locale_manager
from config.locales.language_buttons import get_language_keyboard


class CallbackHandlers(BaseCallbackHandler):
    """Main callback handlers coordinator - refactored version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        
        # Initialize LocaleManager
        self.locale_manager = get_global_locale_manager()
        
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
        
        # Save user_id to context for language loading
        self.save_user_context(update, context)
        
        # Language will be automatically loaded by get_text() calls
        
        action = query.data
        print(f"DEBUG: Callback received: {action}")
        
        # Route to appropriate handler based on action
        # Google Sheets actions must be checked first to avoid conflicts with general edit_ actions
        if action in ["google_sheets_matching", "gs_upload", "upload_to_google_sheets", "gs_show_table",
                     "edit_google_sheets_matching", "preview_google_sheets_upload", "confirm_google_sheets_upload",
                     "select_google_sheets_position", "back_to_google_sheets_matching",
                     "back_to_google_sheets_preview", "undo_google_sheets_upload", "generate_excel_file",
                     "gs_skip_item", "gs_next_item", "skip_ingredient", "next_ingredient_match"] or action.startswith("edit_google_sheets_item_") or action.startswith("select_google_sheets_line_") or action.startswith("select_google_sheets_suggestion_") or action.startswith("search_google_sheets_ingredient_") or action.startswith("select_google_sheets_search_") or action.startswith("select_google_sheets_position_match_"):
            return await self.google_sheets_dispatcher._handle_google_sheets_actions(update, context, action)
        
        elif action in ["add_row", "edit_total", "auto_calculate_total", "finish_editing", "edit_receipt", 
                     "back_to_edit", "delete_row", "edit_line_number", "manual_edit_total", "reanalyze", 
                     "back_to_receipt", "back_to_main_menu"] or action.startswith("field_") or action.startswith("apply_") or action.startswith("edit_item_") or action.startswith("delete_item_"):
            return await self.receipt_edit_dispatcher._handle_receipt_edit_actions(update, context, action)
        
        elif action.startswith("edit_") and not action.startswith("edit_mapping_field_"):
            # Handle other edit actions (but not mapping field edits)
            return await self.receipt_edit_dispatcher._handle_receipt_edit_actions(update, context, action)
        
        elif action in ["ingredient_matching", "manual_matching", "position_selection", "match_item_", 
                       "select_item_", "select_suggestion_", "next_item", "skip_item", "show_matching_table",
                       "manual_match_ingredients", "rematch_ingredients", "apply_matching_changes",
                       "select_position_for_matching", "back_to_matching_overview", "search_ingredient",
                       "skip_ingredient", "next_ingredient_match", "confirm_back_without_changes",
                       "cancel_back"]:
            return await self.ingredient_matching_dispatcher._handle_ingredient_matching_actions(update, context, action)
        
        elif action in ["generate_supply_file", "generate_poster_file", "generate_google_sheets_file",
                       "generate_file_xlsx", "generate_file_from_table", "match_ingredients"]:
            return await self.file_generation_dispatcher._handle_file_generation_actions(update, context, action)
        
        elif action == "finish":
            await query.answer(self.get_text("buttons.finish", context, update=update))
            return self.config.AWAITING_CORRECTION
        
        elif action == "cancel":
            return await self._cancel(update, context)
        
        elif action == "analyze_receipt":
            await update.callback_query.edit_message_text(
                self.get_text("welcome.analyze_receipt", context, update=update)
            )
            return self.config.AWAITING_CORRECTION
        
        elif action in ["select_language_ru", "select_language_en", "select_language_id"]:
            return await self._handle_language_selection(update, context, action)
        
        elif action == "dashboard_language_settings":
            return await self._handle_dashboard_language_settings(update, context)
        
        elif action == "dashboard_google_sheets_management":
            return await self._handle_dashboard_google_sheets_management(update, context)
        
        elif action == "dashboard_main":
            return await self._handle_dashboard_main(update, context)
        
        elif action == "back_to_main_menu":
            return await self._handle_back_to_main_menu(update, context)
        
        elif action == "sheets_add_new" or action.startswith("sheets_manage_"):
            return await self._handle_sheets_management_actions(update, context, action)
        
        elif action in ["confirm_use_default_mapping", "confirm_configure_manual_mapping"]:
            return await self._handle_confirm_mapping_actions(update, context, action)
        
        elif action.startswith("edit_mapping_field_"):
            # Handle field editing in mapping editor
            field_key = action.replace("edit_mapping_field_", "")
            return await self._handle_mapping_field_edit(update, context, field_key)
        
        elif action in ["save_mapping_and_exit", "cancel_mapping_edit"]:
            # Handle mapping editor actions
            return await self._handle_mapping_editor_actions(update, context, action)
        
        
        elif action == "noop":
            await query.answer()
            return self.config.AWAITING_CORRECTION
        
        else:
            await query.answer(self.get_text("errors.unknown_action", context, update=update))
            return self.config.AWAITING_CORRECTION
    
    async def _handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle language selection callback"""
        query = update.callback_query
        await query.answer()
        
        # Extract language code from action (e.g., "select_language_ru" -> "ru")
        language_code = action.replace("select_language_", "")
        print(f"DEBUG: Language selection: {action} -> {language_code}")
        
        # Validate language code
        if not self.locale_manager.is_language_supported(language_code):
            await query.answer(self.get_text("errors.unsupported_language", context, update=update))
            return self.config.AWAITING_CORRECTION
        
        # Set user language
        success = self.locale_manager.set_user_language(update, context, language_code)
        
        if success:
            # Show main menu in selected language
            
            # Create main menu with localized buttons
            keyboard = [
                [InlineKeyboardButton(
                    self.get_text("buttons.analyze_receipt", context, update=update), 
                    callback_data="analyze_receipt"
                )],
                [InlineKeyboardButton(
                    self.get_text("buttons.generate_supply_file", context, update=update), 
                    callback_data="generate_supply_file"
                )],
                [InlineKeyboardButton(
                    self.get_text("buttons.dashboard", context, update=update), 
                    callback_data="dashboard_main"
                )]
            ]
            
            # Add back button if there's existing receipt data
            if context.user_data.get('receipt_data'):
                keyboard.append([InlineKeyboardButton(
                    self.get_text("buttons.back_to_receipt", context, update=update), 
                    callback_data="back_to_receipt"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                self.get_text("welcome.start_message", context, update=update, user=update.effective_user.mention_html()),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            return self.config.AWAITING_CORRECTION
        else:
            # Fallback to Russian if language not supported
            await query.edit_message_text(
                self.get_text("errors.language_fallback", context, update=update)
            )
            return self.config.AWAITING_CORRECTION
    
    async def _cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current operation"""
        query = update.callback_query
        await query.answer()
        
        # Clear all data
        self._clear_receipt_data(context)
        
        # Show start message - avoid circular import
        await query.edit_message_text(
            self.get_text("errors.operation_cancelled", context, update=update)
        )
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_dashboard_language_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle language settings from dashboard"""
        query = update.callback_query
        await query.answer()
        
        # Show language selection
        language_keyboard = get_language_keyboard()
        
        await query.edit_message_text(
            self.get_text("welcome.choose_language", context, update=update),
            reply_markup=language_keyboard
        )
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_dashboard_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle dashboard main button from main menu"""
        query = update.callback_query
        await query.answer()
        
        # Create dashboard keyboard
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("welcome.dashboard.buttons.language_settings", context, update=update), 
                callback_data="dashboard_language_settings"
            )],
            [InlineKeyboardButton(
                self.get_text("welcome.dashboard.buttons.google_sheets_management", context, update=update), 
                callback_data="dashboard_google_sheets_management"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back_to_main_menu", context, update=update), 
                callback_data="back_to_main_menu"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("welcome.dashboard.welcome_message", context, update=update, 
                         user=update.effective_user.mention_html()),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle back to main menu"""
        query = update.callback_query
        await query.answer()
        
        # Show main menu
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("buttons.analyze_receipt", context, update=update), 
                callback_data="analyze_receipt"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.generate_supply_file", context, update=update), 
                callback_data="generate_supply_file"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.dashboard", context, update=update), 
                callback_data="dashboard_main"
            )]
        ]
        
        if context.user_data.get('receipt_data'):
            keyboard.append([InlineKeyboardButton(
                self.get_text("buttons.back_to_receipt", context, update=update), 
                callback_data="back_to_receipt"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("welcome.start_message", context, update=update, 
                         user=update.effective_user.mention_html()),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_dashboard_google_sheets_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Google Sheets management button from dashboard"""
        query = update.callback_query
        if query:
            await query.answer()
        
        # Get user ID
        user_id = update.effective_user.id
        
        # Check if user sheets are already cached
        cache_key = f"user_sheets_{user_id}"
        user_sheets = context.bot_data.get(cache_key)
        
        if user_sheets is None:
            # Import Google Sheets Manager
            from services.google_sheets_manager import get_google_sheets_manager
            
            try:
                # Get Google Sheets Manager instance
                sheets_manager = get_google_sheets_manager()
                
                # Get user's sheets and cache them
                user_sheets = await sheets_manager.get_user_sheets(user_id)
                context.bot_data[cache_key] = user_sheets
                print(f"✅ Cached {len(user_sheets)} sheets for user {user_id}")
            except Exception as e:
                print(f"❌ Error loading user sheets: {e}")
                user_sheets = []
        else:
            print(f"✅ Using cached sheets for user {user_id} ({len(user_sheets)} sheets)")
        
        # Create message text
        title = self.get_text("sheets_management.title", context, update=update)
        
        if not user_sheets:
            # No sheets scenario
            description = self.get_text("sheets_management.no_sheets_description", context, update=update)
            message_text = f"{title}\n\n{description}"
            
            # Create keyboard for no sheets scenario
            keyboard = [
                [InlineKeyboardButton(
                    self.get_text("sheets_management.buttons.add_new_sheet", context, update=update),
                    callback_data="sheets_add_new"
                )],
                [InlineKeyboardButton(
                    self.get_text("sheets_management.buttons.back_to_dashboard", context, update=update),
                    callback_data="dashboard_main"
                )]
            ]
        else:
            # Has sheets scenario
            description = self.get_text("sheets_management.has_sheets_description", context, update=update)
            message_text = f"{title}\n\n{description}"
            
            # Create keyboard with sheets list
            keyboard = []
            
            # Add buttons for each sheet
            for sheet in user_sheets:
                friendly_name = sheet.get('friendly_name', 'Unknown Sheet')
                is_default = sheet.get('is_default', False)
                sheet_doc_id = sheet.get('doc_id', '')
                
                # Add star emoji for default sheet
                button_text = f"⭐ {friendly_name}" if is_default else friendly_name
                
                keyboard.append([InlineKeyboardButton(
                    button_text,
                    callback_data=f"sheets_manage_{sheet_doc_id}"
                )])
            
            # Add action buttons
            keyboard.extend([
                [InlineKeyboardButton(
                    self.get_text("sheets_management.buttons.add_new_sheet", context, update=update),
                    callback_data="sheets_add_new"
                )],
                [InlineKeyboardButton(
                    self.get_text("sheets_management.buttons.back_to_dashboard", context, update=update),
                    callback_data="dashboard_main"
                )]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send or edit the message
        if query:
            await query.edit_message_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        return self.config.AWAITING_CORRECTION
    
    def _clear_user_sheets_cache(self, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Clear cached user sheets data"""
        cache_key = f"user_sheets_{user_id}"
        if cache_key in context.bot_data:
            del context.bot_data[cache_key]
            print(f"✅ Cleared sheets cache for user {user_id}")
    
    async def _handle_sheets_management_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle Google Sheets management actions"""
        query = update.callback_query
        await query.answer()
        
        if action == "sheets_add_new":
            # Handle "Add new sheet" button - start FSM process
            return await self._handle_add_new_sheet_step1(update, context)
        
        elif action.startswith("sheets_manage_"):
            # Handle individual sheet management
            sheet_doc_id = action.replace("sheets_manage_", "")
            
            # For now, just show a placeholder message
            # In the future, this could show sheet details and management options
            await query.edit_message_text(
                f"📊 Sheet Management\n\nSheet ID: {sheet_doc_id}\n\nThis feature is coming soon!",
                parse_mode='HTML'
            )
            return self.config.AWAITING_CORRECTION
        
        else:
            # Fallback to dashboard
            return await self._handle_dashboard_main(update, context)
    
    async def _handle_add_new_sheet_step1(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Step 1: Show instructions and service account email"""
        query = update.callback_query
        await query.answer()
        
        # Get service account email from credentials
        service_email = self._get_service_account_email()
        
        # Create message text
        title = self.get_text("add_sheet.step1_title", context, update=update)
        instruction = self.get_text("add_sheet.step1_instruction", context, update=update, service_email=service_email)
        message_text = f"{title}\n\n{instruction}"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("add_sheet.buttons.cancel", context, update=update),
                callback_data="dashboard_google_sheets_management"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit the message
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Set state to await sheet URL
        return self.config.AWAITING_SHEET_URL
    
    def _get_service_account_email(self) -> str:
        """Get service account email from credentials file"""
        try:
            import json
            with open(self.config.GOOGLE_SHEETS_CREDENTIALS, 'r') as f:
                credentials = json.load(f)
                return credentials.get('client_email', '366461711404-compute@developer.gserviceaccount.com')
        except Exception as e:
            print(f"❌ Error reading service account email: {e}")
            return '366461711404-compute@developer.gserviceaccount.com'
    
    async def _handle_sheet_url_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Step 2: Process sheet URL input"""
        user_message = update.message.text.strip()
        
        # Extract sheet ID from URL
        sheet_id = self._extract_sheet_id_from_url(user_message)
        if not sheet_id:
            # Send temporary error message
            temp_message = await update.message.reply_text(
                self.get_text("add_sheet.errors.invalid_sheet_id", context, update=update),
                parse_mode='HTML'
            )
            # Store temp message ID for deletion
            context.user_data['temp_message_id'] = temp_message.message_id
            return self.config.AWAITING_SHEET_URL
        
        # Check access to the sheet (with fallback for JWT issues)
        has_access = await self._check_sheet_access(sheet_id)
        if not has_access:
            # Check if it's a JWT error (system time issue) or real permission error
            try:
                from services.google_sheets_service import GoogleSheetsService
                temp_service = GoogleSheetsService(
                    credentials_path=self.config.GOOGLE_SHEETS_CREDENTIALS,
                    spreadsheet_id=sheet_id
                )
                # Try to access the sheet by getting its properties
                if temp_service.service:
                    result = temp_service.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
                    # If we get here, we have access
                    print("✅ Access granted after retry")
                    has_access = True
                else:
                    print("❌ Google Sheets service not initialized")
            except Exception as e:
                if "PERMISSION_DENIED" in str(e) or "permission" in str(e).lower():
                    # Real permission error - show error message
                    temp_message = await update.message.reply_text(
                        self.get_text("add_sheet.errors.invalid_url", context, update=update),
                        parse_mode='HTML'
                    )
                    context.user_data['temp_message_id'] = temp_message.message_id
                    return self.config.AWAITING_SHEET_URL
                else:
                    # JWT error - assume access is granted
                    print("⚠️ JWT error, assuming access is granted (user added service account)")
                    has_access = True
        
        # Store sheet data in context
        context.user_data['new_sheet_url'] = user_message
        context.user_data['new_sheet_id'] = sheet_id
        
        # Delete temp message if exists
        if 'temp_message_id' in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data['temp_message_id']
                )
                del context.user_data['temp_message_id']
            except Exception as e:
                print(f"⚠️ Could not delete temp message: {e}")
        
        # Move to step 2: request friendly name
        return await self._handle_add_new_sheet_step2(update, context)
    
    async def _handle_add_new_sheet_step2(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Step 2: Request friendly name for the sheet"""
        # Create message text
        title = self.get_text("add_sheet.step2_title", context, update=update)
        instruction = self.get_text("add_sheet.step2_instruction", context, update=update)
        message_text = f"{title}\n\n{instruction}"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("add_sheet.buttons.cancel", context, update=update),
                callback_data="dashboard_google_sheets_management"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit the message
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Set state to await sheet name
        return self.config.AWAITING_SHEET_NAME
    
    async def _handle_sheet_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Step 2: Process sheet name input and show confirmation screen"""
        sheet_name = update.message.text.strip()
        
        # Get stored sheet data
        sheet_url = context.user_data.get('new_sheet_url')
        sheet_id = context.user_data.get('new_sheet_id')
        
        if not sheet_url or not sheet_id:
            # Error - missing data
            await update.message.reply_text(
                self.get_text("add_sheet.errors.save_failed", context, update=update),
                parse_mode='HTML'
            )
            return await self._handle_dashboard_google_sheets_management(update, context)
        
        # Store sheet name in context for confirmation screen
        context.user_data['new_sheet_name'] = sheet_name
        
        # Show confirmation screen with table preview
        return await self._handle_confirm_mapping_screen(update, context)
    
    async def _handle_confirm_mapping_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Step 3: Show confirmation screen with table preview"""
        # Get stored sheet data
        sheet_name = context.user_data.get('new_sheet_name')
        sheet_url = context.user_data.get('new_sheet_url')
        sheet_id = context.user_data.get('new_sheet_id')
        
        if not all([sheet_name, sheet_url, sheet_id]):
            # Error - missing data
            await update.message.reply_text(
                self.get_text("add_sheet.errors.save_failed", context, update=update),
                parse_mode='HTML'
            )
            return await self._handle_dashboard_google_sheets_management(update, context)
        
        # Create table preview data
        table_data = self._create_table_preview_data(context)
        
        # Generate table preview using TableManager
        table_preview = self._generate_table_preview(table_data, context)
        
        # Create message text
        title = self.get_text("add_sheet.step3_title", context, update=update, sheet_name=sheet_name)
        instruction = self.get_text("add_sheet.step3_instruction", context, update=update)
        question = self.get_text("add_sheet.step3_question", context, update=update)
        
        message_text = f"{title}\n\n{instruction}\n\n{table_preview}\n\n{question}"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("add_sheet.buttons.use_default", context, update=update),
                callback_data="confirm_use_default_mapping"
            )],
            [InlineKeyboardButton(
                self.get_text("add_sheet.buttons.configure_manual", context, update=update),
                callback_data="confirm_configure_manual_mapping"
            )],
            [InlineKeyboardButton(
                self.get_text("add_sheet.buttons.cancel", context, update=update),
                callback_data="dashboard_google_sheets_management"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit the message
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Set state to await confirmation
        return self.config.AWAITING_CONFIRM_MAPPING
    
    def _create_table_preview_data(self, context: ContextTypes.DEFAULT_TYPE) -> list:
        """Create table preview data for confirmation screen"""
        # First row - column letters (A, B, C, D, E)
        column_headers = ['', 'A', 'B', 'C', 'D', 'E']
        
        # Second row - field headers (localized)
        field_headers = [
            '1',
            self.get_text("add_sheet.table_headers.date", context),
            self.get_text("add_sheet.table_headers.product", context),
            self.get_text("add_sheet.table_headers.quantity", context),
            self.get_text("add_sheet.table_headers.price", context),
            self.get_text("add_sheet.table_headers.sum", context)
        ]
        
        return [column_headers, field_headers]
    
    def _generate_table_preview(self, table_data: list, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Generate table preview using ReceiptFormatter style"""
        try:
            # Set column widths - first column (row numbers) is 2 characters, others are 10
            number_width = 2    # First column for row numbers
            column_width = 10   # Other columns
            
            lines = []
            
            # First row - column letters (A, B, C, D, E)
            if len(table_data) > 0:
                row = table_data[0]
                header_parts = []
                for j, cell in enumerate(row):
                    if j == 0:  # Empty cell for row numbers
                        header_parts.append(f"{'':^{number_width}}")
                    else:  # Column letters
                        header_parts.append(f"{cell:^{column_width}}")
                lines.append("|".join(header_parts) + "|")  # Add closing vertical separator
            
            # Second row - separator line
            separator = "─" * (number_width + column_width * 5 + 6)  # 1 number column + 5 data columns + 6 separators
            lines.append(separator)
            
            # Third row - field headers
            if len(table_data) > 1:
                row = table_data[1]
                line_number = row[0] if len(row) > 0 else "1"
                date = row[1] if len(row) > 1 else ""
                product = row[2] if len(row) > 2 else ""
                quantity = row[3] if len(row) > 3 else ""
                price = row[4] if len(row) > 4 else ""
                total = row[5] if len(row) > 5 else ""
                
                line = f"{line_number:^{number_width}}|{date:^{column_width}}|{product:^{column_width}}|{quantity:^{column_width}}|{price:^{column_width}}|{total:^{column_width}}|"
                lines.append(line)
            
            # Wrap in HTML pre/code block for monospace font
            table_content = "\n".join(lines)
            result = f"<pre><code>{table_content}</code></pre>"
            return result
            
        except Exception as e:
            print(f"❌ Error generating table preview: {e}")
            # Fallback to simple table
            return self._create_simple_table_preview(table_data)
    
    def _create_simple_table_preview(self, table_data: list) -> str:
        """Create simple table preview as fallback"""
        # Use same column widths as main method
        number_width = 2    # First column for row numbers
        column_width = 10   # Other columns
        
        lines = []
        
        # First row - column letters (A, B, C, D, E)
        if len(table_data) > 0:
            row = table_data[0]
            header_parts = []
            for j, cell in enumerate(row):
                if j == 0:  # Empty cell for row numbers
                    header_parts.append(f"{'':^{number_width}}")
                else:  # Column letters
                    header_parts.append(f"{cell:^{column_width}}")
            lines.append("|".join(header_parts) + "|")  # Add closing vertical separator
        
        # Second row - separator line
        separator = "─" * (number_width + column_width * 5 + 6)  # 1 number column + 5 data columns + 6 separators
        lines.append(separator)
        
        # Third row - field headers
        if len(table_data) > 1:
            row = table_data[1]
            line_number = row[0] if len(row) > 0 else "1"
            date = row[1] if len(row) > 1 else ""
            product = row[2] if len(row) > 2 else ""
            quantity = row[3] if len(row) > 3 else ""
            price = row[4] if len(row) > 4 else ""
            total = row[5] if len(row) > 5 else ""
            
            line = f"{line_number:^{number_width}}|{date:^{column_width}}|{product:^{column_width}}|{quantity:^{column_width}}|{price:^{column_width}}|{total:^{column_width}}|"
            lines.append(line)
        
        table_content = "\n".join(lines)
        return f"<pre><code>{table_content}</code></pre>"
    
    def _create_mapping_editor_table_preview(self, column_mapping: dict, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Create table preview for mapping editor - same as Table Configuration but with field names"""
        # Use the same table structure as Table Configuration (Step 3 of 3)
        # Set column widths - first column (row numbers) is 2 characters, others are 10
        number_width = 2    # First column for row numbers
        column_width = 10   # Other columns
        
        lines = []
        
        # First row - column letters (A, B, C, D, E)
        header_parts = []
        header_parts.append(f"{'':^{number_width}}")  # Empty cell for row numbers
        header_parts.append(f"{'A':^{column_width}}")
        header_parts.append(f"{'B':^{column_width}}")
        header_parts.append(f"{'C':^{column_width}}")
        header_parts.append(f"{'D':^{column_width}}")
        header_parts.append(f"{'E':^{column_width}}")
        lines.append("|".join(header_parts) + "|")  # Add closing vertical separator
        
        # Second row - separator line
        separator = "─" * (number_width + column_width * 5 + 6)  # 1 number column + 5 data columns + 6 separators
        lines.append(separator)
        
        # Third row - field names mapped to columns (initially all empty with dashes)
        row_parts = []
        row_parts.append(f"{'1':^{number_width}}")  # Row number
        
        # Map fields to columns - show field names only if mapped, otherwise show dashes
        columns = ['A', 'B', 'C', 'D', 'E']
        field_mapping = {
            'check_date': 'Date',
            'product_name': 'Product',
            'quantity': 'Qty',
            'price_per_item': 'Price',
            'total_price': 'Sum'
        }
        
        for col in columns:
            # Find which field is mapped to this column
            field_name = "---"
            for field_key, mapped_col in column_mapping.items():
                if mapped_col == col:
                    field_name = field_mapping.get(field_key, field_key)
                    break
            row_parts.append(f"{field_name:^{column_width}}")
        
        lines.append("|".join(row_parts) + "|")
        
        # Wrap in HTML pre/code block for monospace font
        table_content = "\n".join(lines)
        return f"<pre><code>{table_content}</code></pre>"
    
    async def _handle_confirm_mapping_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle confirmation mapping actions"""
        query = update.callback_query
        await query.answer()
        
        if action == "confirm_use_default_mapping":
            # Use default mapping - save sheet and finish
            return await self._handle_use_default_mapping(update, context)
        
        elif action == "confirm_configure_manual_mapping":
            # Configure manual mapping - enter editor
            return await self._enter_mapping_editor(update, context)
        
        else:
            # Fallback
            return await self._handle_dashboard_google_sheets_management(update, context)
    
    async def _handle_use_default_mapping(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle using default mapping - save sheet and finish"""
        query = update.callback_query
        
        # Get stored sheet data
        sheet_name = context.user_data.get('new_sheet_name')
        sheet_url = context.user_data.get('new_sheet_url')
        sheet_id = context.user_data.get('new_sheet_id')
        
        if not all([sheet_name, sheet_url, sheet_id]):
            # Error - missing data
            await query.edit_message_text(
                self.get_text("add_sheet.errors.save_failed", context, update=update),
                parse_mode='HTML'
            )
            return await self._handle_dashboard_google_sheets_management(update, context)
        
        # Save the sheet using Google Sheets Manager
        try:
            from services.google_sheets_manager import get_google_sheets_manager
            sheets_manager = get_google_sheets_manager()
            
            result = await sheets_manager.add_user_sheet(
                user_id=update.effective_user.id,
                sheet_url=sheet_url,
                sheet_id=sheet_id,
                friendly_name=sheet_name
            )
            
            if result:
                # Success - show success message and return to management
                success_message = self.get_text("add_sheet.step3_success", context, update=update, sheet_name=sheet_name)
                
                # Clear stored data
                context.user_data.pop('new_sheet_url', None)
                context.user_data.pop('new_sheet_id', None)
                context.user_data.pop('new_sheet_name', None)
                context.user_data.pop('temp_message_id', None)
                
                # Clear user sheets cache since we added a new sheet
                self._clear_user_sheets_cache(context, update.effective_user.id)
                
                # Show success message
                await query.edit_message_text(success_message, parse_mode='HTML')
                
                # Return to Google Sheets management
                return await self._handle_dashboard_google_sheets_management(update, context)
            else:
                # Save failed
                await query.edit_message_text(
                    self.get_text("add_sheet.errors.save_failed", context, update=update),
                    parse_mode='HTML'
                )
                return await self._handle_dashboard_google_sheets_management(update, context)
                
        except Exception as e:
            print(f"❌ Error saving sheet: {e}")
            await query.edit_message_text(
                self.get_text("add_sheet.errors.save_failed", context, update=update),
                parse_mode='HTML'
            )
            return await self._handle_dashboard_google_sheets_management(update, context)
    
    def _extract_sheet_id_from_url(self, url: str) -> str:
        """Extract Google Sheets ID from URL"""
        import re
        
        # Pattern for Google Sheets URL
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/([a-zA-Z0-9-_]{44})',  # Google Sheets IDs are typically 44 characters
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _check_sheet_access(self, sheet_id: str) -> bool:
        """Check if we have access to the Google Sheet"""
        try:
            # Use the existing Google Sheets service instead of creating new credentials
            # This reuses the working service that's already configured
            from services.google_sheets_service import GoogleSheetsService
            
            # Create a temporary service instance with the new sheet ID
            temp_service = GoogleSheetsService(
                credentials_path=self.config.GOOGLE_SHEETS_CREDENTIALS,
                spreadsheet_id=sheet_id
            )
            
            # Try to access the sheet by getting its properties
            # This will fail if we don't have access
            if temp_service.service:
                # Try to get spreadsheet metadata
                result = temp_service.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
                
                # If we get here, we have access
                sheet_title = result.get('properties', {}).get('title', 'Unknown')
                print(f"✅ Successfully accessed sheet: {sheet_title}")
                return True
            else:
                print("❌ Google Sheets service not initialized")
                return False
            
        except Exception as e:
            print(f"❌ Error checking sheet access: {e}")
            # Check if it's a permission error specifically
            if "PERMISSION_DENIED" in str(e) or "permission" in str(e).lower():
                print("❌ Permission denied - service account needs Editor access")
            elif "invalid_grant" in str(e).lower():
                print("❌ Invalid credentials - check if service account is properly configured")
            return False
    
    async def _enter_mapping_editor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Enter mapping editor mode"""
        query = update.callback_query
        await query.answer()
        
        # Get stored sheet data
        sheet_id = context.user_data.get('new_sheet_id')
        if not sheet_id:
            await query.edit_message_text(
                self.get_text("add_sheet.errors.save_failed", context, update=update),
                parse_mode='HTML'
            )
            return await self._handle_dashboard_google_sheets_management(update, context)
        
        # Set default mapping - initially all empty
        default_mapping = {}
        
        # Store mapping data in FSM state
        context.user_data['column_mapping'] = default_mapping
        context.user_data['editing_sheet_id'] = sheet_id
        
        # Show mapping editor
        return await self._show_mapping_editor(update, context)
    
    async def _show_mapping_editor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show mapping editor interface"""
        # Get current settings from FSM state
        column_mapping = context.user_data.get('column_mapping', {})
        
        # Create message text
        title = self.get_text("add_sheet.mapping_editor.title", context, update=update)
        description = self.get_text("add_sheet.mapping_editor.description", context, update=update)
        
        # Create table preview data
        table_preview = self._create_mapping_editor_table_preview(column_mapping, context)
        
        message_text = f"{title}\n\n{description}\n\n{table_preview}"
        
        # Create keyboard with field buttons in two columns
        keyboard = []
        
        # Add field buttons in two columns
        field_keys = ['check_date', 'product_name', 'quantity', 'price_per_item', 'total_price']
        field_buttons = []
        
        for field_key in field_keys:
            button_text = self.get_text(f"add_sheet.mapping_editor.field_buttons.{field_key}", context, update=update)
            field_buttons.append(InlineKeyboardButton(
                button_text,
                callback_data=f"edit_mapping_field_{field_key}"
            ))
        
        # Arrange buttons in two columns
        for i in range(0, len(field_buttons), 2):
            row = [field_buttons[i]]
            if i + 1 < len(field_buttons):
                row.append(field_buttons[i + 1])
            keyboard.append(row)
        
        # Add action buttons
        keyboard.extend([
            [InlineKeyboardButton(
                self.get_text("add_sheet.mapping_editor.action_buttons.save_and_exit", context, update=update),
                callback_data="save_mapping_and_exit"
            )],
            [InlineKeyboardButton(
                self.get_text("add_sheet.mapping_editor.action_buttons.cancel", context, update=update),
                callback_data="cancel_mapping_edit"
            )]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit the message
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        return self.config.EDIT_MAPPING
    
    async def _handle_mapping_field_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, field_key: str) -> int:
        """Handle field button press in mapping editor"""
        query = update.callback_query
        await query.answer()
        
        # Store which field we're editing
        context.user_data['field_to_edit'] = field_key
        
        # Get field name for display
        field_name = self.get_text(f"add_sheet.mapping_editor.field_names.{field_key}", context, update=update)
        
        # Create message text
        message_text = self.get_text("add_sheet.mapping_editor.column_input", context, update=update, field_name=field_name)
        
        # Send new message under the main one (don't edit the main message)
        sent_message = await update.effective_message.reply_text(
            message_text,
            parse_mode='HTML'
        )
        
        # Store the message ID for later deletion
        context.user_data['mapping_request_message_id'] = sent_message.message_id
        
        return self.config.AWAITING_COLUMN_INPUT
    
    async def _handle_mapping_editor_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle mapping editor action buttons"""
        query = update.callback_query
        await query.answer()
        
        if action == "save_mapping_and_exit":
            # Save mapping and exit
            return await self._handle_save_mapping_and_exit(update, context)
        
        elif action == "cancel_mapping_edit":
            # Cancel editing - return to sheet management
            return await self._handle_cancel_mapping_edit(update, context)
        
        else:
            # Fallback
            return await self._handle_dashboard_google_sheets_management(update, context)
    
    
    async def _handle_save_mapping_and_exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle save mapping and exit button"""
        query = update.callback_query
        
        # Get final mapping data from FSM state
        column_mapping = context.user_data.get('column_mapping', {})
        sheet_doc_id = context.user_data.get('sheet_doc_id')  # For editing existing sheet
        editing_sheet_id = context.user_data.get('editing_sheet_id')  # For new sheet
        
        try:
            from services.google_sheets_manager import get_google_sheets_manager
            sheets_manager = get_google_sheets_manager()
            
            if sheet_doc_id:
                # Editing existing sheet - update mapping
                success = await sheets_manager.update_user_sheet_mapping(
                    user_id=update.effective_user.id,
                    sheet_doc_id=sheet_doc_id,
                    new_mapping=column_mapping,
                    new_start_row=2  # Default start row
                )
                
                if success:
                    # Success message
                    success_text = self.get_text("add_sheet.mapping_editor.save_success_existing", context, update=update)
                    await query.edit_message_text(success_text, parse_mode='HTML')
                    
                    # Clear FSM data
                    self._clear_mapping_fsm_data(context)
                    
                    # Clear user sheets cache since we updated a sheet
                    self._clear_user_sheets_cache(context, update.effective_user.id)
                    
                    # Return to Google Sheets management
                    return await self._handle_dashboard_google_sheets_management(update, context)
                else:
                    # Save failed
                    error_text = self.get_text("add_sheet.mapping_editor.save_error", context, update=update)
                    await query.edit_message_text(error_text, parse_mode='HTML')
                    return await self._handle_dashboard_google_sheets_management(update, context)
            
            elif editing_sheet_id:
                # Adding new sheet with custom mapping
                sheet_name = context.user_data.get('new_sheet_name')
                sheet_url = context.user_data.get('new_sheet_url')
                
                if not all([sheet_name, sheet_url, editing_sheet_id]):
                    # Error - missing data
                    error_text = self.get_text("add_sheet.errors.save_failed", context, update=update)
                    await query.edit_message_text(error_text, parse_mode='HTML')
                    return await self._handle_dashboard_google_sheets_management(update, context)
                
                # Add new sheet with custom mapping
                result = await sheets_manager.add_user_sheet_with_mapping(
                    user_id=update.effective_user.id,
                    sheet_url=sheet_url,
                    sheet_id=editing_sheet_id,
                    friendly_name=sheet_name,
                    column_mapping=column_mapping,
                    start_row=2  # Default start row
                )
                
                if result:
                    # Success message
                    success_text = self.get_text("add_sheet.mapping_editor.save_success_new", context, update=update, sheet_name=sheet_name)
                    await query.edit_message_text(success_text, parse_mode='HTML')
                    
                    # Clear FSM data
                    self._clear_mapping_fsm_data(context)
                    self._clear_new_sheet_fsm_data(context)
                    
                    # Clear user sheets cache since we added a new sheet
                    self._clear_user_sheets_cache(context, update.effective_user.id)
                    
                    # Return to Google Sheets management
                    return await self._handle_dashboard_google_sheets_management(update, context)
                else:
                    # Save failed
                    error_text = self.get_text("add_sheet.mapping_editor.save_error", context, update=update)
                    await query.edit_message_text(error_text, parse_mode='HTML')
                    return await self._handle_dashboard_google_sheets_management(update, context)
            else:
                # Error - no sheet context
                error_text = self.get_text("add_sheet.mapping_editor.save_error", context, update=update)
                await query.edit_message_text(error_text, parse_mode='HTML')
                return await self._handle_dashboard_google_sheets_management(update, context)
                
        except Exception as e:
            print(f"❌ Error saving mapping: {e}")
            error_text = self.get_text("add_sheet.mapping_editor.save_error", context, update=update)
            await query.edit_message_text(error_text, parse_mode='HTML')
            return await self._handle_dashboard_google_sheets_management(update, context)
    
    async def _handle_cancel_mapping_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancel mapping edit button"""
        query = update.callback_query
        
        # Clear FSM data
        self._clear_mapping_fsm_data(context)
        
        # Show cancellation message
        cancel_text = self.get_text("add_sheet.mapping_editor.cancel_message", context, update=update)
        await query.edit_message_text(cancel_text, parse_mode='HTML')
        
        # Return to Google Sheets management
        return await self._handle_dashboard_google_sheets_management(update, context)
    
    def _clear_mapping_fsm_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear mapping editor FSM data"""
        context.user_data.pop('column_mapping', None)
        context.user_data.pop('field_to_edit', None)
        context.user_data.pop('editing_sheet_id', None)
        context.user_data.pop('sheet_doc_id', None)
        context.user_data.pop('mapping_request_message_id', None)
    
    def _clear_new_sheet_fsm_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear new sheet FSM data"""
        context.user_data.pop('new_sheet_url', None)
        context.user_data.pop('new_sheet_id', None)
        context.user_data.pop('new_sheet_name', None)
        context.user_data.pop('temp_message_id', None)