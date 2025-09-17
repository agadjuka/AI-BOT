"""
Google Sheets callback handler for Telegram bot - Optimized version
"""
import asyncio
import aiofiles
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus
from services.google_sheets_service import GoogleSheetsService
from services.file_generator_service import FileGeneratorService
from services.google_sheets_manager import get_google_sheets_manager
from utils.common_handlers import CommonHandlers
from config.locales.locale_manager import get_global_locale_manager
from config.table_config import TableConfig, ColumnConfig, TableStyle, DeviceType, TableType


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
        self.locale_manager = get_global_locale_manager()
    
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
            text = self.locale_manager.get_text("sheets.callback.matching_results_not_found", context)
            await query.edit_message_text(text)
            return
        
        # Use the same table formatting as the editor
        table_text = await self._format_google_sheets_matching_table(matching_result, context)
        choose_action_text = self.locale_manager.get_text("sheets.callback.choose_action_for_matching", context)
        schema_text = table_text + "\n\n" + choose_action_text
        
        # Create action buttons
        keyboard = self._create_action_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Data is already saved in dispatcher, no need to save again
        
        await query.edit_message_text(schema_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_google_sheets_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        receipt_data=None, matching_result=None, selected_sheet_id=None):
        """Show Google Sheets upload preview with dynamic table structure based on selected sheet"""
        query = update.callback_query
        await query.answer()
        
        # Get data from parameters or context
        receipt_data, matching_result = self._get_data_from_context_or_params(
            context, receipt_data, matching_result
        )
        
        if not matching_result or not receipt_data:
            text = self.locale_manager.get_text("sheets.callback.preview_data_not_found", context)
            await query.edit_message_text(text)
            return
        
        # Get user ID
        user_id = update.effective_user.id
        
        # Get all user sheets
        user_sheets = await self._get_user_sheets(user_id)
        if not user_sheets:
            error_text = self.locale_manager.get_text("sheets.callback.no_sheets_found", context)
            await query.edit_message_text(error_text)
            return
        
        # Determine which sheet to use
        selected_sheet = None
        if selected_sheet_id:
            # Find the selected sheet by ID
            for sheet in user_sheets:
                if sheet.get('doc_id') == selected_sheet_id:
                    selected_sheet = sheet
                    break
        else:
            # Use default sheet or first available
            selected_sheet = await self._get_user_default_sheet(user_id)
            if not selected_sheet and user_sheets:
                selected_sheet = user_sheets[0]
        
        if not selected_sheet:
            error_text = self.locale_manager.get_text("sheets.callback.no_sheet_selected", context)
            await query.edit_message_text(error_text)
            return
        
        # Get column mapping from the selected sheet
        column_mapping = selected_sheet.get('column_mapping', {})
        if not column_mapping:
            error_text = self.locale_manager.get_text("sheets.callback.no_column_mapping_found", context)
            await query.edit_message_text(error_text)
            return
        
        # print(f"📊 Using column mapping from sheet '{selected_sheet.get('friendly_name', 'Unknown')}': {column_mapping}")  # Отключено для чистоты консоли
        
        # Store selected sheet ID in context for upload
        context.user_data['selected_sheet_id'] = selected_sheet.get('doc_id')
        
        # Determine device type
        device_type = DeviceType.MOBILE  # Default
        if context and hasattr(context, 'user_data'):
            device_type_str = context.user_data.get('device_type')
            if device_type_str:
                try:
                    device_type = DeviceType(device_type_str)
                except ValueError:
                    pass
        
        # Create dynamic table preview
        table_preview = self._format_dynamic_google_sheets_preview(
            receipt_data, matching_result, column_mapping, device_type, context
        )
        
        preview_title = self.locale_manager.get_text("sheets.callback.upload_preview_title", context)
        
        # Get sheet name for display
        sheet_name = selected_sheet.get('sheet_name', 'Sheet1')
        sheet_name_label = self.locale_manager.get_text("sheets.callback.sheet_name_label", context).format(sheet_name=sheet_name)
        
        text = f"{preview_title}\n\n```\n{table_preview}\n```\n\n{sheet_name_label}"
        
        keyboard = self._create_preview_keyboard(context, user_sheets, selected_sheet)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
            uploading_text = self.locale_manager.get_text("sheets.callback.uploading_data", context)
            await query.edit_message_text(uploading_text)
            
            receipt_data = context.user_data.get('receipt_data')
            if not receipt_data:
                error_text = self.locale_manager.get_text("sheets.callback.receipt_data_not_found", context)
                await query.edit_message_text(error_text)
                return
            
            # Get user's default sheet configuration from Firestore
            user_id = update.effective_user.id
            default_sheet = await self._get_user_default_sheet(user_id)
            
            if not default_sheet:
                error_text = self.locale_manager.get_text("sheets.callback.no_sheet_configured", context)
                await query.edit_message_text(error_text)
                return
            
            # Create new GoogleSheetsService with user's sheet configuration
            from services.google_sheets_service import GoogleSheetsService
            user_sheets_service = GoogleSheetsService(
                credentials_path=self.config.GOOGLE_SHEETS_CREDENTIALS,
                spreadsheet_id=default_sheet.get('sheet_id')
            )
            
            if not user_sheets_service.is_available():
                error_text = self.locale_manager.get_text("sheets.callback.service_not_available", context)
                await query.edit_message_text(error_text)
                return
            
            # Upload with user's configuration
            worksheet_name = "Receipts"  # Default worksheet name
            column_mapping = default_sheet.get('column_mapping', {})
            data_start_row = default_sheet.get('data_start_row', 1)
            
            success, message = user_sheets_service.upload_receipt_data(
                receipt_data, 
                matching_result,
                worksheet_name=worksheet_name,
                column_mapping=column_mapping,
                data_start_row=data_start_row
            )
            
            if success:
                success_text = self.locale_manager.get_text("sheets.callback.upload_successful", context)
                await self._show_upload_success_page(update, context, success_text, message)
            else:
                # Check for specific error types and provide better messages
                if "quota" in message.lower() or "429" in message:
                    error_text = self.locale_manager.get_text("sheets.callback.quota_exceeded", context)
                elif "permission" in message.lower():
                    error_text = self.locale_manager.get_text("sheets.callback.permission_denied", context)
                elif "not found" in message.lower():
                    error_text = self.locale_manager.get_text("sheets.callback.sheet_not_found", context)
                else:
                    error_text = self.locale_manager.get_text("sheets.callback.upload_error", context).format(message=message)
                
                await query.edit_message_text(error_text)
                
        except Exception as e:
            print(f"DEBUG: Error uploading to Google Sheets: {e}")
            # Escape special characters to prevent Markdown parsing errors
            error_message = str(e).replace('`', '').replace('*', '').replace('_', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
            # Additional escaping for common problematic characters
            error_message = error_message.replace('!', '').replace('@', '').replace('#', '').replace('$', '').replace('%', '').replace('^', '').replace('&', '').replace('+', '').replace('=', '').replace('{', '').replace('}', '').replace('|', '').replace('\\', '').replace(':', '').replace(';', '').replace('"', '').replace("'", '').replace('<', '').replace('>', '').replace(',', '').replace('.', '').replace('?', '').replace('/', '')
            
            error_text = self.locale_manager.get_text("sheets.callback.upload_error", context).format(message=error_message)
            await query.edit_message_text(error_text, parse_mode='HTML')
    
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
            error_text = self.locale_manager.get_text("sheets.callback.matching_data_not_found", context)
            await self.ui_manager.send_temp(update, context, error_text, duration=5)
            return
        
        matching_result = pending_data['matching_result']
        current_item = context.user_data.get('current_gs_matching_item', 0)
        
        # Find next item that needs matching
        next_item = self._find_next_unmatched_item(matching_result, current_item)
        
        if next_item is None:
            success_text = self.locale_manager.get_text("sheets.callback.all_positions_processed", context)
            await self.ui_manager.send_temp(update, context, success_text, duration=5)
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
                text = self.locale_manager.get_text("sheets.callback.matching_results_not_found", context)
                await query.edit_message_text(text)
                return
        
        # Format the matching table for Google Sheets
        table_text = await self._format_google_sheets_matching_table(matching_result, context)
        
        # Create buttons for items that need matching
        keyboard = self._create_matching_table_keyboard(matching_result, context)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit existing message instead of sending new one
        await query.edit_message_text(table_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _show_google_sheets_position_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show position selection for Google Sheets matching"""
        query = update.callback_query
        await query.answer()
        
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            error_text = self.locale_manager.get_text("sheets.callback.matching_data_not_found", context)
            await self.ui_manager.send_temp(
                update, context, error_text, duration=5
            )
            return
        
        matching_result = pending_data['matching_result']
        
        # Format the matching table for Google Sheets (same as in editor)
        table_text = await self._format_google_sheets_matching_table(matching_result, context)
        instruction_text = "\n\n" + self.locale_manager.get_text("sheets.callback.choose_position_for_matching", context) + "\n\n"
        full_text = table_text + instruction_text
        
        # Create buttons for each item
        keyboard = self._create_position_selection_keyboard(matching_result, context)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit existing message instead of sending new one
        await query.edit_message_text(full_text, reply_markup=reply_markup, parse_mode='Markdown')
    
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
        progress_text = self._format_matching_progress_text(current_match, context)
        
        # Create buttons
        keyboard = self._create_manual_matching_keyboard(current_match, item_index, context)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit existing message instead of sending new one
        await query.edit_message_text(progress_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # ==================== SUGGESTION HANDLING METHODS ====================
    
    async def _handle_google_sheets_suggestion_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       item_index: int, suggestion_index: int):
        """Handle Google Sheets suggestion selection"""
        query = update.callback_query
        answer_text = self.locale_manager.get_text("sheets.callback.matching_updated", context)
        await query.answer(answer_text)
        
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
        
        # Show success and return to matching table
        await self._cleanup_and_show_success(update, context, current_match, selected_suggestion)
    
    async def _handle_google_sheets_search_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                   item_index: int, result_index: int):
        """Handle Google Sheets search result selection"""
        query = update.callback_query
        answer_text = self.locale_manager.get_text("sheets.callback.matching_updated", context)
        await query.answer(answer_text)
        
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
        
        # Show success and return to matching table
        await self._cleanup_and_show_success(update, context, current_match, selected_result)
    
    # ==================== SUCCESS AND UNDO METHODS ====================
    
    async def _show_upload_success_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      summary: str, message: str):
        """Show upload success page"""
        # Clean up all messages except anchor first
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        # Create success message with only the header
        success_text = self.locale_manager.get_text("sheets.callback.data_successfully_uploaded", context)
        
        # Create new button layout
        keyboard = self._create_success_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(update, context, success_text, reply_markup, 'Markdown')
    
    async def _handle_undo_google_sheets_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle undo Google Sheets upload"""
        try:
            # Get last upload data
            last_upload = context.user_data.get('last_google_sheets_upload')
            if not last_upload:
                error_text = self.locale_manager.get_text("sheets.callback.no_upload_data_for_undo", context)
                await self._show_undo_error(update, error_text, context)
                return self.config.AWAITING_CORRECTION
            
            # Get upload details
            worksheet_name = last_upload.get('worksheet_name', 'Receipts')
            row_count = last_upload.get('row_count', 0)
            sheet_id = last_upload.get('sheet_id')
            data_start_row = last_upload.get('data_start_row', 1)
            
            if row_count <= 0:
                error_text = self.locale_manager.get_text("sheets.callback.no_data_to_undo", context)
                await self._show_undo_error(update, error_text, context)
                return self.config.AWAITING_CORRECTION
            
            if not sheet_id:
                error_text = self.locale_manager.get_text("sheets.callback.sheet_not_found", context)
                await self._show_undo_error(update, error_text, context)
                return self.config.AWAITING_CORRECTION
            
            # Create GoogleSheetsService instance with the same sheet_id as used for upload
            from services.google_sheets_service import GoogleSheetsService
            sheet_service = GoogleSheetsService(
                credentials_path=self.config.GOOGLE_SHEETS_CREDENTIALS,
                spreadsheet_id=sheet_id
            )
            
            # Attempt to delete the uploaded rows using the correct service
            success, message = sheet_service.delete_last_uploaded_rows(worksheet_name, row_count, data_start_row)
            
            if success:
                context.user_data.pop('last_google_sheets_upload', None)
                await self._handle_successful_undo(update, context, worksheet_name, row_count)
            else:
                error_text = self.locale_manager.get_text("sheets.callback.undo_upload_failed", context).format(message=message)
                await self._show_undo_error(update, error_text, context)
                
        except Exception as e:
            print(f"DEBUG: Error undoing Google Sheets upload: {e}")
            error_text = self.locale_manager.get_text("sheets.callback.unexpected_error", context).format(error=str(e))
            await self._show_undo_error(update, error_text, context)
    
    async def _generate_excel_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate Excel file with the same data that was uploaded to Google Sheets"""
        try:
            # Get receipt data and Google Sheets matching result
            receipt_data = context.user_data.get('receipt_data')
            matching_result = context.user_data.get('google_sheets_matching_result')
            
            if not receipt_data:
                error_text = self.locale_manager.get_text("sheets.callback.no_receipt_data_for_file", context)
                await self.ui_manager.send_temp(update, context, error_text, duration=5)
                return
            
            if not matching_result:
                error_text = self.locale_manager.get_text("sheets.callback.no_matching_data_for_file", context)
                await self.ui_manager.send_temp(update, context, error_text, duration=5)
                return
            
            # Generate Excel file (use async version for better performance)
            file_path = await self.file_generator.generate_excel_file_async(receipt_data, matching_result)
            
            if file_path:
                await self._send_excel_file(update, context, file_path)
                await self._schedule_file_cleanup(file_path)
                await self._show_excel_success(update, context)
            else:
                error_text = self.locale_manager.get_text("sheets.callback.excel_generation_error", context)
                await self.ui_manager.send_temp(update, context, error_text, duration=5)
                
        except Exception as e:
            print(f"Error generating Excel file: {e}")
            error_text = self.locale_manager.get_text("sheets.callback.excel_generation_error_detailed", context).format(error=str(e))
            await self.ui_manager.send_temp(update, context, error_text, duration=5)
    
    # ==================== HELPER METHODS ====================
    
    async def _get_user_sheets(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получает все таблицы пользователя из Firestore
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            List[Dict] с данными всех таблиц пользователя
        """
        try:
            sheets_manager = get_google_sheets_manager()
            user_sheets = await sheets_manager.get_user_sheets(user_id)
            
            if not user_sheets:
                print(f"❌ No sheets found for user {user_id}")
                return []
            
            print(f"✅ Found {len(user_sheets)} sheets for user {user_id}")
            return user_sheets
            
        except Exception as e:
            print(f"❌ Error getting user sheets: {e}")
            return []

    async def _get_user_default_sheet(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает основную (дефолтную) таблицу пользователя из Firestore
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Dict с данными основной таблицы или None если не найдена
        """
        try:
            sheets_manager = get_google_sheets_manager()
            user_sheets = await sheets_manager.get_user_sheets(user_id)
            
            if not user_sheets:
                print(f"❌ No sheets found for user {user_id}")
                return None
            
            # Ищем основную таблицу (is_default = True)
            for sheet in user_sheets:
                if sheet.get('is_default', False):
                    print(f"✅ Found default sheet for user {user_id}: {sheet.get('friendly_name', 'Unknown')}")
                    return sheet
            
            # Если основная таблица не найдена, берем первую попавшуюся
            if user_sheets:
                print(f"⚠️ No default sheet found for user {user_id}, using first available: {user_sheets[0].get('friendly_name', 'Unknown')}")
                return user_sheets[0]
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting user default sheet: {e}")
            return None
    
    def _create_dynamic_columns_from_mapping(self, column_mapping: Dict[str, str], device_type: DeviceType) -> List[ColumnConfig]:
        """
        Создает динамические колонки на основе column_mapping пользователя
        
        Args:
            column_mapping: Маппинг полей на колонки (например, {'check_date': 'A', 'product_name': 'B'})
            device_type: Тип устройства для определения ширины колонок
            
        Returns:
            List[ColumnConfig]: Список конфигураций колонок
        """
        if not column_mapping:
            print("❌ No column mapping provided")
            return []
        
        # Получаем все используемые колонки и сортируем их по алфавиту
        used_columns = sorted(column_mapping.values())
        # print(f"📊 Creating dynamic columns for: {used_columns}")  # Отключено для чистоты консоли
        
        # Определяем ширину колонок согласно требованиям:
        # дата 10 (было 9, увеличили на 1), название 20 (было 21, уменьшили на 1), 
        # количество 6, цена 10, сумма 10
        field_widths = {
            'check_date': 10,
            'product_name': 20,
            'quantity': 6,
            'unit_price': 10,
            'total_price': 10
        }
        
        columns = []
        for column_letter in used_columns:
            # Находим поле, которое соответствует этой колонке
            field_name = None
            for field, col in column_mapping.items():
                if col == column_letter:
                    field_name = field
                    break
            
            # Определяем ширину колонки на основе поля
            if field_name in field_widths:
                width = field_widths[field_name]
            else:
                # Для неизвестных полей используем базовую ширину
                width = 12 if device_type == DeviceType.MOBILE else 15
            
            # Все колонки выравниваем по левому краю
            align = "left"
            
            # Создаем конфигурацию колонки
            column_config = ColumnConfig(
                key=column_letter.lower(),  # Используем букву как ключ
                title=column_letter,  # Заголовок - это буква колонки
                width=width,
                align=align
            )
            columns.append(column_config)
        
        return columns
    
    def _get_field_name_for_column(self, column_letter: str, column_mapping: Dict[str, str]) -> str:
        """
        Получает человекочитаемое название поля для колонки
        
        Args:
            column_letter: Буква колонки (A, B, C, etc.)
            column_mapping: Маппинг полей на колонки
            
        Returns:
            str: Человекочитаемое название поля
        """
        # Обратный поиск: ищем поле, которое соответствует этой колонке
        for field_name, col_letter in column_mapping.items():
            if col_letter == column_letter:
                # Преобразуем snake_case в читаемый текст
                field_display_names = {
                    'check_date': 'Дата',
                    'product_name': 'Название товара',
                    'quantity': 'Количество',
                    'price_per_item': 'Цена за единицу',
                    'total_price': 'Сумма',
                    'store_name': 'Магазин',
                    'category': 'Категория',
                    'notes': 'Примечания'
                }
                return field_display_names.get(field_name, field_name.replace('_', ' ').title())
        
        return "---"  # Если поле не найдено
    
    def _prepare_dynamic_table_data(self, receipt_data, matching_result, column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Подготавливает данные для динамической таблицы на основе column_mapping
        
        Args:
            receipt_data: Данные чека
            matching_result: Результат сопоставления ингредиентов
            column_mapping: Маппинг полей на колонки
            
        Returns:
            List[Dict[str, Any]]: Подготовленные данные для таблицы
        """
        if not receipt_data.items or not matching_result.matches:
            return []
        
        table_data = []
        
        for i, item in enumerate(receipt_data.items):
            # Получаем сопоставленный ингредиент
            match = None
            if i < len(matching_result.matches):
                match = matching_result.matches[i]
            
            # Создаем строку данных
            row_data = {}
            
            # Заполняем данные для каждой колонки
            for field_name, column_letter in column_mapping.items():
                if field_name == 'check_date':
                    row_data[column_letter.lower()] = datetime.now().strftime('%d.%m.%Y')
                elif field_name == 'product_name':
                    # Для красных маркеров (NO_MATCH) используем название из чека (Gemini recognition)
                    # Для зеленых и желтых маркеров используем сопоставленное название
                    if match and match.match_status.value != 'no_match' and match.matched_ingredient_name:
                        row_data[column_letter.lower()] = match.matched_ingredient_name
                    else:
                        # Для NO_MATCH (red marker), используем название из чека (Gemini recognition)
                        row_data[column_letter.lower()] = item.name if item.name else ""
                elif field_name == 'quantity':
                    quantity = item.quantity if item.quantity is not None else 0
                    # Извлекаем объем из названия товара
                    volume_from_name = self._extract_volume_from_name(item.name)
                    if volume_from_name > 0:
                        total_volume = volume_from_name * quantity
                        if total_volume == int(total_volume):
                            row_data[column_letter.lower()] = str(int(total_volume))
                        else:
                            row_data[column_letter.lower()] = f"{total_volume:.2f}"
                    elif quantity > 0:
                        if quantity == int(quantity):
                            row_data[column_letter.lower()] = str(int(quantity))
                        else:
                            row_data[column_letter.lower()] = f"{quantity:.2f}"
                    else:
                        row_data[column_letter.lower()] = "-"
                elif field_name == 'price_per_item':
                    price = item.price if item.price is not None else 0
                    if price > 0:
                        if price == int(price):
                            row_data[column_letter.lower()] = f"{int(price):,}".replace(",", " ")
                        else:
                            row_data[column_letter.lower()] = f"{price:,.1f}".replace(",", " ")
                    else:
                        row_data[column_letter.lower()] = "-"
                elif field_name == 'total_price':
                    price = item.price if item.price is not None else 0
                    quantity = item.quantity if item.quantity is not None else 0
                    total = price * quantity
                    if total > 0:
                        if total == int(total):
                            row_data[column_letter.lower()] = f"{int(total):,}".replace(",", " ")
                        else:
                            row_data[column_letter.lower()] = f"{total:,.1f}".replace(",", " ")
                    else:
                        row_data[column_letter.lower()] = "-"
                else:
                    # Для других полей используем пустую строку
                    row_data[column_letter.lower()] = ""
            
            table_data.append(row_data)
        
        return table_data
    
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
            error_text = self.locale_manager.get_text('sheets.callback.matching_data_not_found', context)
            return {'valid': False, 'error': error_text}
        
        matching_result = pending_data['matching_result']
        if item_index >= len(matching_result.matches):
            error_text = self.locale_manager.get_text('sheets.callback.invalid_item_index', context)
            return {'valid': False, 'error': error_text}
        
        return {'valid': True, 'matching_result': matching_result}
    
    def _validate_suggestion_data(self, context: ContextTypes.DEFAULT_TYPE, item_index: int, suggestion_index: int) -> Dict[str, Any]:
        """Validate suggestion data and indices"""
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            error_text = self.locale_manager.get_text('sheets.callback.matching_data_not_found', context)
            return {'valid': False, 'error': error_text}
        
        matching_result = pending_data['matching_result']
        if item_index >= len(matching_result.matches):
            error_text = self.locale_manager.get_text('sheets.callback.invalid_item_index', context)
            return {'valid': False, 'error': error_text}
        
        current_match = matching_result.matches[item_index]
        if not current_match.suggested_matches or suggestion_index >= len(current_match.suggested_matches):
            error_text = self.locale_manager.get_text('sheets.callback.invalid_suggestion_index', context)
            return {'valid': False, 'error': error_text}
        
        selected_suggestion = current_match.suggested_matches[suggestion_index]
        return {'valid': True, 'matching_result': matching_result, 'current_match': current_match, 'selected_suggestion': selected_suggestion}
    
    def _validate_search_data(self, context: ContextTypes.DEFAULT_TYPE, item_index: int, result_index: int) -> Dict[str, Any]:
        """Validate search data and indices"""
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if not pending_data:
            error_text = self.locale_manager.get_text('sheets.callback.matching_data_not_found', context)
            return {'valid': False, 'error': error_text}
        
        matching_result = pending_data['matching_result']
        if item_index >= len(matching_result.matches):
            error_text = self.locale_manager.get_text('sheets.callback.invalid_item_index', context)
            return {'valid': False, 'error': error_text}
        
        current_match = matching_result.matches[item_index]
        search_results = context.user_data.get('google_sheets_search_results', [])
        if not search_results or result_index >= len(search_results):
            error_text = self.locale_manager.get_text('sheets.callback.invalid_search_result_index', context)
            return {'valid': False, 'error': error_text}
        
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
        """Show success and return to matching table"""
        # Show temporary success message
        success_text = self.locale_manager.get_text("sheets.callback.matched_successfully", context).format(
            receipt_item=current_match.receipt_item_name,
            ingredient_name=selected_item['name']
        )
        await self.ui_manager.send_temp(
            update, context,
            success_text,
            duration=2
        )
        
        # Return to Google Sheets matching table
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if pending_data:
            await self._show_google_sheets_matching_table(update, context, 
                pending_data['receipt_data'], pending_data['matching_result'])
    
    # ==================== KEYBOARD CREATION METHODS ====================
    
    def _create_action_keyboard(self, context) -> List[List[InlineKeyboardButton]]:
        """Create action keyboard for matching page"""
        return [
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.edit_matching", context), callback_data="edit_google_sheets_matching")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.preview", context), callback_data="preview_google_sheets_upload")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.back_to_receipt", context), callback_data="back_to_receipt")]
        ]
    
    def _create_preview_keyboard(self, context, user_sheets: List[Dict[str, Any]], selected_sheet: Dict[str, Any]) -> List[List[InlineKeyboardButton]]:
        """Create preview keyboard with sheet selection"""
        keyboard = []
        
        # Find default sheet
        default_sheet = None
        for sheet in user_sheets:
            if sheet.get('is_default', False):
                default_sheet = sheet
                break
        
        # If no default sheet found, use first one
        if not default_sheet and user_sheets:
            default_sheet = user_sheets[0]
        
        # Main upload button for selected sheet
        selected_sheet_name = selected_sheet.get('friendly_name', 'Unknown')
        upload_text = self.locale_manager.get_text("sheets.callback.upload_to_main_sheet", context).format(sheet_name=selected_sheet_name)
        
        keyboard.append([InlineKeyboardButton(upload_text, callback_data="confirm_google_sheets_upload")])
        
        # Add buttons for other sheets
        for sheet in user_sheets:
            if sheet.get('doc_id') != selected_sheet.get('doc_id'):  # Skip currently selected sheet
                sheet_name = sheet.get('friendly_name', 'Unknown')
                button_text = self.locale_manager.get_text("sheets.callback.upload_to_sheet", context).format(sheet_name=sheet_name)
                callback_data = f"gs_select_sheet_{sheet.get('doc_id')}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.edit_matching", context), callback_data="edit_google_sheets_matching")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.back", context), callback_data="upload_to_google_sheets")]
        ])
        
        return keyboard
    
    def _create_matching_table_keyboard(self, matching_result: IngredientMatchingResult, context) -> List[List[InlineKeyboardButton]]:
        """Create keyboard for matching table"""
        keyboard = []
        
        # Add buttons for items that need matching (max 2 per row)
        items_needing_matching = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status.value in ['partial', 'no_match']:
                items_needing_matching.append((i, match))
        
        for i, (index, match) in enumerate(items_needing_matching):
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            if status_emoji:
                button_text = f"{status_emoji} {self._truncate_name(match.receipt_item_name, 15)}"
            else:
                button_text = self._truncate_name(match.receipt_item_name, 15)
            
            if i % 2 == 0:
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_google_sheets_item_{index}")])
            else:
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"edit_google_sheets_item_{index}"))
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.select_position_for_matching", context), callback_data="select_google_sheets_position")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.preview", context), callback_data="preview_google_sheets_upload")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.back", context), callback_data="upload_to_google_sheets")]
        ])
        
        return keyboard
    
    def _create_position_selection_keyboard(self, matching_result: IngredientMatchingResult, context) -> List[List[InlineKeyboardButton]]:
        """Create keyboard for position selection"""
        keyboard = []
        for i, match in enumerate(matching_result.matches, 1):
            status_emoji = self._get_google_sheets_status_emoji(match.match_status)
            if status_emoji:
                button_text = f"{i}. {status_emoji} {self._truncate_name(match.receipt_item_name, 20)}"
            else:
                button_text = f"{i}. {self._truncate_name(match.receipt_item_name, 20)}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_google_sheets_line_{i}")])
        
        keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.back", context), callback_data="back_to_google_sheets_matching")])
        return keyboard
    
    def _create_manual_matching_keyboard(self, current_match: IngredientMatch, item_index: int, context) -> List[List[InlineKeyboardButton]]:
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
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.search", context), callback_data=f"search_google_sheets_ingredient_{item_index}")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.back", context), callback_data="back_to_google_sheets_matching")]
        ])
        
        return keyboard
    
    def _create_success_keyboard(self, context) -> List[List[InlineKeyboardButton]]:
        """Create success page keyboard"""
        return [
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.undo_upload", context), callback_data="undo_google_sheets_upload")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.generate_file", context), callback_data="generate_excel_file")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.back_to_receipt_button", context), callback_data="back_to_receipt")],
            [InlineKeyboardButton(self.locale_manager.get_text("sheets.callback.upload_new_receipt", context), callback_data="start_new_receipt")]
        ]
    
    # ==================== TEXT FORMATTING METHODS ====================
    
    def _format_matching_progress_text(self, current_match: IngredientMatch, context=None) -> str:
        """Format matching progress text"""
        if context:
            progress_text = self.locale_manager.get_text("sheets.callback.manual_matching_editor_title", context) + "\n\n"
            progress_text += self.locale_manager.get_text("sheets.callback.current_item", context).format(item_name=current_match.receipt_item_name) + "\n"
            progress_text += self.locale_manager.get_text("sheets.callback.choose_suitable_ingredient", context) + "\n\n"
            
            if not current_match.suggested_matches:
                progress_text += self.locale_manager.get_text("sheets.callback.no_suitable_options", context) + "\n\n"
        else:
            # Fallback to Russian if no context
            progress_text = f"**Редактор сопоставления для Google Таблиц**\n\n"
            progress_text += f"**Товар:** {current_match.receipt_item_name}\n\n"
            progress_text += "**Выберите подходящий ингредиент:**\n\n"
            
            if not current_match.suggested_matches:
                progress_text += "❌ **Подходящих вариантов не найдено**\n\n"
        
        return progress_text
    
    async def _show_undo_error(self, update: Update, error_message: str, context=None):
        """Show undo error message"""
        if context:
            error_title = self.locale_manager.get_text("sheets.callback.undo_error_title", context).format(error_message=error_message)
            error_info = self.locale_manager.get_text("sheets.callback.undo_error_info", context)
            back_button_text = self.locale_manager.get_text("sheets.callback.back_to_receipt", context)
        else:
            # Fallback to Russian if no context
            error_title = f"❌ **{error_message}**"
            error_info = "Информация о последней загрузке не найдена."
            back_button_text = "📋 Вернуться к чеку"
        
        await update.callback_query.edit_message_text(
            f"{error_title}\n\n{error_info}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(back_button_text, callback_data="back_to_receipt")]
            ]),
            parse_mode='Markdown'
        )
    
    async def _handle_successful_undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    worksheet_name: str, row_count: int):
        """Handle successful undo operation - immediately show Google Sheets preview"""
        # Always try to show Google Sheets preview after successful undo
        pending_data = context.user_data.get('pending_google_sheets_upload')
        if pending_data:
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            await self._show_google_sheets_preview(update, context, receipt_data, matching_result)
        else:
            # If no pending data, try to get data from user_data
            receipt_data = context.user_data.get('receipt_data')
            matching_result = context.user_data.get('google_sheets_matching_result')
            
            if receipt_data and matching_result:
                await self._show_google_sheets_preview(update, context, receipt_data, matching_result)
            else:
                # Fallback: show error and return to receipt
                error_text = self.locale_manager.get_text("sheets.callback.no_data_for_preview", context)
                back_to_receipt_text = self.locale_manager.get_text("sheets.callback.back_to_receipt", context)
                
                await update.callback_query.edit_message_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(back_to_receipt_text, callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
    
    async def _send_excel_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str):
        """Send Excel file to user"""
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                file_content = await file.read()
                file_message = await update.callback_query.message.reply_document(
                    document=file_content,
                    filename=f"receipt_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    caption=self.locale_manager.get_text("sheets.callback.excel_file_created", context)
                )
                
                # Save file message ID for cleanup
                if 'messages_to_cleanup' not in context.user_data:
                    context.user_data['messages_to_cleanup'] = []
                context.user_data['messages_to_cleanup'].append(file_message.message_id)
        except Exception as e:
            print(f"Error sending Excel file: {e}")
            error_text = self.locale_manager.get_text("sheets.callback.excel_file_send_error", context).format(error=str(e))
            await self.ui_manager.send_temp(update, context, error_text, duration=5)
    
    async def _schedule_file_cleanup(self, file_path: str):
        """Schedule file cleanup after 5 minutes"""
        async def cleanup_file():
            await asyncio.sleep(300)  # Wait 5 minutes before cleanup
            try:
                import os
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Temporary file {file_path} cleaned up")
            except Exception as e:
                print(f"Warning: Could not remove temporary file {file_path}: {e}")
        
        asyncio.create_task(cleanup_file())
    
    async def _show_excel_success(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Excel file generation success message"""
        success_title = self.locale_manager.get_text("sheets.callback.excel_success_title", context)
        success_description = self.locale_manager.get_text("sheets.callback.excel_success_description", context)
        file_available = self.locale_manager.get_text("sheets.callback.file_available_for_download", context)
        preview_text = self.locale_manager.get_text("sheets.callback.preview_google_sheets", context)
        back_to_receipt_text = self.locale_manager.get_text("sheets.callback.back_to_receipt", context)
        
        await update.callback_query.edit_message_text(
            f"{success_title}\n\n{success_description}\n\n{file_available}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(preview_text, callback_data="preview_google_sheets_upload")],
                [InlineKeyboardButton(back_to_receipt_text, callback_data="back_to_receipt")]
            ]),
            parse_mode='Markdown'
        )
    
    # ==================== DELEGATED METHODS ====================
    
    def _format_dynamic_google_sheets_preview(self, receipt_data, matching_result, column_mapping: Dict[str, str], device_type: DeviceType, context=None) -> str:
        """
        Форматирует динамическую таблицу предпросмотра Google Sheets на основе column_mapping пользователя
        
        Args:
            receipt_data: Данные чека
            matching_result: Результат сопоставления ингредиентов
            column_mapping: Маппинг полей на колонки
            device_type: Тип устройства
            context: Контекст Telegram
            
        Returns:
            str: Отформатированная таблица
        """
        if not receipt_data.items or not matching_result.matches:
            if context:
                return self.locale_manager.get_text("sheets.callback.no_data_to_display", context)
            return "Нет данных для отображения"
        
        # Создаем динамические колонки
        dynamic_columns = self._create_dynamic_columns_from_mapping(column_mapping, device_type)
        if not dynamic_columns:
            return "Ошибка создания колонок таблицы"
        
        # Подготавливаем данные
        table_data = self._prepare_dynamic_table_data(receipt_data, matching_result, column_mapping)
        if not table_data:
            return "Нет данных для отображения"
        
        # Создаем заголовок таблицы
        lines = []
        
        # Первая строка: буквы колонок (A, B, C, ...)
        column_headers = []
        for column in dynamic_columns:
            column_headers.append(f"{column.title:^{column.width}}")
        lines.append(" | ".join(column_headers))
        
        # Разделитель
        total_width = sum(column.width for column in dynamic_columns) + (len(dynamic_columns) - 1) * 3
        lines.append("─" * total_width)
        
        # Строки данных - используем TableManager для правильного переноса текста
        from utils.table_manager import TableManager
        table_manager = TableManager(self.locale_manager)
        
        for row_data in table_data:
            # Подготавливаем данные для строки
            row_data_list = []
            for column in dynamic_columns:
                value = str(row_data.get(column.key, ""))
                # Используем улучшенную функцию переноса текста из TableManager
                wrapped_value = table_manager._wrap_text(value, column.width, column.width * 5)  # max_name_length = width * 5
                row_data_list.append(wrapped_value)
            
            # Создаем многострочную строку таблицы
            table_lines = table_manager._create_multiline_table_row(row_data_list, 
                TableConfig(
                    table_type=TableType.GOOGLE_SHEETS_PREVIEW,
                    device_type=device_type,
                    columns=dynamic_columns,
                    style=TableStyle(max_name_length=50),
                    title=""
                )
            )
            lines.extend(table_lines)
        
        return "\n".join(lines)
    
    
    async def _format_google_sheets_matching_table(self, matching_result: IngredientMatchingResult, context=None) -> str:
        """Format Google Sheets matching table for editing"""
        # Всегда используем TableManager для правильной локализации
        from utils.table_manager import TableManager
        table_manager = TableManager(self.locale_manager)
        return await table_manager.format_google_sheets_matching_table(matching_result, context)
    
    def _create_google_sheets_table_header(self, context=None) -> str:
        """Create Google Sheets table header"""
        if context:
            # Используем локализованные заголовки
            name_header = self.locale_manager.get_text("formatters.table_headers.name", context)
            ingredient_header = self.locale_manager.get_text("formatters.table_headers.ingredient", context)
            return f"{'№':<2} | {name_header:<25} | {ingredient_header:<20} | {'':<4}"
        return f"{'№':<2} | {'Nama':<25} | {'Bahan':<20} | {'':<4}"
    
    def _create_google_sheets_table_separator(self) -> str:
        """Create Google Sheets table separator"""
        return "-" * 55  # Fixed width to match table structure (2 + 25 + 20 + 4 + 4 = 55)
    
    def _create_google_sheets_table_row(self, row_number: int, match: IngredientMatch) -> str:
        """Create a Google Sheets table row for a match"""
        # Wrap names instead of truncating
        receipt_name_wrapped = self._wrap_text(match.receipt_item_name, 24)
        ingredient_name_wrapped = self._wrap_text(
            match.matched_ingredient_name or "—", 
            20
        )
        
        # Split into lines
        receipt_name_lines = receipt_name_wrapped.split('\n')
        ingredient_name_lines = ingredient_name_wrapped.split('\n')
        
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
                line = f"{row_number:<2} | {receipt_name:<24} | {ingredient_name:<20} | {status_emoji:<4}"
            else:
                # Subsequent lines are indented
                line = f"{'':<2} | {receipt_name:<24} | {ingredient_name:<20} | {'':<4}"
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def _get_google_sheets_status_emoji(self, status) -> str:
        """Get status text for Google Sheets match status"""
        if status == MatchStatus.EXACT_MATCH:
            return "OK"
        elif status == MatchStatus.PARTIAL_MATCH:
            return "OK"
        else:
            return ""
    
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
    
    def _wrap_text(self, text: str, max_width: int) -> str:
        """Wrap text to fit within max_width, breaking on words when possible"""
        wrapped_lines = self.common_handlers.wrap_text(text, max_width)
        return "\n".join(wrapped_lines) if wrapped_lines else text
    
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
