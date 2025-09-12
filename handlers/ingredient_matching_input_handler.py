"""
Ingredient matching input handling for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.receipt import ReceiptData
from models.ingredient_matching import IngredientMatchingResult
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import LocaleManager


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
            print(f"Failed to delete user message: {e}")
        
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
        
        # Get user's personal ingredients from Firestore
        from services.ingredients_manager import get_ingredients_manager
        ingredients_manager = get_ingredients_manager()
        user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
        
        # Convert to matching format
        google_sheets_ingredients = {}
        for i, ingredient_name in enumerate(user_ingredients):
            google_sheets_ingredients[ingredient_name] = f"user_ingredient_{i}"
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.matching_data_not_found", context), duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        current_match = matching_result.matches[current_match_index]
        
        try:
            if user_input == "0":
                # Skip this ingredient
                await self.ui_manager.send_temp(
                    update, context, self.locale_manager.get_text("matching.ingredient_skipped", context, ingredient_name=current_match.receipt_item_name), duration=2
                )
                await self._process_next_ingredient_match(update, context)
                
            elif user_input.startswith("search:"):
                # Search for ingredients
                query = user_input[7:].strip()
                if not query:
                    await self.ui_manager.send_temp(
                        update, context, self.locale_manager.get_text("matching.enter_search_query", context), duration=5
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
                            google_sheets_ingredients
                        )
                        
                        # Update the match in the result
                        matching_result.matches[current_match_index] = manual_match
                        context.user_data['ingredient_matching_result'] = matching_result
                        
                        await self.ui_manager.send_temp(
                            update, context, self.locale_manager.get_text("matching.ingredient_matched", context, receipt_item=current_match.receipt_item_name, matched_ingredient=selected_suggestion['name']), duration=2
                        )
                        await self._process_next_ingredient_match(update, context)
                        
                    else:
                        await self.ui_manager.send_temp(
                            update, context, self.locale_manager.get_text("matching.invalid_suggestion_number", context, max_number=len(current_match.suggested_matches)), duration=5
                        )
                        return self.config.AWAITING_MANUAL_MATCH
                        
                except ValueError:
                    await self.ui_manager.send_temp(
                        update, context, self.locale_manager.get_text("matching.invalid_format", context), duration=5
                    )
                    return self.config.AWAITING_MANUAL_MATCH
                    
        except Exception as e:
            print(f"Error processing manual matching: {e}")
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.try_again", context), duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_position_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
        """Handle position search for manual matching"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        # Get user's personal ingredients from Firestore
        from services.ingredients_manager import get_ingredients_manager
        ingredients_manager = get_ingredients_manager()
        user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
        
        # Convert to matching format
        google_sheets_ingredients = {}
        for i, ingredient_name in enumerate(user_ingredients):
            google_sheets_ingredients[ingredient_name] = f"user_ingredient_{i}"
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.matching_data_not_found", context), duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        # Search for ingredients in the loaded list
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            query, google_sheets_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                search_text = self.locale_manager.get_text("matching.search_results_title", context, query=query)
                search_text += self.locale_manager.get_text("matching.found_variants", context, count=len(filtered_results))
                search_text += self.locale_manager.get_text("matching.select_ingredient", context)
                
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
                    [InlineKeyboardButton(self.locale_manager.get_text("matching.new_search", context), callback_data="select_position_for_matching")],
                    [InlineKeyboardButton(self.locale_manager.get_text("matching.back_to_receipt", context), callback_data="back_to_receipt")]
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
                    self.locale_manager.get_text("matching.no_suitable_variants", context, query=query),
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton(self.locale_manager.get_text("matching.new_search", context), callback_data="select_position_for_matching")],
                        [InlineKeyboardButton(self.locale_manager.get_text("matching.back_to_receipt", context), callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
        else:
            await self.ui_manager.send_menu(
                update, context,
                self.locale_manager.get_text("matching.nothing_found", context, query=query),
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(self.locale_manager.get_text("matching.new_search", context), callback_data="select_position_for_matching")],
                    [InlineKeyboardButton(self.locale_manager.get_text("matching.back_to_receipt", context), callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
        
        return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_ingredient_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> int:
        """Handle ingredient search"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        # Get user's personal ingredients from Firestore
        from services.ingredients_manager import get_ingredients_manager
        ingredients_manager = get_ingredients_manager()
        user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
        
        # Convert to matching format
        google_sheets_ingredients = {}
        for i, ingredient_name in enumerate(user_ingredients):
            google_sheets_ingredients[ingredient_name] = f"user_ingredient_{i}"
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.matching_data_not_found", context), duration=5
            )
            return self.config.AWAITING_CORRECTION
        
        current_match = matching_result.matches[current_match_index]
        
        # Search for ingredients
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            query, google_sheets_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                progress_text = self.locale_manager.get_text("matching.search_results_title", context, query=query)
                progress_text += self.locale_manager.get_text("matching.current_item", context, item_name=current_match.receipt_item_name)
                progress_text += self.locale_manager.get_text("matching.select_ingredient", context)
                
                # Create buttons for search results (max 4 buttons)
                keyboard = []
                for i, result in enumerate(filtered_results[:4], 1):
                    name = self._truncate_name(result['name'], 20)
                    score = int(result['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_search_{i}")])
                
                # Add control buttons
                keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("matching.new_search", context), callback_data="search_ingredient")])
                keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("matching.skip_ingredient", context), callback_data="skip_ingredient")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.ui_manager.send_menu(
                    update, context, progress_text, reply_markup, 'Markdown'
                )
                
                # Save search results for selection
                context.user_data['search_results'] = filtered_results
            else:
                await self.ui_manager.send_temp(
                    update, context, self.locale_manager.get_text("matching.no_suitable_results", context, query=query), duration=5
                )
        else:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.search_nothing_found", context, query=query), duration=5
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
                    update, context, self.locale_manager.get_text("matching.invalid_line_number", context, max_lines=len(matching_result.matches) if matching_result else 0), duration=5
                )
                return self.config.AWAITING_MANUAL_MATCH
            
            # Set the selected line number for position matching
            context.user_data['selected_line_number'] = line_number
            
            # Clear position selection mode flag
            context.user_data.pop('in_position_selection_mode', None)
            
            # Show instruction to enter ingredient name
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.line_selected", context, line_number=line_number), duration=10
            )
            context.user_data['awaiting_ingredient_name_for_position'] = True
            
            return self.config.AWAITING_MANUAL_MATCH
            
        except ValueError:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.invalid_line_format", context), duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
    
    async def _handle_ingredient_name_for_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str) -> int:
        """Handle ingredient name input for position matching"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        # Get user's personal ingredients from Firestore
        from services.ingredients_manager import get_ingredients_manager
        ingredients_manager = get_ingredients_manager()
        user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
        
        # Convert to matching format
        google_sheets_ingredients = {}
        for i, ingredient_name in enumerate(user_ingredients):
            google_sheets_ingredients[ingredient_name] = f"user_ingredient_{i}"
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("matching.matching_data_not_found", context), duration=5
            )
            return self.config.AWAITING_MANUAL_MATCH
        
        # Search for ingredients in the loaded list
        search_results = self.ingredient_matching_service.get_similar_ingredients(
            user_input, google_sheets_ingredients, limit=10
        )
        
        if search_results:
            # Filter results with score >= 50%
            filtered_results = [r for r in search_results if r['score'] >= 0.5]
            
            if filtered_results:
                # Show search results with buttons
                search_text = self.locale_manager.get_text("matching.search_results_title", context, query=user_input)
                search_text += self.locale_manager.get_text("matching.found_variants", context, count=len(filtered_results))
                search_text += self.locale_manager.get_text("matching.select_ingredient", context)
                
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
                    [InlineKeyboardButton(self.locale_manager.get_text("matching.back", context), callback_data="back_to_receipt")]
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
                    self.locale_manager.get_text("matching.no_suitable_variants", context, query=user_input),
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton(self.locale_manager.get_text("matching.back", context), callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
        else:
            await self.ui_manager.send_menu(
                update, context,
                self.locale_manager.get_text("matching.nothing_found", context, query=user_input),
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(self.locale_manager.get_text("matching.back", context), callback_data="back_to_receipt")]
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
        progress_text = self.locale_manager.get_text("matching.matching_progress", context, current=current_match_index + 1, total=len(matching_result.matches))
        progress_text += self.locale_manager.get_text("matching.current_item", context, item_name=current_match.receipt_item_name)
        
        if current_match.match_status.value == "exact":
            # Already matched, show confirmation
            progress_text += self.locale_manager.get_text("matching.auto_matched", context, ingredient_name=current_match.matched_ingredient_name)
            progress_text += self.locale_manager.get_text("matching.continue_instruction", context)
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
                update, context, self.locale_manager.get_text("matching.matching_data_not_found", context), duration=5
            )
            return
        
        # Format final result
        final_text = self.ingredient_formatter.format_matching_table(matching_result)
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton(self.locale_manager.get_text("matching.rematch_ingredients", context), callback_data="rematch_ingredients")],
            [InlineKeyboardButton(self.locale_manager.get_text("matching.back_to_receipt_final", context), callback_data="back_to_receipt")]
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
