"""
Ingredient matching dispatcher for handling ingredient matching related callbacks
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import MatchStatus
from config.locales.locale_manager import locale_manager


class IngredientMatchingDispatcher(BaseCallbackHandler):
    """Dispatcher for ingredient matching related callbacks"""
    
    def __init__(self, config, analysis_service, ingredient_matching_handler, file_generation_handler):
        super().__init__(config, analysis_service)
        self.ingredient_matching_handler = ingredient_matching_handler
        self.file_generation_handler = file_generation_handler
    
    async def _handle_ingredient_matching_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle ingredient matching related actions"""
        if action == "ingredient_matching":
            await self.ingredient_matching_handler._show_ingredient_matching_results(update, context)
        elif action == "manual_matching":
            await self.ingredient_matching_handler._show_manual_matching_overview(update, context)
        elif action == "position_selection":
            await self.ingredient_matching_handler._show_position_selection_interface(update, context)
        elif action == "show_matching_table":
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                await self.file_generation_handler._show_matching_table_with_edit_button(update, context, matching_result)
        elif action.startswith(("match_item_", "select_item_")):
            item_index = int(action.split("_")[-1])
            await self.ingredient_matching_handler._handle_item_selection_for_matching(update, context, item_index)
        elif action.startswith("select_suggestion_"):
            suggestion_number = int(action.split("_")[-1])
            await self.ingredient_matching_handler._handle_ingredient_selection(update, context, suggestion_number)
        elif action in ["next_item", "skip_item"]:
            await self.ingredient_matching_handler._process_next_ingredient_match(update, context)
        elif action == "manual_match_ingredients":
            await self.ingredient_matching_handler._show_manual_matching_overview(update, context)
        elif action == "rematch_ingredients":
            context.user_data.pop('ingredient_matching_result', None)
            context.user_data.pop('changed_ingredient_indices', None)
            await self.ingredient_matching_handler._show_ingredient_matching_results(update, context)
        elif action == "apply_matching_changes":
            # Apply matching changes - delegate to message handlers
            await update.callback_query.edit_message_text(
                locale_manager.get_text("matching.callback.changes_applied", context)
            )
            return self.config.AWAITING_CORRECTION
        elif action == "select_position_for_matching":
            await self.ingredient_matching_handler._show_position_selection_interface(update, context)
        elif action == "back_to_matching_overview":
            await self.ingredient_matching_handler._show_manual_matching_overview(update, context)
        elif action == "search_ingredient":
            await update.callback_query.edit_message_text(
                locale_manager.get_text("matching.callback.search_ingredient", context)
            )
            return self.config.AWAITING_MANUAL_MATCH
        elif action in ["skip_ingredient", "next_ingredient_match"]:
            await self.ingredient_matching_handler._process_next_ingredient_match(update, context)
        elif action == "confirm_back_without_changes":
            # Confirm back without changes
            await update.callback_query.edit_message_text(
                locale_manager.get_text("matching.callback.back_without_changes", context)
            )
            return self.config.AWAITING_CORRECTION
        elif action == "cancel_back":
            # Cancel back action
            await update.callback_query.edit_message_text(
                locale_manager.get_text("matching.callback.cancel_back", context)
            )
            return self.config.AWAITING_CORRECTION
        
        return self.config.AWAITING_CORRECTION
    
    async def _show_ingredient_matching_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ingredient matching results"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text(
                locale_manager.get_text("matching.callback.results_not_found", context)
            )
            return
        
        # Format matching results
        results_text = self.ingredient_matching_handler.ingredient_formatter.format_matching_results(matching_result)
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton(
                locale_manager.get_text("matching.callback.manual_matching", context), 
                callback_data="manual_matching"
            )],
            [InlineKeyboardButton(
                locale_manager.get_text("matching.callback.show_table", context), 
                callback_data="show_matching_table"
            )],
            [InlineKeyboardButton(
                locale_manager.get_text("matching.callback.back_to_edit", context), 
                callback_data="back_to_edit"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, results_text, reply_markup)
    
    async def _show_manual_matching_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching overview"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text(
                locale_manager.get_text("matching.callback.results_not_found", context)
            )
            return
        
        # Count different match statuses
        no_match_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.NO_MATCH)
        matched_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.MATCHED)
        partial_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.PARTIAL_MATCH)
        
        overview_text = locale_manager.get_text("matching.callback.matching_overview_title", context)
        overview_text += locale_manager.get_text("matching.callback.statistics_title", context)
        overview_text += locale_manager.get_text("matching.callback.matched_count", context, count=matched_count)
        overview_text += locale_manager.get_text("matching.callback.partial_count", context, count=partial_count)
        overview_text += locale_manager.get_text("matching.callback.no_match_count", context, count=no_match_count)
        overview_text += locale_manager.get_text("matching.callback.total_positions", context, count=len(matching_result.matches))
        overview_text += locale_manager.get_text("matching.callback.choose_action", context)
        
        # Create buttons for each unmatched item
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status == MatchStatus.NO_MATCH:
                item_text = f"{i+1}. {match.receipt_item_name[:25]}{'...' if len(match.receipt_item_name) > 25 else ''}"
                keyboard.append([InlineKeyboardButton(f"🔍 {item_text}", callback_data=f"match_item_{i}")])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton(
                locale_manager.get_text("matching.callback.auto_match_all", context), 
                callback_data="auto_match_all"
            )],
            [InlineKeyboardButton(
                locale_manager.get_text("matching.callback.show_table", context), 
                callback_data="show_matching_table"
            )],
            [InlineKeyboardButton(
                locale_manager.get_text("matching.callback.back_to_edit", context), 
                callback_data="back_to_edit"
            )]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(overview_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_position_selection_interface(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show position selection interface"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text(
                locale_manager.get_text("matching.callback.results_not_found", context)
            )
            return
        
        # Show items that need matching
        items_text = locale_manager.get_text("matching.callback.position_selection_title", context)
        
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            status_emoji = "✅" if match.match_status == MatchStatus.MATCHED else "❌"
            item_text = f"{i+1}. {match.receipt_item_name[:30]}{'...' if len(match.receipt_item_name) > 30 else ''}"
            keyboard.append([InlineKeyboardButton(f"{status_emoji} {item_text}", callback_data=f"select_item_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton(
            locale_manager.get_text("matching.callback.back_to_edit", context), 
            callback_data="manual_matching"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(items_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_item_selection_for_matching(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int):
        """Handle item selection for matching"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result or item_index >= len(matching_result.matches):
            await query.edit_message_text(
                locale_manager.get_text("matching.callback.invalid_position_index", context)
            )
            return
        
        # Store current item index
        context.user_data['current_matching_item'] = item_index
        
        # Show manual matching for this item
        await self.ingredient_matching_handler._show_manual_matching_for_current_item(update, context)
