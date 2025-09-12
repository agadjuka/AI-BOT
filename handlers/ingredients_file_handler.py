"""
Ingredients File Handler
Обработчик для загрузки и обработки файлов с ингредиентами
"""

import asyncio
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import get_global_locale_manager
from services.ingredients_manager import get_ingredients_manager


class IngredientsFileHandler(BaseMessageHandler):
    """Handler for ingredients file upload and processing"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.ingredients_manager = get_ingredients_manager()
    
    async def handle_ingredients_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle file upload for ingredients"""
        # Check if message has document
        if not update.message or not update.message.document:
            # Send error message and stay in same state
            error_message = await update.message.reply_text(
                self.get_text("ingredients.management.file_upload_error_format", context, update=update)
            )
            
            # Delete error message after 3 seconds
            await asyncio.sleep(3)
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=error_message.message_id
                )
            except Exception as e:
                print(f"Failed to delete error message: {e}")
            
            return self.config.AWAITING_INGREDIENTS_FILE
        
        document = update.message.document
        
        # Validate file type
        if not self._is_valid_text_file(document):
            # Send error message and stay in same state
            error_message = await update.message.reply_text(
                self.get_text("ingredients.management.file_upload_error_format", context, update=update)
            )
            
            # Delete error message after 3 seconds
            await asyncio.sleep(3)
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=error_message.message_id
                )
            except Exception as e:
                print(f"Failed to delete error message: {e}")
            
            return self.config.AWAITING_INGREDIENTS_FILE
        
        # Delete user message immediately
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Failed to delete user message: {e}")
        
        # Process the file
        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_content = await file.download_as_bytearray()
            
            # Parse file content
            ingredients_list = self._parse_ingredients_file(file_content)
            
            if not ingredients_list:
                # File is empty or contains no valid ingredients
                # Send temporary error message
                error_message = await update.effective_message.reply_text(
                    self.get_text("ingredients.management.file_upload_error_empty", context, update=update)
                )
                
                # Delete error message after 3 seconds
                await asyncio.sleep(3)
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=error_message.message_id
                    )
                except Exception as e:
                    print(f"Failed to delete error message: {e}")
                
                return self.config.AWAITING_INGREDIENTS_FILE
            
            # Save ingredients to database
            user_id = update.effective_user.id
            success = await self.ingredients_manager.update_user_ingredients(user_id, ingredients_list)
            
            if success:
                # Success - edit message to show success and return to management
                success_text = self.get_text("ingredients.management.file_upload_success", 
                                           context, update=update, count=len(ingredients_list))
                
                # Create keyboard to return to management
                keyboard = [
                    [InlineKeyboardButton(
                        self.get_text("buttons.back", context, update=update),
                        callback_data="ingredients_management"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Edit the main message
                await update.effective_message.edit_text(
                    success_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                
                # Wait a bit and return to management screen
                await asyncio.sleep(2)
                return await self._return_to_ingredients_management(update, context)
            else:
                # Database error
                error_message = await update.effective_message.reply_text(
                    self.get_text("ingredients.management.file_upload_error_processing", context, update=update)
                )
                
                # Delete error message after 3 seconds
                await asyncio.sleep(3)
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=error_message.message_id
                    )
                except Exception as e:
                    print(f"Failed to delete error message: {e}")
                
                return self.config.AWAITING_INGREDIENTS_FILE
                
        except Exception as e:
            print(f"Error processing ingredients file: {e}")
            
            # Send error message
            error_message = await update.effective_message.reply_text(
                self.get_text("ingredients.management.file_upload_error_processing", context, update=update)
            )
            
            # Delete error message after 3 seconds
            await asyncio.sleep(3)
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=error_message.message_id
                )
            except Exception as e:
                print(f"Failed to delete error message: {e}")
            
            return self.config.AWAITING_INGREDIENTS_FILE
    
    def _is_valid_text_file(self, document) -> bool:
        """Check if document is a valid text file"""
        # Check MIME type
        if document.mime_type and document.mime_type != 'text/plain':
            return False
        
        # Check file extension
        if document.file_name:
            return document.file_name.lower().endswith('.txt')
        
        # If no file name, assume it's valid if MIME type is text/plain
        return document.mime_type == 'text/plain'
    
    def _parse_ingredients_file(self, file_content: bytes) -> List[str]:
        """Parse ingredients from file content"""
        try:
            # Decode file content
            text_content = file_content.decode('utf-8')
            
            # Split into lines and clean
            lines = text_content.split('\n')
            ingredients = []
            
            for line in lines:
                # Strip whitespace and skip empty lines
                cleaned_line = line.strip()
                if cleaned_line:
                    ingredients.append(cleaned_line)
            
            return ingredients
            
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                text_content = file_content.decode('latin-1')
                lines = text_content.split('\n')
                ingredients = []
                
                for line in lines:
                    cleaned_line = line.strip()
                    if cleaned_line:
                        ingredients.append(cleaned_line)
                
                return ingredients
            except Exception:
                return []
        except Exception:
            return []
    
    async def _return_to_ingredients_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Return to ingredients management screen"""
        # Import here to avoid circular imports
        from handlers.ingredients_menu.ingredients_menu_callback_handler import IngredientsMenuCallbackHandler
        
        ingredients_handler = IngredientsMenuCallbackHandler(self.config, self.analysis_service)
        return await ingredients_handler.handle_ingredients_management(update, context)
