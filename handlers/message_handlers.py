"""
Message handlers for Telegram bot - Refactored version
"""
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from handlers.base_message_handler import BaseMessageHandler
from handlers.photo_handler import PhotoHandler
from handlers.input_handler import InputHandler
from handlers.ingredient_matching_input_handler import IngredientMatchingInputHandler
from handlers.google_sheets_input_handler import GoogleSheetsInputHandler
from handlers.ingredients_file_handler import IngredientsFileHandler
from handlers.ingredients_text_handler import IngredientsTextHandler
from utils.common_handlers import CommonHandlers
from utils.access_control import access_check
from config.locales.locale_manager import get_global_locale_manager
from config.locales.language_buttons import get_language_keyboard


class MessageHandlers(BaseMessageHandler):
    """Main message handlers coordinator - refactored version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        
        # Initialize LocaleManager
        self.locale_manager = get_global_locale_manager()
        
        # Initialize specialized handlers
        self.photo_handler = PhotoHandler(config, analysis_service)
        self.input_handler = InputHandler(config, analysis_service)
        self.ingredient_matching_handler = IngredientMatchingInputHandler(config, analysis_service)
        self.google_sheets_handler = GoogleSheetsInputHandler(config, analysis_service)
        self.ingredients_file_handler = IngredientsFileHandler(config, analysis_service)
        self.ingredients_text_handler = IngredientsTextHandler(config, analysis_service)
        self.common_handlers = CommonHandlers(config, analysis_service)
    
    @access_check
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command"""
        print(f"DEBUG: Start command received from user {update.effective_user.id}")
        
        # Check user permissions
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        from utils.role_initializer import check_user_permissions
        from google.cloud import firestore
        
        # Get Firestore instance
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if db:
            permissions = await check_user_permissions(user_id, username, db)
            
            if not permissions['has_access']:
                await update.message.reply_text(
                    "❌ **Access Denied**\n\n"
                    "You don't have permission to use this bot.\n"
                    "Please contact the administrator for access.",
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_DASHBOARD
        
        # Save user_id to context for language loading
        self.save_user_context(update, context)
        
        # Check if user has explicitly set a language (not just default)
        user_id = update.effective_user.id
        stored_language = self.locale_manager.language_service.get_user_language(user_id)
        print(f"DEBUG: Stored language in Firestore: '{stored_language}' for user {user_id}")
        
        if stored_language and self.locale_manager.is_language_supported(stored_language):
            # User has a saved language, show welcome instruction with buttons
            print(f"DEBUG: Using saved language '{stored_language}' for user {user_id}")
            
            # Set language in context
            context.user_data['language'] = stored_language
            
            # Create welcome instruction with localized buttons - explicitly pass language
            keyboard = [
                [InlineKeyboardButton(
                    self.get_text("buttons.personal_dashboard", context, update=update, language=stored_language), 
                    callback_data="dashboard_main"
                )],
                [InlineKeyboardButton(
                    self.get_text("buttons.scan_receipt", context, update=update, language=stored_language), 
                    callback_data="start_new_receipt"
                )]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                self.get_text("welcome.start_instruction", context, update=update, language=stored_language),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # No saved language, show language selection
            print(f"DEBUG: No saved language found for user {user_id}, showing language selection")
            from config.locales.language_buttons import get_language_keyboard
            language_keyboard = get_language_keyboard()
            await update.message.reply_html(
                self.get_text("welcome.choose_language", context, update=update, language='ru'),
                reply_markup=language_keyboard
            )
        
        return self.config.AWAITING_CORRECTION
    
    async def reset_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /reset_language command - reset language and show selection"""
        # Clear language from user_data
        context.user_data.pop('language', None)
        
        # Show language selection
        language_keyboard = get_language_keyboard()
        await update.message.reply_html(
            self.get_text("welcome.choose_language", context, update=update),
            reply_markup=language_keyboard
        )
        return self.config.AWAITING_CORRECTION
    
    async def check_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /check_language command - show current language settings"""
        user_id = update.effective_user.id
        current_language = context.user_data.get('language', 'not set')
        stored_language = self.locale_manager.language_service.get_user_language(user_id)
        
        message = f"🔍 Language Debug Info:\n"
        message += f"Current in context: {current_language}\n"
        message += f"Stored in Firestore: {stored_language or 'not found'}\n"
        message += f"User ID: {user_id}"
        
        await update.message.reply_text(message)
        return self.config.AWAITING_CORRECTION
    
    @access_check
    async def dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /dashboard command - show user dashboard"""
        # Language will be automatically loaded by get_text() calls
        
        # Set anchor message for dashboard
        self.ui_manager.set_anchor(context, update.message.message_id)
        
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
                self.get_text("welcome.dashboard.buttons.ingredients_management", context, update=update), 
                callback_data="ingredients_management"
            )],
            [InlineKeyboardButton(
                self.get_text("welcome.dashboard.buttons.instruction", context, update=update), 
                callback_data="dashboard_instruction"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back_to_main_menu", context, update=update), 
                callback_data="back_to_main_menu"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send dashboard message
        await update.message.reply_html(
            self.get_text("welcome.dashboard.welcome_message", context, update=update, 
                         user=update.effective_user.mention_html()),
            reply_markup=reply_markup
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def admin_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin commands - show admin panel"""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Check if user is admin
        from utils.role_initializer import check_user_permissions
        from google.cloud import firestore
        
        # Get Firestore instance
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not db:
            await update.message.reply_text("❌ Database not available")
            return self.config.AWAITING_DASHBOARD
        
        permissions = await check_user_permissions(user_id, username, db)
        
        if not permissions['is_admin']:
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Create admin keyboard
        keyboard = [
            [InlineKeyboardButton("👥 Manage Whitelist", callback_data="admin_whitelist")],
            [InlineKeyboardButton("👤 User Roles", callback_data="admin_roles")],
            [InlineKeyboardButton("📊 System Status", callback_data="admin_status")],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="dashboard")]
        ]
        
        await update.message.reply_text(
            "🔧 **Admin Panel**\n\n"
            "Select an option to manage the system:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return self.config.AWAITING_DASHBOARD
    
    async def add_to_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle adding user to whitelist"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        from utils.role_initializer import check_user_permissions
        from google.cloud import firestore
        
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not db:
            await update.message.reply_text("❌ Database not available")
            return self.config.AWAITING_DASHBOARD
        
        permissions = await check_user_permissions(user_id, None, db)
        
        if not permissions['is_admin']:
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Get username from message text
        message_text = update.message.text
        if not message_text or len(message_text.split()) < 2:
            await update.message.reply_text(
                "❌ Please provide a username.\n"
                "Usage: `/add_whitelist username`\n"
                "Example: `/add_whitelist john_doe`",
                parse_mode='Markdown'
            )
            return self.config.AWAITING_DASHBOARD
        
        username = message_text.split()[1]
        
        # Add to whitelist
        from services.user_service import get_user_service
        user_service = get_user_service(db)
        
        success = await user_service.add_to_whitelist(username)
        
        if success:
            await update.message.reply_text(f"✅ Added `{username}` to whitelist", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Failed to add `{username}` to whitelist", parse_mode='Markdown')
        
        return self.config.AWAITING_DASHBOARD
    
    async def remove_from_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle removing user from whitelist"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        from utils.role_initializer import check_user_permissions
        from google.cloud import firestore
        
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not db:
            await update.message.reply_text("❌ Database not available")
            return self.config.AWAITING_DASHBOARD
        
        permissions = await check_user_permissions(user_id, None, db)
        
        if not permissions['is_admin']:
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Get username from message text
        message_text = update.message.text
        if not message_text or len(message_text.split()) < 2:
            await update.message.reply_text(
                "❌ Please provide a username.\n"
                "Usage: `/remove_whitelist username`\n"
                "Example: `/remove_whitelist john_doe`",
                parse_mode='Markdown'
            )
            return self.config.AWAITING_DASHBOARD
        
        username = message_text.split()[1]
        
        # Remove from whitelist
        from services.user_service import get_user_service
        user_service = get_user_service(db)
        
        success = await user_service.remove_from_whitelist(username)
        
        if success:
            await update.message.reply_text(f"✅ Removed `{username}` from whitelist", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Failed to remove `{username}` from whitelist", parse_mode='Markdown')
        
        return self.config.AWAITING_DASHBOARD
    
    async def list_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle listing whitelist"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        from utils.role_initializer import check_user_permissions
        from google.cloud import firestore
        
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not db:
            await update.message.reply_text("❌ Database not available")
            return self.config.AWAITING_DASHBOARD
        
        permissions = await check_user_permissions(user_id, None, db)
        
        if not permissions['is_admin']:
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Get whitelist
        from services.user_service import get_user_service
        user_service = get_user_service(db)
        
        whitelist = await user_service.get_whitelist()
        
        if whitelist:
            whitelist_text = "📋 **Whitelisted Users:**\n\n"
            for username in whitelist:
                whitelist_text += f"• `{username}`\n"
        else:
            whitelist_text = "📋 **Whitelist is empty**"
        
        await update.message.reply_text(whitelist_text, parse_mode='Markdown')
        return self.config.AWAITING_DASHBOARD
    
    @access_check
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle photo upload - delegate to photo handler"""
        # Save user_id to context for language loading
        self.save_user_context(update, context)
        return await self.photo_handler.handle_photo(update, context)
    
    async def handle_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user text input - delegate to input handler"""
        return await self.input_handler.handle_user_input(update, context)
    
    async def handle_line_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle line number input for editing - delegate to input handler"""
        return await self.input_handler.handle_line_number_input(update, context)
    
    async def handle_delete_line_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle line number input for deletion - delegate to input handler"""
        return await self.input_handler.handle_delete_line_number_input(update, context)
    
    async def handle_total_edit_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle total sum edit input - delegate to input handler"""
        return await self.input_handler.handle_total_edit_input(update, context)
    
    async def handle_ingredient_matching_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle manual ingredient matching input - delegate to ingredient matching handler"""
        return await self.ingredient_matching_handler.handle_ingredient_matching_input(update, context)
    
    async def handle_column_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle column input for mapping editor - delegate to input handler"""
        return await self.input_handler.handle_column_input(update, context)
    
    async def handle_sheet_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle sheet name input for mapping editor - delegate to input handler"""
        return await self.input_handler.handle_sheet_name_input(update, context)
    
    async def handle_start_row_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle start row input for mapping editor - delegate to input handler"""
        return await self.input_handler.handle_start_row_input(update, context)
    
    async def handle_ingredients_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ingredients file upload - delegate to ingredients file handler"""
        return await self.ingredients_file_handler.handle_ingredients_file_upload(update, context)
    
    async def handle_ingredients_text_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ingredients text upload - delegate to ingredients text handler"""
        return await self.ingredients_text_handler.handle_ingredients_text_upload(update, context)
    
    # Delegate methods to specialized handlers
    async def show_final_report_with_edit_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons - delegate to photo handler"""
        return await self.photo_handler.show_final_report_with_edit_button(update, context)
    
    # Google Sheets methods - delegate to google sheets handler
    async def _handle_google_sheets_ingredient_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle Google Sheets ingredient name search - delegate to google sheets handler"""
        return await self.google_sheets_handler._handle_google_sheets_ingredient_search(update, context, user_input)
    
    async def _handle_google_sheets_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle Google Sheets search mode - delegate to google sheets handler"""
        return await self.google_sheets_handler._handle_google_sheets_search(update, context, user_input)
    
    async def _show_google_sheets_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                               query: str, results: list, selected_line: int):
        """Show Google Sheets search results for position selection - delegate to google sheets handler"""
        return await self.google_sheets_handler._show_google_sheets_search_results(update, context, query, results, selected_line)
    
    async def _show_google_sheets_item_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                    query: str, results: list, item_index: int):
        """Show Google Sheets search results for specific item - delegate to google sheets handler"""
        return await self.google_sheets_handler._show_google_sheets_item_search_results(update, context, query, results, item_index)
    
    # Utility methods that need to be accessible from all handlers
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name if too long - delegate to google sheets handler"""
        return self.google_sheets_handler._truncate_name(name, max_length)
    
    # Methods that need to be shared between handlers
    async def _update_ingredient_matching_after_data_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                           receipt_data, change_type: str = "general") -> None:
        """Update ingredient matching after any data change"""
        try:
            # Get current matching result from context or storage
            matching_result = context.user_data.get('ingredient_matching_result')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if not matching_result:
                # Try to load from storage using old hash
                user_id = update.effective_user.id
                old_receipt_data = context.user_data.get('original_data')
                if old_receipt_data:
                    old_receipt_hash = old_receipt_data.get_receipt_hash()
                    saved_data = self.ingredient_storage.load_matching_result(user_id, old_receipt_hash)
                    if saved_data:
                        matching_result, changed_indices = saved_data
                        # Update context with loaded data
                        context.user_data['ingredient_matching_result'] = matching_result
                        context.user_data['changed_ingredient_indices'] = changed_indices
            
            if not matching_result:
                print(self.locale_manager.get_text("debug.no_matching_result", context, change_type=change_type))
                return
            
            # For different change types, we need different handling
            if change_type == "deletion":
                # This will be handled by the specific deletion function
                return
            elif change_type == "addition":
                # Add a new empty match for the new item
                from models.ingredient_matching import IngredientMatch, MatchStatus
                new_match = IngredientMatch(
                    receipt_item_name=self.locale_manager.get_text("analysis.new_item_name", context),
                    matched_ingredient_name="",
                    matched_ingredient_id="",
                    match_status=MatchStatus.NO_MATCH,
                    similarity_score=0.0,
                    suggested_matches=[]
                )
                matching_result.matches.append(new_match)
                
            elif change_type == "item_edit":
                # For item edits, we need to regenerate matching for that specific item
                # This is more complex, so for now we'll just mark that matching needs to be redone
                # The user will need to redo ingredient matching if they want accurate results
                print(self.locale_manager.get_text("debug.item_edited", context))
                return
                
            # Update context
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['changed_ingredient_indices'] = changed_indices
            
            # Save updated matching result with new receipt hash
            user_id = update.effective_user.id
            new_receipt_hash = receipt_data.get_receipt_hash()
            success = self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, new_receipt_hash)
            
            # Clear old matching result file if hash changed
            if context.user_data.get('original_data'):
                old_receipt_hash = context.user_data['original_data'].get_receipt_hash()
                if old_receipt_hash != new_receipt_hash:
                    self.ingredient_storage.clear_matching_result(user_id, old_receipt_hash)
            
            print(self.locale_manager.get_text("debug.matching_updated", context, change_type=change_type, new_receipt_hash=new_receipt_hash, success=success))
                
        except Exception as e:
            print(self.locale_manager.get_text("debug.matching_update_error", context, change_type=change_type, error=e))
    
    async def _update_ingredient_matching_after_deletion(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       receipt_data, deleted_line_number: int) -> None:
        """Update ingredient matching after line deletion"""
        try:
            # Get current matching result from context or storage
            matching_result = context.user_data.get('ingredient_matching_result')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if not matching_result:
                # Try to load from storage using old hash
                user_id = update.effective_user.id
                old_receipt_data = context.user_data.get('original_data')
                if old_receipt_data:
                    old_receipt_hash = old_receipt_data.get_receipt_hash()
                    saved_data = self.ingredient_storage.load_matching_result(user_id, old_receipt_hash)
                    if saved_data:
                        matching_result, changed_indices = saved_data
                        # Update context with loaded data
                        context.user_data['ingredient_matching_result'] = matching_result
                        context.user_data['changed_ingredient_indices'] = changed_indices
            
            if not matching_result:
                print(self.locale_manager.get_text("debug.no_matching_result_deletion", context))
                return
            
            # Find the index of the deleted item in the matching result
            # The matching result should have the same order as the original receipt items
            deleted_index = None
            for i, match in enumerate(matching_result.matches):
                # We need to find the match that corresponds to the deleted line
                # Since we don't have direct mapping, we'll use the order
                if i == deleted_line_number - 1:  # Convert line number to 0-based index
                    deleted_index = i
                    break
            
            if deleted_index is not None:
                # Remove the match at the deleted index
                matching_result.matches.pop(deleted_index)
                
                # Update changed indices - remove any indices >= deleted_index and decrement others
                updated_changed_indices = set()
                for idx in changed_indices:
                    if idx < deleted_index:
                        updated_changed_indices.add(idx)
                    elif idx > deleted_index:
                        updated_changed_indices.add(idx - 1)
                # Don't add the deleted index itself
                
                # Update context
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = updated_changed_indices
                
                # Save updated matching result with new receipt hash
                user_id = update.effective_user.id
                new_receipt_hash = receipt_data.get_receipt_hash()
                success = self.ingredient_storage.save_matching_result(user_id, matching_result, updated_changed_indices, new_receipt_hash)
                
                # Clear old matching result file
                if context.user_data.get('original_data'):
                    old_receipt_hash = context.user_data['original_data'].get_receipt_hash()
                    if old_receipt_hash != new_receipt_hash:
                        self.ingredient_storage.clear_matching_result(user_id, old_receipt_hash)
                
                print(self.locale_manager.get_text("debug.matching_updated_deletion", context, new_receipt_hash=new_receipt_hash, success=success))
            else:
                print(self.locale_manager.get_text("debug.deleted_line_not_found", context, deleted_line_number=deleted_line_number))
                
        except Exception as e:
            print(self.locale_manager.get_text("debug.deletion_error", context, error=e))
    
    # Additional utility methods that were in the original file
    async def _send_long_message_with_keyboard(self, message, text: str, reply_markup):
        """Send long message with keyboard"""
        await self.common_handlers.send_long_message_with_keyboard(message, text, reply_markup)
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        await self.common_handlers.send_long_message_with_keyboard(message, text, reply_markup)
