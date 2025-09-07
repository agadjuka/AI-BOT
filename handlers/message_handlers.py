"""
Message handlers for Telegram bot - Refactored version
"""
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisService
from handlers.base_message_handler import BaseMessageHandler
from handlers.photo_handler import PhotoHandler
from handlers.input_handler import InputHandler
from handlers.ingredient_matching_input_handler import IngredientMatchingInputHandler
from handlers.google_sheets_input_handler import GoogleSheetsInputHandler


class MessageHandlers(BaseMessageHandler):
    """Main message handlers coordinator - refactored version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        super().__init__(config, analysis_service)
        
        # Initialize specialized handlers
        self.photo_handler = PhotoHandler(config, analysis_service)
        self.input_handler = InputHandler(config, analysis_service)
        self.ingredient_matching_handler = IngredientMatchingInputHandler(config, analysis_service)
        self.google_sheets_handler = GoogleSheetsInputHandler(config, analysis_service)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        # Create start menu with buttons
        keyboard = [
            [InlineKeyboardButton("📸 Анализировать чек", callback_data="analyze_receipt")],
            [InlineKeyboardButton("📄 Получить файл для загрузки в постер", callback_data="generate_supply_file")]
        ]
        
        # Add back button if there's existing receipt data
        if context.user_data.get('receipt_data'):
            keyboard.append([InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(
            f"Привет, {update.effective_user.mention_html()}! 👋\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
        return self.config.AWAITING_CORRECTION
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle photo upload - delegate to photo handler"""
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
                print(f"DEBUG: No matching result found to update after {change_type}")
                return
            
            # For different change types, we need different handling
            if change_type == "deletion":
                # This will be handled by the specific deletion function
                return
            elif change_type == "addition":
                # Add a new empty match for the new item
                from models.ingredient_matching import IngredientMatch, MatchStatus
                new_match = IngredientMatch(
                    receipt_item_name="Новый товар",
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
                print("DEBUG: Item edited - ingredient matching may need to be redone")
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
            
            print(f"DEBUG: Updated ingredient matching after {change_type}, new hash: {new_receipt_hash}, success: {success}")
                
        except Exception as e:
            print(f"DEBUG: Error updating ingredient matching after {change_type}: {e}")
    
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
                print("DEBUG: No matching result found to update after deletion")
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
                
                print(f"DEBUG: Updated ingredient matching after deletion, new hash: {new_receipt_hash}, success: {success}")
            else:
                print(f"DEBUG: Could not find matching index for deleted line {deleted_line_number}")
                
        except Exception as e:
            print(f"DEBUG: Error updating ingredient matching after deletion: {e}")
    
    # Additional utility methods that were in the original file
    async def _send_long_message_with_keyboard(self, message, text: str, reply_markup):
        """Send long message with keyboard"""
        if len(text) <= self.config.MAX_MESSAGE_LENGTH:
            sent_message = await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return sent_message
        
        # Split into parts
        parts = [text[i:i + self.config.MAX_MESSAGE_LENGTH] for i in range(0, len(text), self.config.MAX_MESSAGE_LENGTH)]
        
        # Send all parts except last
        for part in parts[:-1]:
            await message.reply_text(part, parse_mode='Markdown')
            await asyncio.sleep(self.config.MESSAGE_DELAY)
        
        # Send last part with keyboard
        sent_message = await message.reply_text(parts[-1], reply_markup=reply_markup, parse_mode='Markdown')
        return sent_message
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        if len(text) <= self.config.MAX_MESSAGE_LENGTH:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Split into parts
        parts = [text[i:i + self.config.MAX_MESSAGE_LENGTH] for i in range(0, len(text), self.config.MAX_MESSAGE_LENGTH)]
        
        # Send all parts except last
        for part in parts[:-1]:
            await message.reply_text(part, parse_mode='Markdown')
            await asyncio.sleep(self.config.MESSAGE_DELAY)
        
        # Send last part with keyboard
        await message.reply_text(parts[-1], reply_markup=reply_markup, parse_mode='Markdown')
