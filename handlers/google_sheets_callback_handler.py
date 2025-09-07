"""
Google Sheets callback handler for Telegram bot
"""
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
                                               page: int = 0, items_per_page: int = 10):
        """Show Google Sheets matching page"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Calculate pagination
        total_items = len(matching_result.matches)
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        
        # Format page content
        page_text = f"📊 **Google Sheets сопоставление (стр. {page + 1})**\n\n"
        
        for i in range(start_idx, end_idx):
            match = matching_result.matches[i]
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            item_text = f"{i+1}. {status_emoji} {match.receipt_item_name[:30]}{'...' if len(match.receipt_item_name) > 30 else ''}"
            if match.matched_ingredient_name:
                item_text += f"\n   → {match.matched_ingredient_name[:25]}{'...' if len(match.matched_ingredient_name) > 25 else ''}"
            page_text += item_text + "\n\n"
        
        # Create pagination buttons
        keyboard = []
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"gs_page_{page-1}"))
        nav_buttons.append(InlineKeyboardButton(f"{page + 1}", callback_data="gs_current_page"))
        if end_idx < total_items:
            nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"gs_page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Action buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Ручное сопоставление", callback_data="gs_manual_matching")],
            [InlineKeyboardButton("📤 Загрузить в Google Sheets", callback_data="gs_upload")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_edit")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(page_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_google_sheets_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        matching_result: IngredientMatchingResult):
        """Show Google Sheets preview"""
        query = update.callback_query
        await query.answer()
        
        # Format preview table
        preview_text = self._format_google_sheets_table_preview(matching_result)
        
        keyboard = [
            [InlineKeyboardButton("📤 Загрузить в Google Sheets", callback_data="gs_upload")],
            [InlineKeyboardButton("◀️ Назад", callback_data="gs_matching_page")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, preview_text, reply_markup)
    
    async def _show_google_sheets_matching_table(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                               matching_result: IngredientMatchingResult):
        """Show Google Sheets matching table"""
        query = update.callback_query
        await query.answer()
        
        # Format matching table
        table_text = self._format_google_sheets_matching_table(matching_result)
        
        keyboard = [
            [InlineKeyboardButton("📤 Загрузить в Google Sheets", callback_data="gs_upload")],
            [InlineKeyboardButton("◀️ Назад", callback_data="gs_matching_page")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, table_text, reply_markup)
    
    async def _show_google_sheets_position_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Google Sheets position selection"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Show items for position selection
        items_text = "🔍 **Выберите позицию для сопоставления с Google Sheets:**\n\n"
        
        keyboard = []
        for i, match in enumerate(matching_result.matches):
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            item_text = f"{i+1}. {match.receipt_item_name[:30]}{'...' if len(match.receipt_item_name) > 30 else ''}"
            keyboard.append([InlineKeyboardButton(f"{status_emoji} {item_text}", callback_data=f"gs_select_item_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="gs_matching_page")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(items_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_google_sheets_manual_matching_for_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int):
        """Show Google Sheets manual matching for specific item"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result or item_index >= len(matching_result.matches):
            await query.edit_message_text("❌ Неверный индекс позиции")
            return
        
        match = matching_result.matches[item_index]
        
        # Show item details
        item_text = f"🔍 **Google Sheets сопоставление позиции {item_index + 1}:**\n\n"
        item_text += f"📝 **Товар из чека:** {match.receipt_item_name}\n\n"
        
        # Get Google Sheets suggestions
        google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        if not google_sheets_ingredients:
            await self._ensure_google_sheets_ingredients_loaded(context)
            google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        
        if google_sheets_ingredients:
            # Find similar ingredients
            suggestions = []
            for ingredient_id, ingredient_data in google_sheets_ingredients.items():
                similarity = self._calculate_similarity(match.receipt_item_name, ingredient_data['name'])
                if similarity > 0.3:  # Threshold for suggestions
                    suggestions.append({
                        'id': ingredient_id,
                        'name': ingredient_data['name'],
                        'similarity': similarity
                    })
            
            # Sort by similarity
            suggestions.sort(key=lambda x: x['similarity'], reverse=True)
            
            if suggestions:
                item_text += f"💡 **Предложения из Google Sheets:**\n"
                for i, suggestion in enumerate(suggestions[:5], 1):
                    item_text += f"{i}. {suggestion['name']} (сходство: {suggestion['similarity']:.2f})\n"
            else:
                item_text += "❌ Подходящие ингредиенты не найдены\n"
        else:
            item_text += "❌ Google Sheets ингредиенты не загружены\n"
        
        # Create buttons
        keyboard = []
        
        # Add suggestion buttons
        if google_sheets_ingredients:
            suggestions = []
            for ingredient_id, ingredient_data in google_sheets_ingredients.items():
                similarity = self._calculate_similarity(match.receipt_item_name, ingredient_data['name'])
                if similarity > 0.3:
                    suggestions.append({
                        'id': ingredient_id,
                        'name': ingredient_data['name'],
                        'similarity': similarity
                    })
            
            suggestions.sort(key=lambda x: x['similarity'], reverse=True)
            
            for i, suggestion in enumerate(suggestions[:5], 1):
                suggestion_text = suggestion['name'][:25] + ('...' if len(suggestion['name']) > 25 else '')
                keyboard.append([InlineKeyboardButton(f"✅ {i}. {suggestion_text}", callback_data=f"gs_select_suggestion_{i-1}")])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Поиск вручную", callback_data="gs_manual_search")],
            [InlineKeyboardButton("❌ Пропустить", callback_data="gs_skip_item")],
            [InlineKeyboardButton("◀️ Назад к списку", callback_data="gs_position_selection")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(item_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_google_sheets_suggestion_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       suggestion_number: int):
        """Handle Google Sheets suggestion selection"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        current_item = context.user_data.get('current_gs_matching_item', 0)
        
        if not matching_result or current_item >= len(matching_result.matches):
            await query.edit_message_text("❌ Неверный индекс позиции")
            return
        
        match = matching_result.matches[current_item]
        
        # Get Google Sheets suggestions
        google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
        if not google_sheets_ingredients:
            await query.edit_message_text("❌ Google Sheets ингредиенты не загружены")
            return
        
        # Find the selected suggestion
        suggestions = []
        for ingredient_id, ingredient_data in google_sheets_ingredients.items():
            similarity = self._calculate_similarity(match.receipt_item_name, ingredient_data['name'])
            if similarity > 0.3:
                suggestions.append({
                    'id': ingredient_id,
                    'name': ingredient_data['name'],
                    'similarity': similarity
                })
        
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        
        if suggestion_number >= len(suggestions):
            await query.edit_message_text("❌ Неверный номер предложения")
            return
        
        # Select the suggestion
        selected_suggestion = suggestions[suggestion_number]
        match.matched_ingredient_name = selected_suggestion['name']
        match.matched_ingredient_id = selected_suggestion['id']
        match.match_status = MatchStatus.EXACT_MATCH
        match.similarity_score = selected_suggestion['similarity']
        
        # Update changed indices
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        changed_indices.add(current_item)
        context.user_data['changed_ingredient_indices'] = changed_indices
        
        # Save updated matching result
        self._save_ingredient_matching_data(update.effective_user.id, context)
        
        # Show success message
        success_text = f"✅ **Google Sheets сопоставление выполнено!**\n\n"
        success_text += f"📝 **Товар:** {match.receipt_item_name}\n"
        success_text += f"🎯 **Ингредиент:** {match.matched_ingredient_name}\n"
        success_text += f"📊 **Сходство:** {match.similarity_score:.2f}\n\n"
        success_text += "Переходим к следующей позиции..."
        
        keyboard = [
            [InlineKeyboardButton("➡️ Следующая позиция", callback_data="gs_next_item")],
            [InlineKeyboardButton("◀️ Назад к списку", callback_data="gs_position_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _upload_to_google_sheets(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     matching_result: IngredientMatchingResult):
        """Upload matching result to Google Sheets"""
        query = update.callback_query
        await query.answer()
        
        print(f"DEBUG: _upload_to_google_sheets called with matching_result: {matching_result}")
        
        try:
            # Show uploading message
            await query.edit_message_text("📤 Загружаем данные в Google Sheets...")
            
            # Prepare data for upload
            upload_data = []
            for i, match in enumerate(matching_result.matches):
                row_data = {
                    'line_number': i + 1,
                    'receipt_item': match.receipt_item_name,
                    'matched_ingredient': match.matched_ingredient_name or '',
                    'ingredient_id': match.matched_ingredient_id or '',
                    'status': match.match_status.value,
                    'similarity': match.similarity_score
                }
                upload_data.append(row_data)
            
            # Upload to Google Sheets
            receipt_data = context.user_data.get('receipt_data')
            if receipt_data:
                success, message = self.google_sheets_service.upload_receipt_data(receipt_data, matching_result)
            else:
                success = False
                message = "Receipt data not found"
            
            if success:
                # Show success page with full functionality
                await self._show_upload_success_page(update, context, upload_data, message)
            else:
                await query.edit_message_text(f"❌ Ошибка при загрузке: {message}")
                
        except Exception as e:
            print(f"DEBUG: Error uploading to Google Sheets: {e}")
            await query.edit_message_text(f"❌ Ошибка при загрузке: {str(e)}")
    
    def _format_google_sheets_table_preview(self, matching_result: IngredientMatchingResult) -> str:
        """Format Google Sheets table preview"""
        preview_text = "📊 **Предварительный просмотр таблицы Google Sheets:**\n\n"
        
        # Create table header
        preview_text += self._create_google_sheets_table_header()
        preview_text += self._create_google_sheets_table_separator()
        
        # Add table rows
        for i, match in enumerate(matching_result.matches):
            preview_text += self._create_google_sheets_table_row(i + 1, match)
        
        preview_text += "\n💡 **Легенда:**\n"
        preview_text += "✅ - Сопоставлено\n"
        preview_text += "⚠️ - Частично сопоставлено\n"
        preview_text += "❌ - Не сопоставлено\n"
        
        return preview_text
    
    def _format_google_sheets_matching_table(self, matching_result: IngredientMatchingResult) -> str:
        """Format Google Sheets matching table"""
        table_text = "📊 **Таблица сопоставления для Google Sheets:**\n\n"
        
        # Create table header
        table_text += self._create_google_sheets_table_header()
        table_text += self._create_google_sheets_table_separator()
        
        # Add table rows
        for i, match in enumerate(matching_result.matches):
            table_text += self._create_google_sheets_table_row(i + 1, match)
        
        return table_text
    
    def _create_google_sheets_table_header(self) -> str:
        """Create Google Sheets table header"""
        return "| № | Товар из чека | Ингредиент | ID | Статус | Сходство |\n"
    
    def _create_google_sheets_table_separator(self) -> str:
        """Create Google Sheets table separator"""
        return "|---|---|---|---|---|---|\n"
    
    def _create_google_sheets_table_row(self, row_number: int, match: IngredientMatch) -> str:
        """Create Google Sheets table row"""
        status_emoji = self._get_google_sheets_status_emoji(match.match_status)
        ingredient_name = self._truncate_name(match.matched_ingredient_name or '', 20)
        item_name = self._truncate_name(match.receipt_item_name, 25)
        
        return f"| {row_number} | {item_name} | {ingredient_name} | {match.matched_ingredient_id or ''} | {status_emoji} | {match.similarity_score:.2f} |\n"
    
    def _get_google_sheets_status_emoji(self, status) -> str:
        """Get emoji for Google Sheets status"""
        if status == MatchStatus.EXACT_MATCH:
            return "✅"
        elif status == MatchStatus.PARTIAL_MATCH:
            return "⚠️"
        else:
            return "❌"
    
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
    
    def _extract_volume_from_name(self, name: str) -> str:
        """Extract volume information from ingredient name"""
        import re
        
        # Look for volume patterns like "500мл", "1л", "0.5л", etc.
        volume_patterns = [
            r'(\d+(?:\.\d+)?)\s*мл',
            r'(\d+(?:\.\d+)?)\s*л',
            r'(\d+(?:\.\d+)?)\s*г',
            r'(\d+(?:\.\d+)?)\s*кг'
        ]
        
        for pattern in volume_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1) + pattern.split('\\')[1]
        
        return ""
    
    def _wrap_text(self, text: str, max_length: int = 20) -> str:
        """Wrap text to fit in table cells"""
        if len(text) <= max_length:
            return text
        
        # Try to wrap at word boundaries
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_length:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return "\n".join(lines)
    
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
                                      upload_data: list, message: str):
        """Show upload success page"""
        query = update.callback_query
        await query.answer()
        
        success_text = "✅ **Данные успешно загружены в Google Sheets!**\n\n"
        success_text += f"📊 **Загружено позиций:** {len(upload_data)}\n"
        success_text += f"📅 **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        success_text += f"ℹ️ **Детали:** {message}\n\n"
        
        # Show statistics
        matched_count = sum(1 for item in upload_data if item['status'] == 'matched')
        partial_count = sum(1 for item in upload_data if item['status'] == 'partial_match')
        unmatched_count = sum(1 for item in upload_data if item['status'] == 'not_matched')
        
        success_text += "📈 **Статистика сопоставления:**\n"
        success_text += f"✅ Сопоставлено: {matched_count}\n"
        success_text += f"⚠️ Частично: {partial_count}\n"
        success_text += f"❌ Не найдено: {unmatched_count}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Показать таблицу", callback_data="gs_show_table")],
            [InlineKeyboardButton("📁 Скачать Excel", callback_data="generate_file_xlsx")],
            [InlineKeyboardButton("◀️ Назад к чеку", callback_data="back_to_receipt")]
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
    
    async def _show_google_sheets_matching_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                               page: int = 0, items_per_page: int = 10):
        """Show Google Sheets matching page with full functionality"""
        query = update.callback_query
        await query.answer()
        
        matching_result = context.user_data.get('ingredient_matching_result')
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Calculate statistics
        total_items = len(matching_result.matches)
        matched_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.EXACT_MATCH)
        partial_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.PARTIAL_MATCH)
        unmatched_count = sum(1 for match in matching_result.matches if match.match_status == MatchStatus.NO_MATCH)
        
        # Format page content
        page_text = f"📊 **Google Sheets сопоставление (стр. {page + 1})**\n\n"
        page_text += f"📈 **Статистика:**\n"
        page_text += f"✅ Сопоставлено: {matched_count}\n"
        page_text += f"⚠️ Частично: {partial_count}\n"
        page_text += f"❌ Не найдено: {unmatched_count}\n\n"
        
        # Calculate pagination
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        
        # Show items for current page
        for i in range(start_idx, end_idx):
            match = matching_result.matches[i]
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            item_text = f"{i+1}. {status_emoji} {match.receipt_item_name[:30]}{'...' if len(match.receipt_item_name) > 30 else ''}"
            if match.matched_ingredient_name:
                item_text += f"\n   → {match.matched_ingredient_name[:25]}{'...' if len(match.matched_ingredient_name) > 25 else ''}"
            page_text += item_text + "\n\n"
        
        # Create pagination buttons
        keyboard = []
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"gs_page_{page-1}"))
        nav_buttons.append(InlineKeyboardButton(f"{page + 1}", callback_data="gs_current_page"))
        if end_idx < total_items:
            nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"gs_page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Action buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Ручное сопоставление", callback_data="gs_manual_matching")],
            [InlineKeyboardButton("📊 Показать таблицу", callback_data="gs_show_table")],
            [InlineKeyboardButton("📤 Загрузить в Google Sheets", callback_data="gs_upload")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(page_text, reply_markup=reply_markup, parse_mode='Markdown')