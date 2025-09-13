"""
Google Sheets input handling for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import LocaleManager


class GoogleSheetsInputHandler(BaseMessageHandler):
    """Handler for Google Sheets input processing"""
    
    async def _handle_google_sheets_ingredient_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle Google Sheets ingredient name search"""
        from handlers.callback_handlers import CallbackHandlers
        
        # Get the selected line number
        selected_line = context.user_data.get('selected_google_sheets_line')
        if not selected_line:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("sheets.no_line_selected", context), duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Get user's personal ingredients from Firestore
        from services.ingredients_manager import get_ingredients_manager
        ingredients_manager = get_ingredients_manager()
        user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
        
        if not user_ingredients:
            await self.ui_manager.send_temp(
                update, context, "❌ Нет персональных ингредиентов для поиска. Добавьте ингредиенты в настройках для использования поиска.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Convert user ingredients to the format expected by search service
        google_sheets_ingredients_for_search = {}
        for i, ingredient_name in enumerate(user_ingredients):
            google_sheets_ingredients_for_search[ingredient_name] = f"user_ingredient_{i}"
        
        # Use the same smart search as in poster
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            user_input, google_sheets_ingredients_for_search, limit=10
        )
        
        print(f"DEBUG: Smart search for '{user_input}' in {len(google_sheets_ingredients_for_search)} Google Sheets ingredients (ingredient search)")
        print(f"DEBUG: Found {len(search_results)} search results (ingredient search)")
        
        # Clear the search flag
        context.user_data.pop('awaiting_google_sheets_ingredient_name', None)
        
        if search_results:
            # Show search results
            await self._show_google_sheets_search_results(update, context, user_input, search_results, selected_line)
        else:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("sheets.no_search_results", context, query=user_input), duration=5
            )
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_google_sheets_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle Google Sheets search mode"""
        print(f"DEBUG: _handle_google_sheets_search called with input: '{user_input}'")
        item_index = context.user_data.get('google_sheets_search_item_index')
        if item_index is None:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("sheets.no_item_selected", context), duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Get user's personal ingredients from Firestore
        from services.ingredients_manager import get_ingredients_manager
        ingredients_manager = get_ingredients_manager()
        user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
        
        if not user_ingredients:
            await self.ui_manager.send_temp(
                update, context, "❌ Нет персональных ингредиентов для поиска. Добавьте ингредиенты в настройках для использования поиска.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Convert user ingredients to the format expected by search service
        google_sheets_ingredients_for_search = {}
        for i, ingredient_name in enumerate(user_ingredients):
            google_sheets_ingredients_for_search[ingredient_name] = f"user_ingredient_{i}"
        
        print(f"DEBUG: Using {len(google_sheets_ingredients_for_search)} personal ingredients for search")
        
        # Use the same smart search as in poster
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            user_input, google_sheets_ingredients_for_search, limit=10
        )
        
        print(f"DEBUG: Smart search for '{user_input}' in {len(google_sheets_ingredients_for_search)} Google Sheets ingredients")
        print(f"DEBUG: Found {len(search_results)} search results")
        if search_results:
            print(f"DEBUG: Top 3 results: {[r['name'] for r in search_results[:3]]}")
        else:
            print("DEBUG: No search results found - checking ingredient list:")
            print(f"DEBUG: Available ingredients: {list(google_sheets_ingredients_for_search.keys())[:10]}")
        
        # Clear search mode
        context.user_data.pop('google_sheets_search_mode', None)
        context.user_data.pop('google_sheets_search_item_index', None)
        
        if search_results:
            # Show search results for specific item
            await self._show_google_sheets_item_search_results(update, context, user_input, search_results, item_index)
        else:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("sheets.no_search_results", context, query=user_input), duration=5
            )
        
        return self.config.AWAITING_CORRECTION
    
    async def _show_google_sheets_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                               query: str, results: list, selected_line: int):
        """Show Google Sheets search results for position selection"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = self.locale_manager.get_text("sheets.search_results_title", context, query=query)
        
        # Create buttons for results
        keyboard = []
        for i, result in enumerate(results[:10], 1):  # Show max 10 results
            button_text = self.locale_manager.get_text("sheets.search_result_button", context, 
                                                      number=i, name=self._truncate_name(result['name'], 25))
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_position_match_{selected_line}_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("sheets.back_button", context), callback_data="back_to_google_sheets_matching")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to edit existing message instead of sending new one
        try:
            # Get the working menu message ID
            working_message_id = context.user_data.get('working_menu_message_id')
            if working_message_id:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=working_message_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                # Fallback to sending new message
                await self.ui_manager.send_menu(
                    update, context, text, reply_markup, 'Markdown'
                )
        except Exception as e:
            print(f"DEBUG: Error editing message, falling back to new message: {e}")
            await self.ui_manager.send_menu(
                update, context, text, reply_markup, 'Markdown'
            )
    
    async def _show_google_sheets_item_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                    query: str, results: list, item_index: int):
        """Show Google Sheets search results for specific item"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        print(f"DEBUG: _show_google_sheets_item_search_results called with {len(results)} results for query '{query}'")
        text = self.locale_manager.get_text("sheets.search_results_title", context, query=query)
        
        # Save search results for callback handling
        context.user_data['google_sheets_search_results'] = results
        
        # Create buttons for results in two columns
        keyboard = []
        for i, result in enumerate(results[:10], 1):  # Show max 10 results
            button_text = self.locale_manager.get_text("sheets.search_result_button", context, 
                                                      number=i, name=self._truncate_name(result['name'], 20))
            if i % 2 == 1:
                # Start new row
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_search_{item_index}_{i-1}")])
            else:
                # Add to existing row
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_search_{item_index}_{i-1}"))
        
        # Add back button
        keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("sheets.back_button", context), callback_data="back_to_google_sheets_matching")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to edit existing message instead of sending new one
        try:
            # Get the working menu message ID
            working_message_id = context.user_data.get('working_menu_message_id')
            if working_message_id:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=working_message_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                # Fallback to sending new message
                await self.ui_manager.send_menu(
                    update, context, text, reply_markup, 'Markdown'
                )
        except Exception as e:
            print(f"DEBUG: Error editing message, falling back to new message: {e}")
            await self.ui_manager.send_menu(
                update, context, text, reply_markup, 'Markdown'
            )
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name if too long"""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
