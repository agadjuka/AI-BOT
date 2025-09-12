"""
Ingredient matching callback handler for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.locales.locale_manager import get_global_locale_manager
from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus
from services.ingredient_matching_service import IngredientMatchingService
from utils.ingredient_formatter import IngredientFormatter


class IngredientMatchingCallbackHandler(BaseCallbackHandler):
    """Handler for ingredient matching callbacks"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.ingredient_matching_service = IngredientMatchingService()
        self.ingredient_formatter = IngredientFormatter(self.table_manager)
    
    async def _show_ingredient_matching_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ingredient matching results"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.results_not_found", context))
            return
        
        # Format matching results
        results_text = self.ingredient_formatter.format_matching_table(matching_result, context=context)
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.manual_matching", context), callback_data="manual_matching")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.show_table", context), callback_data="show_matching_table")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.back_to_edit", context), callback_data="back_to_edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, results_text, reply_markup)
    
    async def _show_manual_matching_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching overview"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.results_not_found", context))
            return
        
        # Count different match statuses
        no_match_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.NO_MATCH)
        matched_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.MATCHED)
        partial_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.PARTIAL_MATCH)
        
        overview_text = self.locale_manager.get_text("matching.callback.matching_overview_title", context)
        overview_text += self.locale_manager.get_text("matching.callback.statistics_title", context)
        overview_text += self.locale_manager.get_text("matching.callback.matched_count", context, count=matched_count)
        overview_text += self.locale_manager.get_text("matching.callback.partial_count", context, count=partial_count)
        overview_text += self.locale_manager.get_text("matching.callback.no_match_count", context, count=no_match_count)
        overview_text += self.locale_manager.get_text("matching.callback.total_positions", context, count=len(matching_result.matches))
        overview_text += self.locale_manager.get_text("matching.callback.choose_action", context)
        
        # Create buttons for each unmatched item
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status == MatchStatus.NO_MATCH:
                item_text = self.locale_manager.get_text("matching.callback.item_list_item", context, 
                                         number=i+1, name=match.receipt_item_name[:25], 
                                         truncated='...' if len(match.receipt_item_name) > 25 else '')
                keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("matching.callback.search_item_button", context, 
                                                                   text=item_text), callback_data=f"match_item_{i}")])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.auto_match_all", context), callback_data="auto_match_all")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.show_table", context), callback_data="show_matching_table")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.back_to_edit", context), callback_data="back_to_edit")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(overview_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_position_selection_interface(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show position selection interface"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.results_not_found", context))
            return
        
        # Show items that need matching
        items_text = self.locale_manager.get_text("matching.callback.position_selection_title", context)
        
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            status_emoji = self.locale_manager.get_text("matching.callback.matched_emoji", context) if match.match_status == MatchStatus.MATCHED else self.locale_manager.get_text("matching.callback.unmatched_emoji", context)
            item_text = self.locale_manager.get_text("matching.callback.position_item", context, 
                                    number=i+1, name=match.receipt_item_name[:30], 
                                    truncated='...' if len(match.receipt_item_name) > 30 else '')
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("matching.callback.position_item_button", context, 
                                                               emoji=status_emoji, text=item_text), callback_data=f"select_item_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("matching.callback.back", context), callback_data="manual_matching")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(items_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_item_selection_for_matching(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int):
        """Handle item selection for matching"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result or item_index >= len(matching_result.matches):
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.invalid_position_index", context))
            return
        
        # Store current item index
        context.user_data['current_matching_item'] = item_index
        
        # Show manual matching for this item
        await self._show_manual_matching_for_current_item(update, context)
    
    async def _show_manual_matching_for_current_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching interface for current item"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        current_item = context.user_data.get('current_matching_item', 0)
        
        if not matching_result or current_item >= len(matching_result.matches):
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.invalid_position_index", context))
            return
        
        match = matching_result.matches[current_item]
        
        # Show item details and suggestions
        item_text = self.locale_manager.get_text("matching.callback.matching_position_title", context, position=current_item + 1)
        item_text += self.locale_manager.get_text("matching.callback.receipt_item", context, item_name=match.receipt_item_name)
        
        if match.suggested_matches:
            item_text += self.locale_manager.get_text("matching.callback.suggestions_title", context)
            for i, suggestion in enumerate(match.suggested_matches[:5], 1):
                item_text += self.locale_manager.get_text("matching.callback.suggestion_item", context, 
                                         number=i, name=suggestion['name'], similarity=suggestion['similarity'])
        else:
            item_text += self.locale_manager.get_text("matching.callback.no_suggestions", context)
        
        # Create buttons
        keyboard = []
        
        # Add suggestion buttons
        for i, suggestion in enumerate(match.suggested_matches[:5], 1):
            suggestion_text = suggestion['name'][:25] + ('...' if len(suggestion['name']) > 25 else '')
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("matching.callback.suggestion_button", context, 
                                                               number=i, text=suggestion_text), 
                                                 callback_data=f"select_suggestion_{i-1}")])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.manual_search", context), callback_data="manual_search")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.skip_item", context), callback_data="skip_item")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.back_to_list", context), callback_data="position_selection")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(item_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_ingredient_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, suggestion_number: int):
        """Handle ingredient selection from suggestions"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        current_item = context.user_data.get('current_matching_item', 0)
        
        if not matching_result or current_item >= len(matching_result.matches):
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.invalid_position_index", context))
            return
        
        match = matching_result.matches[current_item]
        
        if suggestion_number >= len(match.suggested_matches):
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.invalid_suggestion_number", context))
            return
        
        # Select the suggestion
        selected_suggestion = match.suggested_matches[suggestion_number]
        match.matched_ingredient_name = selected_suggestion['name']
        match.matched_ingredient_id = selected_suggestion.get('id', '')
        match.match_status = MatchStatus.MATCHED
        match.similarity_score = selected_suggestion['similarity']
        
        # Update changed indices
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        changed_indices.add(current_item)
        context.user_data['changed_ingredient_indices'] = changed_indices
        
        # Save updated matching result
        self._save_ingredient_matching_data(update.effective_user.id, context)
        
        # Show success message and continue
        success_text = self.locale_manager.get_text("matching.callback.matching_completed", context)
        success_text += self.locale_manager.get_text("matching.callback.matched_item", context, item_name=match.receipt_item_name)
        success_text += self.locale_manager.get_text("matching.callback.matched_ingredient", context, ingredient_name=match.matched_ingredient_name)
        success_text += self.locale_manager.get_text("matching.callback.similarity_score", context, score=match.similarity_score)
        success_text += self.locale_manager.get_text("matching.callback.continue_to_next", context)
        
        keyboard = [
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.next_position", context), callback_data="next_item")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.back_to_list", context), callback_data="position_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _process_next_ingredient_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process next ingredient match"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        current_item = context.user_data.get('current_matching_item', 0)
        
        if not matching_result:
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.results_not_found", context))
            return
        
        # Find next unmatched item
        next_item = None
        for i in range(current_item + 1, len(matching_result.matches)):
            if matching_result.matches[i].match_status == MatchStatus.NO_MATCH:
                next_item = i
                break
        
        if next_item is not None:
            context.user_data['current_matching_item'] = next_item
            await self._show_manual_matching_for_current_item(update, context)
        else:
            # No more items to match
            await self._show_final_ingredient_matching_result(update, context)
    
    async def _show_final_ingredient_matching_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final ingredient matching result"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text(self.locale_manager.get_text("matching.callback.results_not_found", context))
            return
        
        # Count results
        matched_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.MATCHED)
        total_count = len(matching_result.matches)
        
        result_text = self.locale_manager.get_text("matching.callback.matching_finished", context)
        result_text += self.locale_manager.get_text("matching.callback.results_title", context)
        result_text += self.locale_manager.get_text("matching.callback.matched_summary", context, 
                                   matched=matched_count, total=total_count)
        result_text += self.locale_manager.get_text("matching.callback.matched_percentage", context, percentage=matched_count/total_count*100)
        
        if matched_count == total_count:
            result_text += self.locale_manager.get_text("matching.callback.all_matched", context)
        else:
            result_text += self.locale_manager.get_text("matching.callback.remaining_items", context, count=total_count - matched_count)
        
        keyboard = [
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.show_table", context), callback_data="show_matching_table")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.callback.back_to_editing", context), callback_data="back_to_edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')
