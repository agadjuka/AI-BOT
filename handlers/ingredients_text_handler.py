"""
Ingredients Text Handler
Обработчик для загрузки и обработки текстовых сообщений с ингредиентами
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


class IngredientsTextHandler(BaseMessageHandler):
    """Handler for ingredients text message processing"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.ingredients_manager = get_ingredients_manager()
    
    async def handle_ingredients_text_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle text message upload for ingredients"""
        # Check if message has text
        if not update.message or not update.message.text:
            # Send error message and stay in same state
            error_message = await update.message.reply_text(
                self.get_text("ingredients.management.text_upload_error_empty", context, update=update)
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
            
            return self.config.AWAITING_INGREDIENTS_TEXT
        
        text_content = update.message.text.strip()
        
        # Delete user message immediately
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Failed to delete user message: {e}")
        
        # Process the text
        try:
            print(f"Processing text content: {len(text_content)} characters")
            
            # Parse text content
            ingredients_list = self._parse_ingredients_text(text_content)
            print(f"Parsed ingredients: {len(ingredients_list)} items")
            
            if not ingredients_list:
                # Text is empty or contains no valid ingredients
                # Edit the main message with error
                main_message_id = context.user_data.get('ingredients_main_message_id')
                if main_message_id:
                    try:
                        keyboard = [
                            [InlineKeyboardButton(
                                self.get_text("buttons.back", context, update=update),
                                callback_data="ingredients_management"
                            )]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=main_message_id,
                            text=self.get_text("ingredients.management.text_upload_error_empty", context, update=update),
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        
                        # Wait a bit and return to management screen
                        await asyncio.sleep(3)
                        
                        # Return to management screen
                        return await self._return_to_ingredients_management(update, context)
                    except Exception as e:
                        print(f"Failed to edit main message with error: {e}")
                        # Fallback: send temporary error message
                        error_message = await update.effective_message.reply_text(
                            self.get_text("ingredients.management.text_upload_error_empty", context, update=update)
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
                        
                        return self.config.AWAITING_INGREDIENTS_TEXT
                else:
                    # Fallback: send temporary error message
                    error_message = await update.effective_message.reply_text(
                        self.get_text("ingredients.management.text_upload_error_empty", context, update=update)
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
                    
                    return self.config.AWAITING_INGREDIENTS_TEXT
            
            # Save ingredients to database
            user_id = update.effective_user.id
            print(f"Saving {len(ingredients_list)} ingredients for user {user_id}")
            success = await self.ingredients_manager.update_user_ingredients(user_id, ingredients_list)
            print(f"Save result: {success}")
            
            if success:
                # Success - edit the main message with success and return to management
                success_text = self.get_text("ingredients.management.text_upload_success", 
                                           context, update=update, count=len(ingredients_list))
                
                # Create keyboard to return to management
                keyboard = [
                    [InlineKeyboardButton(
                        self.get_text("buttons.back", context, update=update),
                        callback_data="ingredients_management"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Edit the main message with success
                main_message_id = context.user_data.get('ingredients_main_message_id')
                if main_message_id:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=main_message_id,
                            text=success_text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        
                        # Wait a bit and return to management screen
                        await asyncio.sleep(2)
                        
                        # Return to management screen
                        return await self._return_to_ingredients_management(update, context)
                    except Exception as e:
                        print(f"Failed to edit main message: {e}")
                        # Fallback: send new message
                        success_message = await update.effective_message.reply_text(
                            success_text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        
                        # Wait a bit and return to management screen
                        await asyncio.sleep(2)
                        
                        # Delete success message and return to management
                        try:
                            await context.bot.delete_message(
                                chat_id=update.effective_chat.id,
                                message_id=success_message.message_id
                            )
                        except Exception as e:
                            print(f"Failed to delete success message: {e}")
                        
                        return await self._return_to_ingredients_management(update, context)
                else:
                    # Fallback: send new message
                    success_message = await update.effective_message.reply_text(
                        success_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    
                    # Wait a bit and return to management screen
                    await asyncio.sleep(2)
                    
                    # Delete success message and return to management
                    try:
                        await context.bot.delete_message(
                            chat_id=update.effective_chat.id,
                            message_id=success_message.message_id
                        )
                    except Exception as e:
                        print(f"Failed to delete success message: {e}")
                    
                    return await self._return_to_ingredients_management(update, context)
            else:
                # Database error
                error_message = await update.effective_message.reply_text(
                    self.get_text("ingredients.management.text_upload_error_processing", context, update=update)
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
                
                return self.config.AWAITING_INGREDIENTS_TEXT
                
        except Exception as e:
            print(f"Error processing ingredients text: {e}")
            import traceback
            traceback.print_exc()
            
            # Send error message
            error_message = await update.effective_message.reply_text(
                self.get_text("ingredients.management.text_upload_error_processing", context, update=update)
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
            
            return self.config.AWAITING_INGREDIENTS_TEXT
    
    def _parse_ingredients_text(self, text_content: str) -> List[str]:
        """Parse ingredients from text content"""
        try:
            # Split into lines and clean
            lines = text_content.split('\n')
            ingredients = []
            
            for line in lines:
                # Strip whitespace and skip empty lines
                cleaned_line = line.strip()
                if cleaned_line:
                    ingredients.append(cleaned_line)
            
            return ingredients
            
        except Exception as e:
            print(f"Error parsing ingredients text: {e}")
            return []
    
    async def _return_to_ingredients_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Return to ingredients management screen"""
        try:
            print("Returning to ingredients management screen")
            # Import here to avoid circular imports
            from handlers.ingredients_menu.ingredients_menu_callback_handler import IngredientsMenuCallbackHandler
            
            ingredients_handler = IngredientsMenuCallbackHandler(self.config, self.analysis_service)
            return await ingredients_handler.handle_ingredients_management(update, context)
        except Exception as e:
            print(f"Error returning to ingredients management: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to dashboard
            return self.config.AWAITING_DASHBOARD
