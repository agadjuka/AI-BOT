"""
Field editing callback handlers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from models.receipt import ReceiptData
from services.ai_service import ReceiptAnalysisService
from utils.formatters import NumberFormatter, TextParser
from utils.receipt_processor import ReceiptProcessor
from utils.ui_manager import UIManager
from utils.ingredient_storage import IngredientStorage
from validators.receipt_validator import ReceiptValidator


class FieldEditHandler:
    """Handler for field editing operations"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
        self.processor = ReceiptProcessor()
        self.validator = ReceiptValidator()
        self.ingredient_storage = IngredientStorage()
        self.ui_manager = UIManager(config)
    
    async def handle_field_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle field edit action"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        if action.startswith("field_"):
            # Extract line number and field name
            parts = action.split("_")
            if len(parts) >= 3:
                line_number = int(parts[1])
                field_name = parts[2]
                
                # Set editing context
                context.user_data['line_to_edit'] = line_number
                context.user_data['field_to_edit'] = field_name
                
                # Show input prompt
                field_labels = {
                    'name': 'название товара',
                    'quantity': 'количество',
                    'price': 'цену за единицу',
                    'total': 'сумму'
                }
                
                field_label = field_labels.get(field_name, field_name)
                await self.ui_manager.send_temp(
                    update, context,
                    f"Введите новое значение для **{field_label}**:",
                    duration=30
                )
                
                return self.config.AWAITING_FIELD_EDIT
        
        elif action.startswith("apply_"):
            # Apply changes and return to report
            line_number = int(action.split("_")[1])
            context.user_data['line_to_edit'] = line_number
            
            # Show edit menu
            await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
        
        return self.config.AWAITING_CORRECTION
    
    async def handle_edit_line(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle edit specific line action"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        if action.startswith("edit_"):
            line_number = int(action.split("_")[1])
            context.user_data['line_to_edit'] = line_number
            
            # Show edit menu
            await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
        
        return self.config.AWAITING_CORRECTION
    
    async def handle_ingredient_matching_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ingredient matching related actions"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        
        elif action == "select_position_for_matching":
            await self.ui_manager.send_temp(
                update, context,
                "Введите название ингредиента для поиска в справочнике:",
                duration=30
            )
            context.user_data['awaiting_position_search'] = True
            return self.config.AWAITING_MANUAL_MATCH
        
        elif action.startswith("select_item_"):
            match_index = int(action.split("_")[2])
            context.user_data['current_match_index'] = match_index
            await self._show_manual_matching_for_item(update, context, match_index)
            return self.config.AWAITING_MANUAL_MATCH
        
        elif action.startswith("select_position_"):
            result_index = int(action.split("_")[2]) - 1
            await self._handle_position_selection(update, context, result_index)
            return self.config.AWAITING_MANUAL_MATCH
        
        elif action.startswith("select_position_match_"):
            result_index = int(action.split("_")[3]) - 1
            await self._handle_position_match_selection(update, context, result_index)
            return self.config.AWAITING_MANUAL_MATCH
        
        elif action.startswith("select_search_"):
            result_index = int(action.split("_")[2]) - 1
            await self._handle_search_selection(update, context, result_index)
            return self.config.AWAITING_MANUAL_MATCH
        
        elif action == "search_ingredient":
            await self.ui_manager.send_temp(
                update, context,
                "Введите поисковый запрос:",
                duration=30
            )
            context.user_data['awaiting_search'] = True
            return self.config.AWAITING_MANUAL_MATCH
        
        elif action == "skip_ingredient":
            await self._process_next_ingredient_match(update, context)
            return self.config.AWAITING_MANUAL_MATCH
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send edit menu for specific line"""
        line_number = context.user_data.get('line_to_edit')
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number)
        
        if not item_to_edit:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: строка не найдена", duration=5
            )
            return
        
        # Auto calculate and update status
        item_to_edit = self.processor.auto_calculate_total_if_needed(item_to_edit)
        item_to_edit = self.processor.auto_update_item_status(item_to_edit)
        
        # Format values
        name = item_to_edit.name
        quantity = self.number_formatter.format_number_with_spaces(item_to_edit.quantity)
        price = self.number_formatter.format_number_with_spaces(item_to_edit.price)
        total = self.number_formatter.format_number_with_spaces(item_to_edit.total)
        
        # Status icon
        status = item_to_edit.status
        if status == 'confirmed':
            status_icon = "✅"
        elif status == 'error':
            status_icon = "🔴"
        else:
            status_icon = "⚠️"
        
        text = f"**Редактирование строки {line_number}:** {status_icon}\n\n"
        text += f"📝 **Название:** {name}\n"
        text += f"🔢 **Количество:** {quantity}\n"
        text += f"💰 **Цена:** {price}\n"
        text += f"💵 **Сумма:** {total}\n\n"
        text += "Выберите поле для редактирования:"
        
        keyboard = [
            [
                InlineKeyboardButton("📝 Название", callback_data=f"field_{line_number}_name"),
                InlineKeyboardButton("🔢 Количество", callback_data=f"field_{line_number}_quantity"),
                InlineKeyboardButton("💰 Цена", callback_data=f"field_{line_number}_price")
            ],
            [
                InlineKeyboardButton("💵 Сумма", callback_data=f"field_{line_number}_total"),
                InlineKeyboardButton("✅ Применить", callback_data=f"apply_{line_number}"),
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await self.ui_manager.send_menu(
            update, context, text, reply_markup, 'Markdown'
        )
        context.user_data['edit_menu_message_id'] = message.message_id
    
    async def _show_manual_matching_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show manual matching overview"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        # Filter items that need matching
        items_needing_match = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status.value != 'exact':
                items_needing_match.append((i, match))
        
        if not items_needing_match:
            await self.ui_manager.send_menu(
                update, context,
                "✅ **Все ингредиенты уже сопоставлены!**\n\n"
                "Все товары имеют точные совпадения с ингредиентами Poster.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Вернуться к обзору", callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
            return
        
        # Create overview text
        overview_text = f"**Ручное сопоставление ингредиентов**\n\n"
        overview_text += f"📊 **Требуют сопоставления:** {len(items_needing_match)} из {len(matching_result.matches)}\n\n"
        overview_text += "**Выберите товар для сопоставления:**\n"
        
        # Create buttons for items needing match
        keyboard = []
        for i, (match_index, match) in enumerate(items_needing_match):
            status_emoji = "🟡" if match.match_status.value == 'partial' else "🔴"
            button_text = f"{status_emoji} {match.receipt_item_name[:15]}"
            
            if i % 2 == 0:
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_item_{match_index}")])
            else:
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_item_{match_index}"))
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Выбрать позицию для сопоставления", callback_data="select_position_for_matching")],
            [InlineKeyboardButton("◀️ Вернуться к обзору", callback_data="back_to_receipt")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(update, context, overview_text, reply_markup, 'Markdown')
    
    async def _show_manual_matching_for_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, match_index: int) -> None:
        """Show manual matching interface for specific item"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result or match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        current_match = matching_result.matches[match_index]
        
        # Show current match info
        progress_text = f"**Сопоставление ингредиентов** ({match_index + 1}/{len(matching_result.matches)})\n\n"
        progress_text += f"**Текущий товар:** {current_match.receipt_item_name}\n\n"
        
        if current_match.match_status.value == "exact":
            progress_text += f"✅ **Автоматически сопоставлено:** {current_match.matched_ingredient_name}\n\n"
            progress_text += "Нажмите /continue для перехода к следующему товару."
        else:
            if current_match.suggested_matches:
                from utils.ingredient_formatter import IngredientFormatter
                formatter = IngredientFormatter()
                suggestions_text = formatter.format_suggestions_for_manual_matching(current_match)
                progress_text += suggestions_text + "\n\n"
            
            from utils.ingredient_formatter import IngredientFormatter
            formatter = IngredientFormatter()
            instructions = formatter.format_manual_matching_instructions()
            progress_text += instructions
        
        await self.ui_manager.send_menu(
            update, context, progress_text, InlineKeyboardMarkup([]), 'Markdown'
        )
    
    async def _handle_position_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result_index: int) -> None:
        """Handle position selection from search results"""
        search_results = context.user_data.get('position_search_results', [])
        
        if result_index >= len(search_results):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс результата.", duration=5
            )
            return
        
        selected_result = search_results[result_index]
        context.user_data['selected_position'] = selected_result
        
        # Show all receipt items for matching
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        text = f"**Выбрана позиция:** {selected_result['name']}\n\n"
        text += "**Выберите товар из чека для сопоставления:**\n"
        
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            button_text = f"Строка {i+1}: {match.receipt_item_name[:20]}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"match_item_{i}")])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(update, context, text, reply_markup, 'Markdown')
    
    async def _handle_position_match_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result_index: int) -> None:
        """Handle position match selection"""
        search_results = context.user_data.get('position_match_search_results', [])
        
        if result_index >= len(search_results):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс результата.", duration=5
            )
            return
        
        selected_result = search_results[result_index]
        selected_line_number = context.user_data.get('selected_line_number')
        
        if selected_line_number is None:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: не выбрана строка для сопоставления.", duration=5
            )
            return
        
        # Perform the match
        await self._perform_ingredient_match(update, context, selected_line_number - 1, selected_result)
    
    async def _handle_search_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result_index: int) -> None:
        """Handle search result selection"""
        search_results = context.user_data.get('search_results', [])
        
        if result_index >= len(search_results):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс результата.", duration=5
            )
            return
        
        selected_result = search_results[result_index]
        current_match_index = context.user_data.get('current_match_index', 0)
        
        # Perform the match
        await self._perform_ingredient_match(update, context, current_match_index, selected_result)
    
    async def _perform_ingredient_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      match_index: int, selected_result: dict) -> None:
        """Perform ingredient matching"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result or match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс сопоставления.", duration=5
            )
            return
        
        # Update the match
        match = matching_result.matches[match_index]
        match.matched_ingredient_name = selected_result['name']
        match.matched_ingredient_id = selected_result['id']
        from models.ingredient_matching import MatchStatus
        match.match_status = MatchStatus.EXACT_MATCH
        match.similarity_score = 1.0
        
        # Mark as changed
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        changed_indices.add(match_index)
        context.user_data['changed_ingredient_indices'] = changed_indices
        
        # Save to storage
        user_id = update.effective_user.id
        receipt_data = context.user_data.get('receipt_data')
        if receipt_data:
            receipt_hash = receipt_data.get_receipt_hash()
            self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, receipt_hash)
        
        # Show success message
        await self.ui_manager.send_temp(
            update, context,
            f"✅ Сопоставлено: {match.receipt_item_name} → {selected_result['name']}",
            duration=2
        )
        
        # Return to overview
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        await self._show_manual_matching_overview(update, context)
    
    async def _process_next_ingredient_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process next ingredient match or finish matching"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            return
        
        current_match_index += 1
        context.user_data['current_match_index'] = current_match_index
        
        if current_match_index >= len(matching_result.matches):
            # All matches processed, show final result
            await self._show_final_ingredient_matching_result(update, context)
        else:
            # Show next match
            await self._show_manual_matching_for_item(update, context, current_match_index)
    
    async def _show_final_ingredient_matching_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show final ingredient matching result"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        # Format final result
        from utils.ingredient_formatter import IngredientFormatter
        formatter = IngredientFormatter()
        final_text = formatter.format_matching_table(matching_result)
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, final_text, reply_markup, 'Markdown'
        )
