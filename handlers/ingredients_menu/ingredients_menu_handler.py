"""
Ingredients Menu Handler
Обработчик для управления меню ингредиентов
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import get_global_locale_manager
from services.ingredients_manager import get_ingredients_manager


class IngredientsMenuHandler(BaseMessageHandler):
    """Handler for ingredients menu management"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.ingredients_manager = get_ingredients_manager()
    
    async def show_ingredients_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show ingredients management screen"""
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
        # Create keyboard for no ingredients scenario
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("ingredients.management.buttons.upload_file", context, update=update),
                callback_data="ingredients_upload_file"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back_to_main_menu", context, update=update),
                callback_data="dashboard_main"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit message with no ingredients content
        if update.callback_query:
            await update.callback_query.edit_message_text(
                self.get_text("ingredients.management.no_ingredients", context, update=update),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_html(
                self.get_text("ingredients.management.no_ingredients", context, update=update),
                reply_markup=reply_markup
            )
        
        return self.config.AWAITING_DASHBOARD
    
    async def _show_has_ingredients_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ingredients: list) -> int:
        """Show screen when user has ingredients"""
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
                self.get_text("buttons.back_to_main_menu", context, update=update),
                callback_data="dashboard_main"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit message with has ingredients content
        if update.callback_query:
            await update.callback_query.edit_message_text(
                self.get_text("ingredients.management.has_ingredients", context, update=update),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_html(
                self.get_text("ingredients.management.has_ingredients", context, update=update),
                reply_markup=reply_markup
            )
        
        return self.config.AWAITING_DASHBOARD
    
    async def show_ingredients_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user's ingredients list"""
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
                self.get_text("buttons.back_to_main_menu", context, update=update),
                callback_data="ingredients_management"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit message with ingredients list
        if update.callback_query:
            await update.callback_query.edit_message_text(
                self.get_text("ingredients.management.list_display", context, update=update, 
                             ingredients=ingredients_text),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_html(
                self.get_text("ingredients.management.list_display", context, update=update,
                             ingredients=ingredients_text),
                reply_markup=reply_markup
            )
        
        return self.config.AWAITING_DASHBOARD
    
    async def handle_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle file upload for ingredients"""
        # This will be implemented to handle file uploads
        # For now, just show a message
        if update.callback_query:
            await update.callback_query.answer(
                self.get_text("ingredients.management.file_upload_instruction", context, update=update)
            )
        else:
            await update.message.reply_text(
                self.get_text("ingredients.management.file_upload_instruction", context, update=update)
            )
        
        return self.config.AWAITING_DASHBOARD
