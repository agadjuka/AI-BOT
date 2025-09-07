"""
Ingredient matching input handling for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.receipt import ReceiptData
from models.ingredient_matching import IngredientMatchingResult
from handlers.base_message_handler import BaseMessageHandler


class IngredientMatchingInputHandler(BaseMessageHandler):
    """Handler for ingredient matching input processing"""
    
    async def handle_ingredient_matching_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle manual ingredient matching input"""
        user_input = update.message.text.strip()
        
        # Delete user message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение пользователя: {e}")
        
        # Check if we're waiting for search input
        if context.user_data.get('awaiting_search'):
            context.user_data.pop('awaiting_search', None)
            return await self._handle_ingredient_search(update, context, user_input)
        
        # Check if we're waiting for position search input
        if context.user_data.get('awaiting_position_search'):
            context.user_data.pop('awaiting_position_search', None)
            return await self._handle_position_search(update, context, user_input)
        
        # Check if we're waiting for line number input for position matching
        if context.user_data.get('awaiting_line_number_for_position'):
            context.user_data.pop('awaiting_line_number_for_position', None)
            return await self._handle_line_number_for_position(update, context, user_input)
        
        # Check if we're waiting for ingredient name input for position matching
        if context.user_data.get('awaiting_ingredient_name_for_position'):
            context.user_data.pop('awaiting_ingredient_name_for_position', None)
            return await self._handle_ingredient_name_for_position(update, context, user_input)
        
        # Check if we're in position selection mode and user entered a line number
        if context.user_data.get('in_position_selection_mode'):
            return await self._handle_line_number_for_position(update, context, user_input)
        
        # Get current matching data
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        current_match = matching_result.matches[current_match_index]
        
        try:
            if user_input == "0":
                # Skip this ingredient
                await self.ui_manager.send_temp(
                    update, context, f"✅ Пропущен ингредиент: {current_match.receipt_item_name}", duration=2
                )
                await self._process_next_ingredient_match(update, context)
                
            elif user_input.startswith("search:"):
                # Search for ingredients
                query = user_input[7:].strip()
                if not query:
                    await self.ui_manager.send_temp(
                        update, context, "Введите поисковый запрос после 'search:'", duration=5
                    )
                    return self.config.AWAITING_MANUAL_MATCH
                
                return await self._handle_ingredient_search(update, context, query)
                
            else:
                # Try to parse as suggestion number
                try:
                    suggestion_number = int(user_input)
                    if 1 <= suggestion_number <= len(current_match.suggested_matches):
                        # Apply suggestion
                        selected_suggestion = current_match.suggested_matches[suggestion_number - 1]
                        manual_match = self.ingredient_matching_service.manual_match_ingredient(
                            current_match.receipt_item_name,
                            selected_suggestion['id'],
                            poster_ingredients
                        )
                        
                        # Update the match in the result
                        matching_result.matches[current_match_index] = manual_match
                        context.user_data['ingredient_matching_result'] = matching_result
                        
                        await self.ui_manager.send_temp(
                            update, context, f"✅ Сопоставлено: {current_match.receipt_item_name} → {selected_suggestion['name']}", duration=2
                        )
                        await self._process_next_ingredient_match(update, context)
                        
                    else:
                        await self.ui_manager.send_temp(
                            update, context, f"Неверный номер. Введите число от 1 до {len(current_match.suggested_matches)} или 0 для пропуска.", duration=5
                        )
                        return self.config.AWAITING_MANUAL_MATCH
                        
                except ValueError:
                    await self.ui_manager.send_temp(
                        update, context, "Неверный формат. Введите номер предложения, 0 для пропуска или 'search: запрос' для поиска.", duration=5
                    )
                    return self.config.AWAITING_MANUAL_MATCH
                    
        except Exception as e:
            print(f"Ошибка при обработке ручного сопоставления: {e}")
            await self.ui_manager.send_temp(
                update, context, "Произошла ошибка. Попробуйте еще раз.", duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_position_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
        """Handle position search for manual matching"""
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Search for ingredients in the loaded list
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            query, poster_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                search_text = f"**Результаты поиска для '{query}':**\n\n"
                search_text += f"Найдено вариантов: **{len(filtered_results)}**\n\n"
                search_text += "**Выберите ингредиент для сопоставления:**\n"
                
                # Create horizontal buttons for search results (max 2 per row)
                keyboard = []
                for i, result in enumerate(filtered_results[:8], 1):  # Show up to 8 results
                    name = self._truncate_name(result['name'], 15)
                    score = int(result['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    
                    if i % 2 == 1:
                        # Start new row
                        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_position_{i}")])
                    else:
                        # Add to existing row
                        keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_position_{i}"))
                
                # Add control buttons
                keyboard.extend([
                    [InlineKeyboardButton("🔍 Новый поиск", callback_data="select_position_for_matching")],
                    [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_receipt")]
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.ui_manager.send_menu(
                    update, context, search_text, reply_markup, 'Markdown'
                )
                
                # Save search results for selection
                context.user_data['position_search_results'] = filtered_results
            else:
                await self.ui_manager.send_menu(
                    update, context,
                    f"❌ **По запросу '{query}' не найдено подходящих вариантов**\n\n"
                    "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Новый поиск", callback_data="select_position_for_matching")],
                        [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
        else:
            await self.ui_manager.send_menu(
                update, context,
                f"❌ **По запросу '{query}' ничего не найдено**\n\n"
                "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Новый поиск", callback_data="select_position_for_matching")],
                    [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_ingredient_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
        """Handle ingredient search"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        current_match = matching_result.matches[current_match_index]
        
        # Search for ingredients
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            query, poster_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                progress_text = f"**Результаты поиска для '{query}':**\n\n"
                progress_text += f"**Текущий товар:** {current_match.receipt_item_name}\n\n"
                progress_text += "**Выберите подходящий ингредиент:**\n"
                
                # Create buttons for search results (max 4 buttons)
                keyboard = []
                for i, result in enumerate(filtered_results[:4], 1):
                    name = self._truncate_name(result['name'], 20)
                    score = int(result['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_search_{i}")])
                
                # Add control buttons
                keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="search_ingredient")])
                keyboard.append([InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_ingredient")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.ui_manager.send_menu(
                    update, context, progress_text, reply_markup, 'Markdown'
                )
                
                # Save search results for selection
                context.user_data['search_results'] = filtered_results
            else:
                await self.ui_manager.send_temp(
                    update, context, f"По запросу '{query}' не найдено подходящих вариантов (с вероятностью > 50%).", duration=5
                )
        else:
            await self.ui_manager.send_temp(
                update, context, f"По запросу '{query}' ничего не найдено.", duration=5
            )
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_line_number_for_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle line number input for position matching"""
        try:
            line_number = int(user_input)
            
            # Check if line number is valid
            matching_result = context.user_data.get('ingredient_matching_result')
            if not matching_result or line_number < 1 or line_number > len(matching_result.matches):
                await self.ui_manager.send_temp(
                    update, context, f"Неверный номер строки. Введите число от 1 до {len(matching_result.matches) if matching_result else 0}", duration=5
                )
                return self.config.AWAITING_MANUAL_MATCH
            
            # Set the selected line number for position matching
            context.user_data['selected_line_number'] = line_number
            
            # Clear position selection mode flag
            context.user_data.pop('in_position_selection_mode', None)
            
            # Show instruction to enter ingredient name
            await self.ui_manager.send_temp(
                update, context, f"Выбрана строка {line_number}. Теперь введите название ингредиента из постер для поиска:", duration=10
            )
            context.user_data['awaiting_ingredient_name_for_position'] = True
            
            return self.config.AWAITING_MANUAL_MATCH
            
        except ValueError:
            await self.ui_manager.send_temp(
                update, context, "Неверный формат. Введите только номер строки (например: `3`):", duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_ingredient_name_for_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle ingredient name input for position matching"""
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
        
        # Search for ingredients in the loaded list
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            user_input, poster_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                search_text = f"**Результаты поиска для '{user_input}':**\n\n"
                search_text += f"Найдено вариантов: **{len(filtered_results)}**\n\n"
                search_text += "**Выберите ингредиент для сопоставления:**\n"
                
                # Create horizontal buttons for search results (max 2 per row)
                keyboard = []
                for i, result in enumerate(filtered_results[:8], 1):  # Show up to 8 results
                    name = self._truncate_name(result['name'], 15)
                    score = int(result['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    
                    if i % 2 == 1:
                        # Start new row
                        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_position_match_{i}")])
                    else:
                        # Add to existing row
                        keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_position_match_{i}"))
                
                # Add control buttons
                keyboard.extend([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.ui_manager.send_menu(
                    update, context, search_text, reply_markup, 'Markdown'
                )
                
                # Save search results for selection
                context.user_data['position_match_search_results'] = filtered_results
            else:
                await self.ui_manager.send_menu(
                    update, context,
                    f"❌ **По запросу '{user_input}' не найдено подходящих вариантов**\n\n"
                    "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
        else:
            await self.ui_manager.send_menu(
                update, context,
                f"❌ **По запросу '{user_input}' ничего не найдено**\n\n"
                "Попробуйте другой поисковый запрос или вернитесь к обзору.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _process_next_ingredient_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await self._show_manual_matching_for_current_item(update, context)
    
    async def _show_manual_matching_for_current_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching interface for current item"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            return
        
        current_match = matching_result.matches[current_match_index]
        
        # Show current match info
        progress_text = f"**Сопоставление ингредиентов** ({current_match_index + 1}/{len(matching_result.matches)})\n\n"
        progress_text += f"**Текущий товар:** {current_match.receipt_item_name}\n\n"
        
        if current_match.match_status.value == "exact":
            # Already matched, show confirmation
            progress_text += f"✅ **Автоматически сопоставлено:** {current_match.matched_ingredient_name}\n\n"
            progress_text += "Нажмите /continue для перехода к следующему товару."
        else:
            # Show suggestions for manual matching
            if current_match.suggested_matches:
                suggestions_text = self.ingredient_formatter.format_suggestions_for_manual_matching(current_match)
                progress_text += suggestions_text + "\n\n"
            
            instructions = self.ingredient_formatter.format_manual_matching_instructions()
            progress_text += instructions
        
        await self.ui_manager.send_menu(
            update, context, progress_text, InlineKeyboardMarkup([]), 'Markdown'
        )
    
    async def _show_final_ingredient_matching_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final ingredient matching result"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        # Format final result
        final_text = self.ingredient_formatter.format_matching_table(matching_result)
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, final_text, reply_markup, 'Markdown'
        )
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name if too long"""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
