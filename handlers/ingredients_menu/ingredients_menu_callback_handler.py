"""
Ingredients Menu Callback Handler
Обработчик callback'ов для управления меню ингредиентов
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from handlers.base_callback_handler import BaseCallbackHandler
from config.locales.locale_manager import get_global_locale_manager
from services.ingredients_manager import get_ingredients_manager


class IngredientsMenuCallbackHandler(BaseCallbackHandler):
    """Handler for ingredients menu callback queries"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.ingredients_manager = get_ingredients_manager()
    
    async def handle_ingredients_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ingredients management callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Get user's ingredients
        user_ingredients = await self.ingredients_manager.get_user_ingredients(user_id)
        
        if not user_ingredients:
            # Scenario A: User has no ingredients
            return await self._show_no_ingredients_screen(update, context)
        else:
            # Scenario B: User has ingredients
            return await self._show_has_ingredients_screen(update, context, user_ingredients)
    
    async def _show_no_ingredients_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show screen when user has no ingredients"""
        query = update.callback_query
        
        # Create keyboard for no ingredients scenario
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.upload_file", context, update=update),
                callback_data="ingredients_upload_file"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back", context, update=update),
                callback_data="dashboard_main"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("ingredients.management.no_ingredients", context, update=update),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def _show_has_ingredients_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ingredients: list) -> int:
        """Show screen when user has ingredients"""
        query = update.callback_query
        
        # Create keyboard for has ingredients scenario
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.view_list", context, update=update),
                callback_data="ingredients_view_list"
            )],
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.replace_list", context, update=update),
                callback_data="ingredients_replace_list"
            )],
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.delete_list", context, update=update),
                callback_data="ingredients_delete_list"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back", context, update=update),
                callback_data="dashboard_main"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("ingredients.management.has_ingredients", context, update=update),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def handle_view_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle view ingredients list callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        user_ingredients = await self.ingredients_manager.get_user_ingredients(user_id)
        
        if not user_ingredients:
            # If no ingredients, show no ingredients screen
            return await self._show_no_ingredients_screen(update, context)
        
        # Format ingredients list
        ingredients_text = "\n".join([f"• {ingredient}" for ingredient in user_ingredients])
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.replace_list", context, update=update),
                callback_data="ingredients_replace_list"
            )],
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.delete_list", context, update=update),
                callback_data="ingredients_delete_list"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back", context, update=update),
                callback_data="ingredients_management"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("ingredients.management.list_display", context, update=update, 
                         ingredients=ingredients_text),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def handle_replace_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle replace ingredients list callback"""
        query = update.callback_query
        await query.answer()
        
        # Show instruction for file upload
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("buttons.back", context, update=update),
                callback_data="ingredients_management"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("ingredients.management.replace_instruction", context, update=update),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def handle_delete_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete ingredients list callback"""
        query = update.callback_query
        await query.answer()
        
        # Show confirmation dialog
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.confirm_delete", context, update=update),
                callback_data="ingredients_confirm_delete"
            )],
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.cancel_delete", context, update=update),
                callback_data="ingredients_management"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("ingredients.management.delete_confirmation", context, update=update),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def handle_confirm_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle confirm delete ingredients list callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Delete ingredients list
        success = await self.ingredients_manager.delete_user_ingredients(user_id)
        
        if success:
            # Show success message and return to no ingredients screen
            await query.edit_message_text(
                self.get_text("ingredients.management.delete_success", context, update=update),
                parse_mode='HTML'
            )
            
            # Wait a bit and show no ingredients screen
            import asyncio
            await asyncio.sleep(2)
            return await self._show_no_ingredients_screen(update, context)
        else:
            # Show error message
            keyboard = [
                [InlineKeyboardButton(
                    self.get_text("buttons.back", context, update=update),
                    callback_data="ingredients_management"
                )]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                self.get_text("ingredients.management.delete_error", context, update=update),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        return self.config.AWAITING_DASHBOARD
    
    async def handle_upload_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle upload file callback"""
        query = update.callback_query
        await query.answer()
        
        # Show instruction for file upload
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("buttons.back", context, update=update),
                callback_data="ingredients_management"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_text("ingredients.management.file_upload_instruction", context, update=update),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_DASHBOARD
