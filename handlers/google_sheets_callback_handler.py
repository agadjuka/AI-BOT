"""
Google Sheets callback handler for Telegram bot
"""
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus
from services.google_sheets_service import GoogleSheetsService
from services.file_generator_service import FileGeneratorService


class GoogleSheetsCallbackHandler(BaseCallbackHandler):
    """Handler for Google Sheets related callbacks"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.google_sheets_service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        self.file_generator = FileGeneratorService()
    
    async def _show_google_sheets_matching_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                               receipt_data=None, matching_result=None):
        """Show Google Sheets matching page with the same table as editor"""
        query = update.callback_query
        await query.answer()
        
        # Get data from parameters or context
        if not matching_result:
            matching_result = context.user_data.get('ingredient_matching_result')
        if not receipt_data:
            receipt_data = context.user_data.get('receipt_data')
        
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Use the same table formatting as the editor
        table_text = self._format_google_sheets_matching_table(matching_result)
        
        # Add additional text after the table
        schema_text = table_text + "\n\nВыберите действие для работы с сопоставлением:"
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton("✏️ Редактировать сопоставление", callback_data="edit_google_sheets_matching")],
            [InlineKeyboardButton("👁️ Предпросмотр", callback_data="preview_google_sheets_upload")],
            [InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Save data for future use
        context.user_data['pending_google_sheets_upload'] = {
            'receipt_data': receipt_data,
            'matching_result': matching_result
        }
        
        await query.edit_message_text(schema_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_google_sheets_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        receipt_data=None, matching_result=None):
        """Show Google Sheets upload preview with confirmation buttons"""
        query = update.callback_query
        await query.answer()
        
        # Get data from parameters or context
        if not matching_result:
            matching_result = context.user_data.get('ingredient_matching_result')
        if not receipt_data:
            receipt_data = context.user_data.get('receipt_data')
        
        if not matching_result or not receipt_data:
            await query.edit_message_text("❌ Данные для предпросмотра не найдены")
            return
        
        # Create table preview with Google Sheets data
        table_preview = self._format_google_sheets_table_preview(receipt_data, matching_result)
        
        # Text with table preview only
        text = "📊 **Предварительный просмотр загрузки в Google Таблицы**\n\n"
        text += f"```\n{table_preview}\n```"
        
        keyboard = [
            [InlineKeyboardButton("✅ Загрузить в Google Таблицы", callback_data="confirm_google_sheets_upload")],
            [InlineKeyboardButton("✏️ Редактировать сопоставление", callback_data="edit_google_sheets_matching")],
            [InlineKeyboardButton("◀️ Назад", callback_data="upload_to_google_sheets")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Save data for upload
        context.user_data['pending_google_sheets_upload'] = {
            'receipt_data': receipt_data,
            'matching_result': matching_result
        }
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_google_sheets_matching_table(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                               receipt_data=None, matching_result=None):
        """Show Google Sheets matching table for editing"""
        query = update.callback_query
        await query.answer()
        
        # Get data from parameters or pending data
        if not matching_result or not receipt_data:
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if pending_data:
                receipt_data = pending_data['receipt_data']
                matching_result = pending_data['matching_result']
            else:
                await query.edit_message_text("❌ Результаты сопоставления не найдены")
                return
        
        # Format the matching table for Google Sheets
        table_text = self._format_google_sheets_matching_table(matching_result)
        
        # Create buttons
        keyboard = []
        
        # Add buttons for items that need matching (max 2 per row)
        items_needing_matching = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status.value in ['partial', 'no_match']:
                items_needing_matching.append((i, match))
        
        for i, (index, match) in enumerate(items_needing_matching):
            # Get status emoji instead of pencil
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            button_text = f"{status_emoji} {self._truncate_name(match.receipt_item_name, 15)}"
            
            if i % 2 == 0:
                # Start new row
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_google_sheets_item_{index}")])
            else:
                # Add to existing row
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"edit_google_sheets_item_{index}"))
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Выбрать позицию для сопоставления", callback_data="select_google_sheets_position")],
            [InlineKeyboardButton("✅ Применить изменения", callback_data="apply_google_sheets_matching")],
            [InlineKeyboardButton("👁️ Предпросмотр", callback_data="preview_google_sheets_upload")],
            [InlineKeyboardButton("◀️ Назад", callback_data="upload_to_google_sheets")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, table_text, reply_markup)
    
    async def _show_google_sheets_position_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show position selection for Google Sheets matching"""
        query = update.callback_query
        await query.answer()
        
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные для сопоставления не найдены.", duration=5
            )
            return
        
        matching_result = pending_data['matching_result']
        
        # Show instruction
        text = "**Выберите позицию для сопоставления**\n\n"
        text += "Введите номер строки, которую хотите сопоставить с ингредиентом из Google Таблиц:"
        
        # Create buttons for each item
        keyboard = []
        for i, match in enumerate(matching_result.matches, 1):
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            button_text = f"{i}. {status_emoji} {self._truncate_name(match.receipt_item_name, 20)}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_line_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_google_sheets_matching")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, text, reply_markup, 'Markdown'
        )
    
    async def _show_google_sheets_manual_matching_for_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int):
        """Show manual matching interface for specific Google Sheets item"""
        query = update.callback_query
        await query.answer()
        
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные для сопоставления не найдены.", duration=5
            )
            return
        
        matching_result = pending_data['matching_result']
        
        if item_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс товара.", duration=5
            )
            return
        
        current_match = matching_result.matches[item_index]
        
        # Show current match info
        progress_text = f"**Редактор сопоставления для Google Таблиц**\n\n"
        progress_text += f"**Товар:** {current_match.receipt_item_name}\n\n"
        progress_text += "**Выберите подходящий ингредиент:**\n\n"
        
        # Get Google Sheets ingredients
        google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        
        if current_match.suggested_matches:
            # Show suggested matches
            suggestions_text = self._format_google_sheets_suggestions(current_match)
            progress_text += suggestions_text + "\n\n"
        else:
            progress_text += "❌ **Подходящих вариантов не найдено**\n\n"
        
        # Create buttons
        keyboard = []
        
        # Add suggestion buttons in two columns
        if current_match.suggested_matches:
            for i, suggestion in enumerate(current_match.suggested_matches[:6], 1):  # Show max 6 suggestions (3 rows x 2 columns)
                button_text = f"{i}. {self._truncate_name(suggestion['name'], 15)} ({int(suggestion['score'] * 100)}%)"
                if i % 2 == 1:
                    # Start new row
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_suggestion_{item_index}_{i-1}")])
                else:
                    # Add to existing row
                    keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_suggestion_{item_index}_{i-1}"))
        
        # Add search and control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Поиск", callback_data=f"search_google_sheets_ingredient_{item_index}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_google_sheets_matching")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, progress_text, reply_markup, 'Markdown'
        )

    def _format_google_sheets_suggestions(self, match) -> str:
        """Format Google Sheets suggestions for manual matching"""
        if not match.suggested_matches:
            return "Нет предложений"
        
        lines = []
        for i, suggestion in enumerate(match.suggested_matches[:5], 1):  # Show max 5 suggestions
            name = self._truncate_name(suggestion['name'], 25)
            score = int(suggestion['score'] * 100)
            lines.append(f"{i}. {name} ({score}%)")
        
        return "\n".join(lines)
    
    async def _handle_google_sheets_suggestion_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       item_index: int, suggestion_index: int):
        """Handle Google Sheets suggestion selection"""
        query = update.callback_query
        await query.answer("✅ Сопоставление обновлено!")
        
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные для сопоставления не найдены.", duration=5
            )
            return
        
        matching_result = pending_data['matching_result']
        
        if item_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс товара.", duration=5
            )
            return
        
        current_match = matching_result.matches[item_index]
        
        if not current_match.suggested_matches or suggestion_index >= len(current_match.suggested_matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс предложения.", duration=5
            )
            return
        
        # Get selected suggestion
        selected_suggestion = current_match.suggested_matches[suggestion_index]
        
        # Update the match
        current_match.matched_ingredient_name = selected_suggestion['name']
        current_match.matched_ingredient_id = selected_suggestion['id']
        from models.ingredient_matching import MatchStatus
        current_match.match_status = MatchStatus.EXACT_MATCH
        current_match.similarity_score = selected_suggestion['score']
        
        # Show success message
        await self.ui_manager.send_temp(
            update, context,
            f"✅ Сопоставлено: {current_match.receipt_item_name} → {selected_suggestion['name']}",
            duration=2
        )
        
        # Return to Google Sheets matching table (editor) with updated data
        await self._show_google_sheets_matching_table(update, context, 
            pending_data['receipt_data'], matching_result)
    
    async def _handle_google_sheets_search_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                   item_index: int, result_index: int):
        """Handle Google Sheets search result selection"""
        query = update.callback_query
        await query.answer("✅ Сопоставление обновлено!")
        
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные для сопоставления не найдены.", duration=5
            )
            return
        
        matching_result = pending_data['matching_result']
        
        if item_index >= len(matching_result.matches):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс товара.", duration=5
            )
            return
        
        current_match = matching_result.matches[item_index]
        
        # Get search results from user data
        search_results = context.user_data.get('google_sheets_search_results', [])
        if not search_results or result_index >= len(search_results):
            await self.ui_manager.send_temp(
                update, context, "Ошибка: неверный индекс результата поиска.", duration=5
            )
            return
        
        # Get selected search result
        selected_result = search_results[result_index]
        
        # Update the match
        current_match.matched_ingredient_name = selected_result['name']
        current_match.matched_ingredient_id = selected_result.get('id', '')
        from models.ingredient_matching import MatchStatus
        current_match.match_status = MatchStatus.EXACT_MATCH
        current_match.similarity_score = 1.0  # Exact match from search
        
        # Clear search data
        context.user_data.pop('google_sheets_search_results', None)
        context.user_data.pop('google_sheets_search_mode', None)
        context.user_data.pop('google_sheets_search_item_index', None)
        
        # Show success message
        await self.ui_manager.send_temp(
            update, context,
            f"✅ Сопоставлено: {current_match.receipt_item_name} → {selected_result['name']}",
            duration=2
        )
        
        # Return to Google Sheets matching table (editor) with updated data
        await self._show_google_sheets_matching_table(update, context, 
            pending_data['receipt_data'], matching_result)
    
    async def _handle_skip_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle skipping current item"""
        query = update.callback_query
        await query.answer()
        
        # Get current item index
        current_item = context.user_data.get('current_gs_matching_item', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result or current_item >= len(matching_result.matches):
            await query.edit_message_text("❌ Неверный индекс позиции")
            return
        
        # Mark as skipped
        match = matching_result.matches[current_item]
        match.match_status = MatchStatus.NO_MATCH
        match.matched_ingredient_name = "Пропущено"
        match.matched_ingredient_id = None
        match.similarity_score = 0.0
        
        # Update changed indices
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        changed_indices.add(current_item)
        context.user_data['changed_ingredient_indices'] = changed_indices
        
        # Save updated matching result
        self._save_ingredient_matching_data(update.effective_user.id, context)
        
        # Show success message
        success_text = f"⏭️ **Позиция пропущена!**\n\n"
        success_text += f"📝 **Товар:** {match.receipt_item_name}\n"
        success_text += f"❌ **Статус:** Пропущено\n\n"
        success_text += "Переходим к следующей позиции..."
        
        keyboard = [
            [InlineKeyboardButton("➡️ Следующая позиция", callback_data="gs_next_item")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_google_sheets_matching")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_next_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle moving to next item"""
        query = update.callback_query
        await query.answer()
        
        # Get current item index
        current_item = context.user_data.get('current_gs_matching_item', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Move to next item
        next_item = current_item + 1
        
        if next_item >= len(matching_result.matches):
            # All items processed, return to matching table
            await self._show_google_sheets_matching_table(update, context)
            return
        
        # Update current item index
        context.user_data['current_gs_matching_item'] = next_item
        
        # Show next item
        await self._show_google_sheets_manual_matching_for_item(update, context, next_item)
    
    async def _upload_to_google_sheets(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     matching_result: IngredientMatchingResult):
        """Upload matching result to Google Sheets"""
        query = update.callback_query
        await query.answer()
        
        print(f"DEBUG: _upload_to_google_sheets called with matching_result: {matching_result}")
        
        try:
            # Show uploading message
            await query.edit_message_text("📤 Загружаем данные в Google Sheets...")
            
            # Upload to Google Sheets
            receipt_data = context.user_data.get('receipt_data')
            if receipt_data:
                success, message = self.google_sheets_service.upload_receipt_data(receipt_data, matching_result)
            else:
                success = False
                message = "Receipt data not found"
            
            if success:
                # Show success page with full functionality
                await self._show_upload_success_page(update, context, "Upload successful", message)
            else:
                await query.edit_message_text(f"❌ Ошибка при загрузке: {message}")
                
        except Exception as e:
            print(f"DEBUG: Error uploading to Google Sheets: {e}")
            await query.edit_message_text(f"❌ Ошибка при загрузке: {str(e)}")
    
    def _format_google_sheets_table_preview(self, receipt_data, matching_result) -> str:
        """Format table preview for Google Sheets upload"""
        if not receipt_data.items or not matching_result.matches:
            return "Нет данных для отображения"
        
        # Set fixed column widths (total max 58 characters)
        date_width = 8        # Fixed width for date
        volume_width = 6      # Fixed width for volume
        price_width = 10      # Fixed width for price
        product_width = 22    # Fixed width for product
        
        # Create header using the new format
        header = f"{'Date':<{date_width}} | {'Vol':<{volume_width}} | {'цена':<{price_width}} | {'Product':<{product_width}}"
        separator = "─" * (date_width + volume_width + price_width + product_width + 12)  # 12 characters for separators
        
        lines = [header, separator]
        
        # Add data rows using the new format
        for i, item in enumerate(receipt_data.items):
            # Get matching result for this item
            match = None
            if i < len(matching_result.matches):
                match = matching_result.matches[i]
            
            # Prepare row data
            current_date = datetime.now().strftime('%d.%m.%Y')
            quantity = item.quantity if item.quantity is not None else 0
            price = item.price if item.price is not None else 0
            matched_product = match.matched_ingredient_name if match and match.matched_ingredient_name else ""
            
            # Extract volume from product name and multiply by quantity
            volume_from_name = self._extract_volume_from_name(item.name)
            if volume_from_name > 0:
                # Multiply extracted volume by quantity
                total_volume = volume_from_name * quantity
                if total_volume == int(total_volume):
                    volume_str = str(int(total_volume))
                else:
                    # Round to 2 decimal places
                    volume_str = f"{total_volume:.2f}"
            elif quantity > 0:
                # Fallback to original behavior if no volume found in name
                if quantity == int(quantity):
                    volume_str = str(int(quantity))
                else:
                    # Round to 2 decimal places
                    volume_str = f"{quantity:.2f}"
            else:
                volume_str = "-"
            
            # Format price using the same format as other tables (with spaces)
            if price > 0:
                if price == int(price):
                    price_str = f"{int(price):,}".replace(",", " ")
                else:
                    price_str = f"{price:,.1f}".replace(",", " ")
            else:
                price_str = "-"
            
            # Handle long product names with word wrapping
            matched_product_parts = self._wrap_text(matched_product, product_width)
            
            # Create multiple lines if product name is wrapped
            for line_idx in range(len(matched_product_parts)):
                current_product = matched_product_parts[line_idx]
                
                # Only show date, volume, and price on first line
                if line_idx == 0:
                    line = f"{current_date:<{date_width}} | {volume_str:<{volume_width}} | {price_str:<{price_width}} | {current_product:<{product_width}}"
                else:
                    line = f"{'':<{date_width}} | {'':<{volume_width}} | {'':<{price_width}} | {current_product:<{product_width}}"
                
                lines.append(line)
        
        return "\n".join(lines)
    
    def _format_google_sheets_matching_table(self, matching_result: IngredientMatchingResult) -> str:
        """Format Google Sheets matching table for editing"""
        if not matching_result.matches:
            return "Нет ингредиентов для сопоставления."
        
        # Create table header
        table_lines = []
        table_lines.append("**Сопоставление с ингредиентами Google Таблиц:**\n")
        
        # Add summary
        summary = f"📊 **Статистика:** Всего: {matching_result.total_items} | "
        summary += f"🟢 Точных: {matching_result.exact_matches} | "
        summary += f"🟡 Частичных: {matching_result.partial_matches} | "
        summary += f"🔴 Не найдено: {matching_result.no_matches}\n"
        table_lines.append(summary)
        
        # Create table
        table_lines.append("```")
        table_lines.append(self._create_google_sheets_table_header())
        table_lines.append(self._create_google_sheets_table_separator())
        
        # Add table rows
        for i, match in enumerate(matching_result.matches, 1):
            table_lines.append(self._create_google_sheets_table_row(i, match))
        
        table_lines.append("```")
        
        return "\n".join(table_lines)
    
    def _create_google_sheets_table_header(self) -> str:
        """Create Google Sheets table header"""
        return f"{'№':<2} | {'Наименование':<20} | {'Google Таблицы':<20} | {'Статус':<4}"
    
    def _create_google_sheets_table_separator(self) -> str:
        """Create Google Sheets table separator"""
        return "-" * 50
    
    def _create_google_sheets_table_row(self, row_number: int, match: IngredientMatch) -> str:
        """Create a Google Sheets table row for a match"""
        # Wrap names instead of truncating
        receipt_name_lines = self._wrap_text(match.receipt_item_name, 20)
        ingredient_name_lines = self._wrap_text(
            match.matched_ingredient_name or "—", 
            20
        )
        
        # Get status emoji
        status_emoji = self._get_google_sheets_status_emoji(match.match_status)
        
        # Create multi-line row
        max_lines = max(len(receipt_name_lines), len(ingredient_name_lines))
        lines = []
        
        for line_idx in range(max_lines):
            receipt_name = receipt_name_lines[line_idx] if line_idx < len(receipt_name_lines) else ""
            ingredient_name = ingredient_name_lines[line_idx] if line_idx < len(ingredient_name_lines) else ""
            
            if line_idx == 0:
                # First line includes row number and status
                line = f"{row_number:<2} | {receipt_name:<20} | {ingredient_name:<20} | {status_emoji:<4}"
            else:
                # Subsequent lines are indented
                line = f"{'':<2} | {receipt_name:<20} | {ingredient_name:<20} | {'':<4}"
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def _get_google_sheets_status_emoji(self, status) -> str:
        """Get emoji for Google Sheets match status"""
        if status == MatchStatus.EXACT_MATCH:
            return "🟢"
        elif status == MatchStatus.PARTIAL_MATCH:
            return "🟡"
        else:
            return "🔴"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simple implementation)"""
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    async def _ensure_google_sheets_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Ensure Google Sheets ingredients are loaded, load them if necessary"""
        google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        
        if not google_sheets_ingredients:
            # Load Google Sheets ingredients from config (same as original backup)
            from google_sheets_handler import get_google_sheets_ingredients
            google_sheets_ingredients = get_google_sheets_ingredients()
            
            if not google_sheets_ingredients:
                return False
            
            # Save Google Sheets ingredients to bot data for future use
            context.bot_data["google_sheets_ingredients"] = google_sheets_ingredients
            print(f"✅ Загружено {len(google_sheets_ingredients)} ингредиентов Google Sheets по требованию")
            print(f"DEBUG: Первые 5 ингредиентов: {list(google_sheets_ingredients.keys())[:5]}")
        
        return True
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name to max length"""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
    
    def _extract_volume_from_name(self, name: str) -> float:
        """Extract volume/weight from product name and convert to base units (kg/l)"""
        import re
        
        if not name:
            return 0.0
        
        # Patterns to match various volume/weight indicators with conversion factors
        patterns = [
            # Base units (kg, l) - no conversion needed
            (r'(\d+[,.]?\d*)\s*kg', 1.0),  # kg (with comma or dot as decimal separator)
            (r'(\d+[,.]?\d*)\s*кг', 1.0),  # кг (Russian)
            (r'(\d+[,.]?\d*)\s*l', 1.0),   # liters
            (r'(\d+[,.]?\d*)\s*л', 1.0),   # литры (Russian)
            # Small units (g, ml) - convert to base units (multiply by 0.001)
            (r'(\d+[,.]?\d*)\s*ml', 0.001),  # milliliters -> liters
            (r'(\d+[,.]?\d*)\s*мл', 0.001),  # миллилитры -> литры (Russian)
            (r'(\d+[,.]?\d*)\s*g', 0.001),   # grams -> kg
            (r'(\d+[,.]?\d*)\s*г', 0.001),   # граммы -> кг (Russian)
        ]
        
        for pattern, conversion_factor in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                volume_str = match.group(1)
                # Replace comma with dot for proper float conversion
                volume_str = volume_str.replace(',', '.')
                try:
                    volume = float(volume_str)
                    return volume * conversion_factor
                except ValueError:
                    continue
        
        return 0.0
    
    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width, breaking on words when possible"""
        if not text:
            return [""]
        
        if len(text) <= max_width:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # If adding this word would exceed the width
            if len(current_line) + len(word) + 1 > max_width:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, split it with hyphen
                    lines.append(word[:max_width-1] + "-")
                    current_line = word[max_width-1:]
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _save_ingredient_matching_data(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Save ingredient matching data to storage"""
        try:
            matching_result = context.user_data.get('ingredient_matching_result')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if matching_result:
                receipt_data = context.user_data.get('receipt_data')
                if receipt_data:
                    receipt_hash = receipt_data.get_receipt_hash()
                    self.ingredient_storage.save_matching_result(user_id, receipt_hash, matching_result, changed_indices)
                    print(f"DEBUG: Saved matching data for user {user_id}, receipt {receipt_hash}")
        except Exception as e:
            print(f"DEBUG: Error saving matching data: {e}")
    
    async def _show_upload_success_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      summary: str, message: str):
        """Show the new upload success page interface"""
        query = update.callback_query
        await query.answer()
        
        # Create success message with only the header
        success_text = "✅ **Данные успешно загружены в Google Sheets!**"
        
        # Create new button layout
        keyboard = [
            [InlineKeyboardButton("↩️ Отменить загрузку", callback_data="undo_google_sheets_upload")],
            [InlineKeyboardButton("📄 Сгенерировать файл", callback_data="generate_excel_file")],
            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
            [InlineKeyboardButton("📸 Загрузить новый чек", callback_data="start_new_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _generate_excel_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate Excel file from matching result"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        try:
            # Show generating message
            await query.edit_message_text("📁 Генерируем Excel файл...")
            
            # Generate Excel file
            excel_file = await self.file_generator.generate_excel_file(matching_result)
            
            if excel_file:
                # Send file
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=excel_file,
                    filename=f"ingredient_matching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    caption="📊 **Файл сопоставления ингредиентов**\n\n"
                           "Excel файл с результатами сопоставления ингредиентов из чека с Google Sheets."
                )
                
                # Show success message
                await query.edit_message_text(
                    "✅ **Excel файл успешно создан!**\n\n"
                    "Файл отправлен в чат.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="gs_show_table")]
                    ])
                )
            else:
                await query.edit_message_text("❌ Ошибка при создании Excel файла")
                
        except Exception as e:
            print(f"DEBUG: Error generating Excel file: {e}")
            await query.edit_message_text(f"❌ Ошибка при создании Excel файла: {str(e)}")
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        if len(text) <= self.config.MAX_MESSAGE_LENGTH:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Split into parts
        parts = [text[i:i + self.config.MAX_MESSAGE_LENGTH] for i in range(0, len(text), self.config.MAX_MESSAGE_LENGTH)]
        
        # Send all parts except last
        for part in parts[:-1]:
            await message.reply_text(part, parse_mode='Markdown')
            await asyncio.sleep(self.config.MESSAGE_DELAY)
        
        # Send last part with keyboard
        await message.reply_text(parts[-1], reply_markup=reply_markup, parse_mode='Markdown')
