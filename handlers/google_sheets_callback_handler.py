"""
Google Sheets callback handler for Telegram bot - Optimized version
"""
import asyncio
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus
from services.google_sheets_service import GoogleSheetsService
from services.file_generator_service import FileGeneratorService
from utils.common_handlers import CommonHandlers


class GoogleSheetsCallbackHandler(BaseCallbackHandler):
    """Handler for Google Sheets related callbacks - Optimized version"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.google_sheets_service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        self.file_generator = FileGeneratorService()
        self.common_handlers = CommonHandlers(config, analysis_service)
    
    # ==================== MAIN INTERFACE METHODS ====================
    
    async def _show_google_sheets_matching_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                               receipt_data=None, matching_result=None):
        """Show Google Sheets matching page with the same table as editor"""
        query = update.callback_query
        await query.answer()
        
        # Get data from parameters or context
        receipt_data, matching_result = self._get_data_from_context_or_params(
            context, receipt_data, matching_result
        )
        
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        # Use the same table formatting as the editor
        table_text = self._format_google_sheets_matching_table(matching_result)
        schema_text = table_text + "\n\nВыберите действие для работы с сопоставлением:"
        
        # Create action buttons
        keyboard = self._create_action_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Save data for future use
        self._save_pending_data(context, receipt_data, matching_result)
        
        await query.edit_message_text(schema_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_google_sheets_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        receipt_data=None, matching_result=None):
        """Show Google Sheets upload preview with confirmation buttons"""
        query = update.callback_query
        await query.answer()
        
        # Get data from parameters or context
        receipt_data, matching_result = self._get_data_from_context_or_params(
            context, receipt_data, matching_result
        )
        
        if not matching_result or not receipt_data:
            await query.edit_message_text("❌ Данные для предпросмотра не найдены")
            return
        
        # Create table preview with Google Sheets data
        table_preview = self._format_google_sheets_table_preview(receipt_data, matching_result)
        text = f"📊 **Предварительный просмотр загрузки в Google Таблицы**\n\n```\n{table_preview}\n```"
        
        keyboard = self._create_preview_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Save data for upload
        self._save_pending_data(context, receipt_data, matching_result)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            print(f"DEBUG: Error editing message in preview: {e}")
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _upload_to_google_sheets(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     matching_result: IngredientMatchingResult):
        """Upload matching result to Google Sheets"""
        query = update.callback_query
        await query.answer()
        
        print(f"DEBUG: _upload_to_google_sheets called with matching_result: {matching_result}")
        
        try:
            await query.edit_message_text("📤 Загружаем данные в Google Sheets...")
            
            receipt_data = context.user_data.get('receipt_data')
            if receipt_data:
                success, message = self.google_sheets_service.upload_receipt_data(receipt_data, matching_result)
            else:
                success, message = False, "Receipt data not found"
            
            if success:
                await self._show_upload_success_page(update, context, "Upload successful", message)
            else:
                await query.edit_message_text(f"❌ Ошибка при загрузке: {message}")
                
        except Exception as e:
            print(f"DEBUG: Error uploading to Google Sheets: {e}")
            await query.edit_message_text(f"❌ Ошибка при загрузке: {str(e)}")
    
    # ==================== NAVIGATION METHODS ====================
    
    async def _handle_skip_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle skip item action - unified with next item logic"""
        await self._handle_item_navigation(update, context, action="skip")
    
    async def _handle_next_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle next item action - unified with skip item logic"""
        await self._handle_item_navigation(update, context, action="next")
    
    async def _handle_item_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        """Unified method for handling item navigation (skip/next)"""
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            await self.ui_manager.send_temp(update, context, "Ошибка: данные для сопоставления не найдены.", duration=5)
            return
        
        matching_result = pending_data['matching_result']
        current_item = context.user_data.get('current_gs_matching_item', 0)
        
        # Find next item that needs matching
        next_item = self._find_next_unmatched_item(matching_result, current_item)
        
        if next_item is None:
            await self.ui_manager.send_temp(update, context, "✅ Все позиции обработаны!", duration=5)
            await self._show_google_sheets_matching_table(update, context)
            return
        
        # Update current item index
        context.user_data['current_gs_matching_item'] = next_item
        
        # Show next item
        await self._show_google_sheets_manual_matching_for_item(update, context, next_item)
    
    # ==================== MATCHING INTERFACE METHODS ====================
    
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
        
        # Create buttons for items that need matching
        keyboard = self._create_matching_table_keyboard(matching_result)
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
        
        # Format the matching table for Google Sheets (same as in editor)
        table_text = self._format_google_sheets_matching_table(matching_result)
        instruction_text = "\n\n**Выберите позицию для сопоставления**\n\n"
        full_text = table_text + instruction_text
        
        # Create buttons for each item
        keyboard = self._create_position_selection_keyboard(matching_result)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, full_text, reply_markup)
    
    async def _show_google_sheets_manual_matching_for_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int):
        """Show manual matching interface for specific Google Sheets item"""
        query = update.callback_query
        await query.answer()
        
        # Validate data and item index
        validation_result = self._validate_matching_data(context, item_index)
        if not validation_result['valid']:
            await self.ui_manager.send_temp(update, context, validation_result['error'], duration=5)
            return
        
        matching_result = validation_result['matching_result']
        current_match = matching_result.matches[item_index]
        
        # Show current match info
        progress_text = self._format_matching_progress_text(current_match)
        
        # Create buttons
        keyboard = self._create_manual_matching_keyboard(current_match, item_index)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(update, context, progress_text, reply_markup, 'Markdown')
    
    # ==================== SUGGESTION HANDLING METHODS ====================
    
    async def _handle_google_sheets_suggestion_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       item_index: int, suggestion_index: int):
        """Handle Google Sheets suggestion selection"""
        query = update.callback_query
        await query.answer("✅ Сопоставление обновлено!")
        
        # Validate data and indices
        validation_result = self._validate_suggestion_data(context, item_index, suggestion_index)
        if not validation_result['valid']:
            await self.ui_manager.send_temp(update, context, validation_result['error'], duration=5)
            return
        
        matching_result = validation_result['matching_result']
        current_match = validation_result['current_match']
        selected_suggestion = validation_result['selected_suggestion']
        
        # Update the match
        self._update_match_with_suggestion(current_match, selected_suggestion)
        
        # Delete the current message and show success
        await self._cleanup_and_show_success(update, context, current_match, selected_suggestion)
        
        # Return to Google Sheets matching table
        await self._show_google_sheets_matching_table(update, context, 
            context.user_data['pending_google_sheets_upload']['receipt_data'], matching_result)
    
    async def _handle_google_sheets_search_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                   item_index: int, result_index: int):
        """Handle Google Sheets search result selection"""
        query = update.callback_query
        await query.answer("✅ Сопоставление обновлено!")
        
        # Validate data and indices
        validation_result = self._validate_search_data(context, item_index, result_index)
        if not validation_result['valid']:
            await self.ui_manager.send_temp(update, context, validation_result['error'], duration=5)
            return
        
        matching_result = validation_result['matching_result']
        current_match = validation_result['current_match']
        selected_result = validation_result['selected_result']
        
        # Update the match
        self._update_match_with_search_result(current_match, selected_result)
        
        # Clear search data
        self._clear_search_data(context)
        
        # Delete the current message and show success
        await self._cleanup_and_show_success(update, context, current_match, selected_result)
        
        # Return to Google Sheets matching table
        await self._show_google_sheets_matching_table(update, context, 
            context.user_data['pending_google_sheets_upload']['receipt_data'], matching_result)
    
    # ==================== SUCCESS AND UNDO METHODS ====================
    
    async def _show_upload_success_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      summary: str, message: str):
        """Show upload success page"""
        # Clean up all messages except anchor first
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        # Create success message with only the header
        success_text = "✅ **Данные успешно загружены в Google Sheets!**"
        
        # Create new button layout
        keyboard = self._create_success_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(update, context, success_text, reply_markup, 'Markdown')
    
    async def _handle_undo_google_sheets_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle undo Google Sheets upload"""
        try:
            # Get last upload data
            last_upload = context.user_data.get('last_google_sheets_upload')
            if not last_upload:
                await self._show_undo_error(update, "Нет данных о последней загрузке для отмены")
                return self.config.AWAITING_CORRECTION
            
            # Get upload details
            worksheet_name = last_upload.get('worksheet_name', 'Receipts')
            row_count = last_upload.get('row_count', 0)
            
            if row_count <= 0:
                await self._show_undo_error(update, "Нет данных для отмены")
                return self.config.AWAITING_CORRECTION
            
            # Attempt to delete the uploaded rows
            success, message = self.google_sheets_service.delete_last_uploaded_rows(worksheet_name, row_count)
            
            if success:
                context.user_data.pop('last_google_sheets_upload', None)
                await self._handle_successful_undo(update, context, worksheet_name, row_count)
            else:
                await self._show_undo_error(update, f"Не удалось отменить загрузку: {message}")
                
        except Exception as e:
            print(f"DEBUG: Error undoing Google Sheets upload: {e}")
            await self._show_undo_error(update, f"Произошла неожиданная ошибка: {str(e)}")
    
    async def _generate_excel_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate Excel file with the same data that was uploaded to Google Sheets"""
        try:
            # Get receipt data and Google Sheets matching result
            receipt_data = context.user_data.get('receipt_data')
            matching_result = context.user_data.get('google_sheets_matching_result')
            
            if not receipt_data:
                await self.ui_manager.send_temp(update, context, "❌ Нет данных чека для генерации файла.", duration=5)
                return
            
            if not matching_result:
                await self.ui_manager.send_temp(update, context, "❌ Нет данных сопоставления Google Sheets для генерации файла.", duration=5)
                return
            
            # Generate Excel file
            file_path = self.file_generator.generate_excel_file(receipt_data, matching_result)
            
            if file_path:
                await self._send_excel_file(update, context, file_path)
                await self._schedule_file_cleanup(file_path)
                await self._show_excel_success(update, context)
            else:
                await self.ui_manager.send_temp(update, context, "❌ Ошибка при создании Excel файла.", duration=5)
                
        except Exception as e:
            print(f"Error generating Excel file: {e}")
            await self.ui_manager.send_temp(update, context, f"❌ Ошибка при создании Excel файла: {str(e)}", duration=5)
    
    # ==================== HELPER METHODS ====================
    
    def _get_data_from_context_or_params(self, context: ContextTypes.DEFAULT_TYPE, 
                                       receipt_data=None, matching_result=None) -> Tuple[Optional[Any], Optional[IngredientMatchingResult]]:
        """Get data from parameters or context"""
        if not matching_result:
            matching_result = context.user_data.get('ingredient_matching_result')
        if not receipt_data:
            receipt_data = context.user_data.get('receipt_data')
        return receipt_data, matching_result
    
    def _save_pending_data(self, context: ContextTypes.DEFAULT_TYPE, receipt_data, matching_result):
        """Save pending data to context"""
        context.user_data['pending_google_sheets_upload'] = {
            'receipt_data': receipt_data,
            'matching_result': matching_result
        }
    
    def _find_next_unmatched_item(self, matching_result: IngredientMatchingResult, current_item: int) -> Optional[int]:
        """Find next item that needs matching"""
        for i in range(current_item + 1, len(matching_result.matches)):
            if matching_result.matches[i].match_status.value in ['partial', 'no_match']:
                return i
        return None
    
    def _validate_matching_data(self, context: ContextTypes.DEFAULT_TYPE, item_index: int) -> Dict[str, Any]:
        """Validate matching data and item index"""
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            return {'valid': False, 'error': 'Ошибка: данные для сопоставления не найдены.'}
        
        matching_result = pending_data['matching_result']
        if item_index >= len(matching_result.matches):
            return {'valid': False, 'error': 'Ошибка: неверный индекс товара.'}
        
        return {'valid': True, 'matching_result': matching_result}
    
    def _validate_suggestion_data(self, context: ContextTypes.DEFAULT_TYPE, item_index: int, suggestion_index: int) -> Dict[str, Any]:
        """Validate suggestion data and indices"""
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            return {'valid': False, 'error': 'Ошибка: данные для сопоставления не найдены.'}
        
        matching_result = pending_data['matching_result']
        if item_index >= len(matching_result.matches):
            return {'valid': False, 'error': 'Ошибка: неверный индекс товара.'}
        
        current_match = matching_result.matches[item_index]
        if not current_match.suggested_matches or suggestion_index >= len(current_match.suggested_matches):
            return {'valid': False, 'error': 'Ошибка: неверный индекс предложения.'}
        
        selected_suggestion = current_match.suggested_matches[suggestion_index]
        return {'valid': True, 'matching_result': matching_result, 'current_match': current_match, 'selected_suggestion': selected_suggestion}
    
    def _validate_search_data(self, context: ContextTypes.DEFAULT_TYPE, item_index: int, result_index: int) -> Dict[str, Any]:
        """Validate search data and indices"""
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            return {'valid': False, 'error': 'Ошибка: данные для сопоставления не найдены.'}
        
        matching_result = pending_data['matching_result']
        if item_index >= len(matching_result.matches):
            return {'valid': False, 'error': 'Ошибка: неверный индекс товара.'}
        
        current_match = matching_result.matches[item_index]
        search_results = context.user_data.get('google_sheets_search_results', [])
        if not search_results or result_index >= len(search_results):
            return {'valid': False, 'error': 'Ошибка: неверный индекс результата поиска.'}
        
        selected_result = search_results[result_index]
        return {'valid': True, 'matching_result': matching_result, 'current_match': current_match, 'selected_result': selected_result}
    
    def _update_match_with_suggestion(self, current_match: IngredientMatch, selected_suggestion: Dict[str, Any]):
        """Update match with selected suggestion"""
        current_match.matched_ingredient_name = selected_suggestion['name']
        current_match.matched_ingredient_id = selected_suggestion['id']
        current_match.match_status = MatchStatus.EXACT_MATCH
        current_match.similarity_score = selected_suggestion['score']
    
    def _update_match_with_search_result(self, current_match: IngredientMatch, selected_result: Dict[str, Any]):
        """Update match with selected search result"""
        current_match.matched_ingredient_name = selected_result['name']
        current_match.matched_ingredient_id = selected_result.get('id', '')
        current_match.match_status = MatchStatus.EXACT_MATCH
        current_match.similarity_score = 1.0
    
    def _clear_search_data(self, context: ContextTypes.DEFAULT_TYPE):
        """Clear search-related data from context"""
        context.user_data.pop('google_sheets_search_results', None)
        context.user_data.pop('google_sheets_search_mode', None)
        context.user_data.pop('google_sheets_search_item_index', None)
    
    async def _cleanup_and_show_success(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      current_match: IngredientMatch, selected_item: Dict[str, Any]):
        """Clean up current message and show success"""
        try:
            await update.callback_query.delete_message()
        except Exception as e:
            print(f"DEBUG: Error deleting message: {e}")
        
        await self.ui_manager.send_temp(
            update, context,
            f"✅ Сопоставлено: {current_match.receipt_item_name} → {selected_item['name']}",
            duration=2
        )
    
    # ==================== KEYBOARD CREATION METHODS ====================
    
    def _create_action_keyboard(self) -> List[List[InlineKeyboardButton]]:
        """Create action keyboard for matching page"""
        return [
            [InlineKeyboardButton("✏️ Редактировать сопоставление", callback_data="edit_google_sheets_matching")],
            [InlineKeyboardButton("👁️ Предпросмотр", callback_data="preview_google_sheets_upload")],
            [InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")]
        ]
    
    def _create_preview_keyboard(self) -> List[List[InlineKeyboardButton]]:
        """Create preview keyboard"""
        return [
            [InlineKeyboardButton("✅ Загрузить в Google Таблицы", callback_data="confirm_google_sheets_upload")],
            [InlineKeyboardButton("✏️ Редактировать сопоставление", callback_data="edit_google_sheets_matching")],
            [InlineKeyboardButton("◀️ Назад", callback_data="upload_to_google_sheets")]
        ]
    
    def _create_matching_table_keyboard(self, matching_result: IngredientMatchingResult) -> List[List[InlineKeyboardButton]]:
        """Create keyboard for matching table"""
        keyboard = []
        
        # Add buttons for items that need matching (max 2 per row)
        items_needing_matching = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status.value in ['partial', 'no_match']:
                items_needing_matching.append((i, match))
        
        for i, (index, match) in enumerate(items_needing_matching):
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            button_text = f"{status_emoji} {self._truncate_name(match.receipt_item_name, 15)}"
            
            if i % 2 == 0:
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_google_sheets_item_{index}")])
            else:
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"edit_google_sheets_item_{index}"))
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Выбрать позицию для сопоставления", callback_data="select_google_sheets_position")],
            [InlineKeyboardButton("👁️ Предпросмотр", callback_data="preview_google_sheets_upload")],
            [InlineKeyboardButton("◀️ Назад", callback_data="upload_to_google_sheets")]
        ])
        
        return keyboard
    
    def _create_position_selection_keyboard(self, matching_result: IngredientMatchingResult) -> List[List[InlineKeyboardButton]]:
        """Create keyboard for position selection"""
        keyboard = []
        for i, match in enumerate(matching_result.matches, 1):
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            button_text = f"{i}. {status_emoji} {self._truncate_name(match.receipt_item_name, 20)}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_line_{i}")])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_google_sheets_matching")])
        return keyboard
    
    def _create_manual_matching_keyboard(self, current_match: IngredientMatch, item_index: int) -> List[List[InlineKeyboardButton]]:
        """Create keyboard for manual matching"""
        keyboard = []
        
        # Add suggestion buttons in two columns
        if current_match.suggested_matches:
            for i, suggestion in enumerate(current_match.suggested_matches[:6], 1):
                button_text = f"{i}. {self._truncate_name(suggestion['name'], 15)} ({int(suggestion['score'] * 100)}%)"
                if i % 2 == 1:
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_suggestion_{item_index}_{i-1}")])
                else:
                    keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_suggestion_{item_index}_{i-1}"))
        
        # Add search and control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Поиск", callback_data=f"search_google_sheets_ingredient_{item_index}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_google_sheets_matching")]
        ])
        
        return keyboard
    
    def _create_success_keyboard(self) -> List[List[InlineKeyboardButton]]:
        """Create success page keyboard"""
        return [
            [InlineKeyboardButton("↩️ Отменить загрузку", callback_data="undo_google_sheets_upload")],
            [InlineKeyboardButton("📄 Сгенерировать файл", callback_data="generate_excel_file")],
            [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
            [InlineKeyboardButton("📸 Загрузить новый чек", callback_data="start_new_receipt")]
        ]
    
    # ==================== TEXT FORMATTING METHODS ====================
    
    def _format_matching_progress_text(self, current_match: IngredientMatch) -> str:
        """Format matching progress text"""
        progress_text = f"**Редактор сопоставления для Google Таблиц**\n\n"
        progress_text += f"**Товар:** {current_match.receipt_item_name}\n\n"
        progress_text += "**Выберите подходящий ингредиент:**\n\n"
        
        if not current_match.suggested_matches:
            progress_text += "❌ **Подходящих вариантов не найдено**\n\n"
        
        return progress_text
    
    async def _show_undo_error(self, update: Update, error_message: str):
        """Show undo error message"""
        await update.callback_query.edit_message_text(
            f"❌ **{error_message}**\n\n"
            "Информация о последней загрузке не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
            ]),
            parse_mode='Markdown'
        )
    
    async def _handle_successful_undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    worksheet_name: str, row_count: int):
        """Handle successful undo operation"""
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if pending_data:
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            await self._show_google_sheets_preview(update, context, receipt_data, matching_result)
        else:
            await update.callback_query.edit_message_text(
                f"✍️ **Загрузка успешно отменена!**\n\n"
                f"📊 **Отменено строк:** {row_count}\n"
                f"📋 **Лист:** {worksheet_name}\n"
                f"🕒 **Время отмены:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Данные были удалены из Google Sheets.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
                    [InlineKeyboardButton("📸 Загрузить новый чек", callback_data="start_new_receipt")]
                ]),
                parse_mode='Markdown'
            )
    
    async def _send_excel_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str):
        """Send Excel file to user"""
        with open(file_path, 'rb') as file:
            file_message = await update.callback_query.message.reply_document(
                document=file,
                filename=f"receipt_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                caption="📄 **Excel-файл с данными чека создан!**"
            )
            
            # Save file message ID for cleanup
            if 'messages_to_cleanup' not in context.user_data:
                context.user_data['messages_to_cleanup'] = []
            context.user_data['messages_to_cleanup'].append(file_message.message_id)
    
    async def _schedule_file_cleanup(self, file_path: str):
        """Schedule file cleanup after 5 minutes"""
        async def cleanup_file():
            await asyncio.sleep(300)  # Wait 5 minutes before cleanup
            try:
                import os
                os.remove(file_path)
                print(f"Temporary file {file_path} cleaned up")
            except Exception as e:
                print(f"Warning: Could not remove temporary file {file_path}: {e}")
        
        asyncio.create_task(cleanup_file())
    
    async def _show_excel_success(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Excel file generation success message"""
        await update.callback_query.edit_message_text(
            "✅ **Excel-файл успешно создан!**\n\n"
            "Файл содержит те же данные, что были загружены в Google Sheets.\n\n"
            "⏰ **Файл будет доступен для скачивания в течение 5 минут**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ Предпросмотр Google Sheets", callback_data="preview_google_sheets_upload")],
                [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
            ]),
            parse_mode='Markdown'
        )
    
    # ==================== DELEGATED METHODS ====================
    
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
    
    # ==================== DELEGATED METHODS TO COMMON HANDLERS ====================
    
    async def _ensure_google_sheets_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Ensure Google Sheets ingredients are loaded, load them if necessary"""
        return await self.common_handlers.ensure_ingredients_loaded(context, "google_sheets")
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name to max length"""
        return self.common_handlers.truncate_name(name, max_length)
    
    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width, breaking on words when possible"""
        return self.common_handlers.wrap_text(text, max_width)
    
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
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        await self.common_handlers.send_long_message_with_keyboard(message, text, reply_markup)
