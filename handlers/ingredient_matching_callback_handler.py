"""
Ingredient matching callback handler for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus
from services.ingredient_matching_service import IngredientMatchingService
from utils.ingredient_formatter import IngredientFormatter


class IngredientMatchingCallbackHandler(BaseCallbackHandler):
    """Handler for ingredient matching callbacks"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.ingredient_matching_service = IngredientMatchingService()
        self.ingredient_formatter = IngredientFormatter()
    
    async def _show_ingredient_matching_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ingredient matching results"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Format matching results
        results_text = self.ingredient_formatter.format_matching_results(matching_result)
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton("✏️ Ручное сопоставление", callback_data="manual_matching")],
            [InlineKeyboardButton("📊 Показать таблицу", callback_data="show_matching_table")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, results_text, reply_markup)
    
    async def _show_manual_matching_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching overview"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Count different match statuses
        no_match_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.NO_MATCH)
        matched_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.MATCHED)
        partial_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.PARTIAL_MATCH)
        
        overview_text = f"🔍 **Обзор сопоставления ингредиентов**\n\n"
        overview_text += f"📊 **Статистика:**\n"
        overview_text += f"✅ Сопоставлено: {matched_count}\n"
        overview_text += f"⚠️ Частично: {partial_count}\n"
        overview_text += f"❌ Не сопоставлено: {no_match_count}\n"
        overview_text += f"📝 Всего позиций: {len(matching_result.matches)}\n\n"
        overview_text += "Выберите действие:"
        
        # Create buttons for each unmatched item
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status == MatchStatus.NO_MATCH:
                item_text = f"{i+1}. {match.receipt_item_name[:25]}{'...' if len(match.receipt_item_name) > 25 else ''}"
                keyboard.append([InlineKeyboardButton(f"🔍 {item_text}", callback_data=f"match_item_{i}")])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔄 Автоматическое сопоставление", callback_data="auto_match_all")],
            [InlineKeyboardButton("📊 Показать таблицу", callback_data="show_matching_table")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_edit")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(overview_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_position_selection_interface(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show position selection interface"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Show items that need matching
        items_text = "🔍 **Выберите позицию для сопоставления:**\n\n"
        
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            status_emoji = "✅" if match.match_status == MatchStatus.MATCHED else "❌"
            item_text = f"{i+1}. {match.receipt_item_name[:30]}{'...' if len(match.receipt_item_name) > 30 else ''}"
            keyboard.append([InlineKeyboardButton(f"{status_emoji} {item_text}", callback_data=f"select_item_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="manual_matching")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(items_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_item_selection_for_matching(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int):
        """Handle item selection for matching"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result or item_index >= len(matching_result.matches):
            await query.edit_message_text("❌ Неверный индекс позиции")
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
            await query.edit_message_text("❌ Неверный индекс позиции")
            return
        
        match = matching_result.matches[current_item]
        
        # Show item details and suggestions
        item_text = f"🔍 **Сопоставление позиции {current_item + 1}:**\n\n"
        item_text += f"📝 **Товар из чека:** {match.receipt_item_name}\n\n"
        
        if match.suggested_matches:
            item_text += f"💡 **Предложения:**\n"
            for i, suggestion in enumerate(match.suggested_matches[:5], 1):
                item_text += f"{i}. {suggestion['name']} (сходство: {suggestion['similarity']:.2f})\n"
        else:
            item_text += "❌ Предложения не найдены\n"
        
        # Create buttons
        keyboard = []
        
        # Add suggestion buttons
        for i, suggestion in enumerate(match.suggested_matches[:5], 1):
            suggestion_text = suggestion['name'][:25] + ('...' if len(suggestion['name']) > 25 else '')
            keyboard.append([InlineKeyboardButton(f"✅ {i}. {suggestion_text}", callback_data=f"select_suggestion_{i-1}")])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Поиск вручную", callback_data="manual_search")],
            [InlineKeyboardButton("❌ Пропустить", callback_data="skip_item")],
            [InlineKeyboardButton("◀️ Назад к списку", callback_data="position_selection")]
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
            await query.edit_message_text("❌ Неверный индекс позиции")
            return
        
        match = matching_result.matches[current_item]
        
        if suggestion_number >= len(match.suggested_matches):
            await query.edit_message_text("❌ Неверный номер предложения")
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
        success_text = f"✅ **Сопоставление выполнено!**\n\n"
        success_text += f"📝 **Товар:** {match.receipt_item_name}\n"
        success_text += f"🎯 **Ингредиент:** {match.matched_ingredient_name}\n"
        success_text += f"📊 **Сходство:** {match.similarity_score:.2f}\n\n"
        success_text += "Переходим к следующей позиции..."
        
        keyboard = [
            [InlineKeyboardButton("➡️ Следующая позиция", callback_data="next_item")],
            [InlineKeyboardButton("◀️ Назад к списку", callback_data="position_selection")]
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
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
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
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Count results
        matched_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.MATCHED)
        total_count = len(matching_result.matches)
        
        result_text = f"🎉 **Сопоставление завершено!**\n\n"
        result_text += f"📊 **Результаты:**\n"
        result_text += f"✅ Сопоставлено: {matched_count}/{total_count}\n"
        result_text += f"📈 Процент: {(matched_count/total_count*100):.1f}%\n\n"
        
        if matched_count == total_count:
            result_text += "🎯 Все позиции успешно сопоставлены!"
        else:
            result_text += f"⚠️ Осталось сопоставить: {total_count - matched_count} позиций"
        
        keyboard = [
            [InlineKeyboardButton("📊 Показать таблицу", callback_data="show_matching_table")],
            [InlineKeyboardButton("◀️ Назад к редактированию", callback_data="back_to_edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')
