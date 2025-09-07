"""
Refactored callback handlers for Telegram bot
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisService
from services.google_sheets_service import GoogleSheetsService
from models.receipt import ReceiptData
from handlers.base_callback_handler import BaseCallbackHandler
from handlers.receipt_edit_callback_handler import ReceiptEditCallbackHandler
from handlers.ingredient_matching_callback_handler import IngredientMatchingCallbackHandler
from handlers.google_sheets_callback_handler import GoogleSheetsCallbackHandler
from handlers.file_generation_callback_handler import FileGenerationCallbackHandler


class CallbackHandlers(BaseCallbackHandler):
    """Main callback handlers coordinator - refactored version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        super().__init__(config, analysis_service)
        
        # Initialize services
        self.google_sheets_service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        # Initialize specialized handlers
        self.receipt_edit_handler = ReceiptEditCallbackHandler(config, analysis_service)
        self.ingredient_matching_handler = IngredientMatchingCallbackHandler(config, analysis_service)
        self.google_sheets_handler = GoogleSheetsCallbackHandler(config, analysis_service)
        self.file_generation_handler = FileGenerationCallbackHandler(config, analysis_service)
    
    async def handle_correction_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle correction choice callback - main dispatcher"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        print(f"DEBUG: Callback action: {action}")
        
        # Route to appropriate handler based on action
        if action in ["add_row", "edit_total", "auto_calculate_total", "edit_item_", "delete_item_", 
                     "finish_editing", "edit_receipt", "back_to_edit", "delete_row", "edit_line_number",
                     "manual_edit_total", "reanalyze", "back_to_receipt", "back_to_main_menu"] or action.startswith("field_") or action.startswith("apply_"):
            return await self._handle_receipt_edit_actions(update, context, action)
        
        elif action in ["ingredient_matching", "manual_matching", "position_selection", "match_item_", 
                       "select_item_", "select_suggestion_", "next_item", "skip_item", "show_matching_table",
                       "manual_match_ingredients", "rematch_ingredients", "apply_matching_changes",
                       "select_position_for_matching", "back_to_matching_overview", "search_ingredient",
                       "skip_ingredient", "next_ingredient_match", "confirm_back_without_changes",
                       "cancel_back"]:
            return await self._handle_ingredient_matching_actions(update, context, action)
        
        elif action in ["google_sheets_matching", "gs_", "gs_upload", "gs_show_table", "upload_to_google_sheets",
                       "edit_google_sheets_matching", "preview_google_sheets_upload", "confirm_google_sheets_upload",
                       "select_google_sheets_position", "back_to_google_sheets_matching",
                       "back_to_google_sheets_preview", "undo_google_sheets_upload", "generate_excel_file",
                       "gs_skip_item", "gs_next_item", "skip_ingredient", "next_ingredient_match"] or action.startswith("edit_google_sheets_item_") or action.startswith("select_google_sheets_line_") or action.startswith("select_google_sheets_suggestion_") or action.startswith("search_google_sheets_ingredient_") or action.startswith("select_google_sheets_search_") or action.startswith("select_google_sheets_position_match_"):
            return await self._handle_google_sheets_actions(update, context, action)
        
        elif action in ["generate_supply_file", "generate_poster_file", "generate_google_sheets_file",
                       "generate_file_xlsx", "generate_file_from_table", "match_ingredients"]:
            return await self._handle_file_generation_actions(update, context, action)
        
        elif action == "finish":
            # "finish" button no longer needed as report is already shown
            await query.answer("Отчет уже готов!")
            return self.config.AWAITING_CORRECTION
        
        elif action == "cancel":
            return await self._cancel(update, context)
        
        elif action == "analyze_receipt":
            # Handle analyze receipt - delegate to message handlers
            await update.callback_query.edit_message_text(
                "📸 Анализ чека\n\n"
                "Отправьте фото чека для анализа:"
            )
            return self.config.AWAITING_CORRECTION
        
        elif action == "noop":
            # Handle no-op action (empty button)
            await query.answer()
            return self.config.AWAITING_CORRECTION
        
        else:
            print(f"DEBUG: Unknown callback action: {action}")
            await query.answer("Неизвестное действие")
            return self.config.AWAITING_CORRECTION
    
    async def _handle_receipt_edit_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle receipt edit related actions"""
        if action == "add_row":
            await self.receipt_edit_handler._add_new_row(update, context)
        elif action == "edit_total":
            await self.receipt_edit_handler._show_total_edit_menu(update, context)
        elif action == "auto_calculate_total":
            await self.receipt_edit_handler._auto_calculate_total(update, context)
        elif action == "finish_editing":
            await self.receipt_edit_handler._show_final_report_with_edit_button_callback(update, context)
        elif action == "edit_receipt":
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action == "back_to_edit":
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action.startswith("edit_item_"):
            # Handle item editing - set line to edit and show edit menu
            item_number = int(action.split("_")[-1])
            context.user_data['line_to_edit'] = item_number
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self.receipt_edit_handler._send_edit_menu(update, context)
        elif action.startswith("delete_item_"):
            # Handle item deletion - delegate to message handlers
            item_number = int(action.split("_")[-1])
            context.user_data['deleting_item'] = item_number
            await update.callback_query.edit_message_text(
                f"🗑️ Удаление позиции {item_number}\n\n"
                "Подтвердите удаление (да/нет):"
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        elif action == "delete_row":
            # Handle delete row - use temporary message to preserve main receipt
            await self.ui_manager.send_temp(
                update, context,
                "🗑️ Удаление строки\n\n"
                "Введите номер строки для удаления:",
                duration=30
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        elif action == "edit_line_number":
            # Handle edit line number - use temporary message to preserve main receipt
            await self.ui_manager.send_temp(
                update, context,
                "✏️ Редактирование строки\n\n"
                "Введите номер строки для редактирования:",
                duration=30
            )
            return self.config.AWAITING_LINE_NUMBER
        elif action == "manual_edit_total":
            # Handle manual total edit - use temporary message to preserve main receipt
            await self.ui_manager.send_temp(
                update, context,
                "💰 Редактирование общей суммы\n\n"
                "Введите новую общую сумму:",
                duration=30
            )
            return self.config.AWAITING_TOTAL_EDIT
        elif action == "reanalyze":
            # Handle reanalysis - delegate to message handlers
            await update.callback_query.edit_message_text(
                "🔄 Повторный анализ чека\n\n"
                "Отправьте фото чека для повторного анализа:"
            )
            return self.config.AWAITING_CORRECTION
        elif action == "back_to_receipt":
            # Handle back to receipt - restore original data and show fresh root menu
            # Delete the current message before showing receipt
            try:
                await update.callback_query.delete_message()
            except Exception as e:
                print(f"DEBUG: Error deleting message: {e}")
            
            # Restore original receipt data (discard any changes)
            original_data = context.user_data.get('original_data')
            if original_data:
                # Restore original data
                context.user_data['receipt_data'] = ReceiptData.from_dict(original_data.to_dict())
                print("DEBUG: Restored original receipt data, discarding changes")
            else:
                # Fallback to current data if no original data
                receipt_data = context.user_data.get('receipt_data')
                if not receipt_data:
                    await update.callback_query.edit_message_text("❌ Данные чека не найдены")
                    return self.config.AWAITING_CORRECTION
            
            # Use UI Manager to clean up and return to receipt
            await self.ui_manager.back_to_receipt(update, context)
            # Show fresh final report with edit button
            await self.receipt_edit_handler._show_final_report_with_edit_button_callback(update, context)
        elif action == "back_to_main_menu":
            # Handle back to main menu - avoid circular import
            await update.callback_query.edit_message_text(
                "🏠 Главное меню\n\n"
                "Используйте /start для начала новой работы."
            )
            return self.config.AWAITING_CORRECTION
        elif action.startswith("field_"):
            # Handle field editing - delegate to message handlers
            parts = action.split("_")
            if len(parts) >= 3:
                line_number = int(parts[1])
                field_name = parts[2]
                context.user_data['field_to_edit'] = field_name
                context.user_data['line_to_edit'] = line_number
                
                field_display_names = {
                    'name': 'название товара',
                    'quantity': 'количество',
                    'price': 'цену',
                    'total': 'сумму'
                }
                
                field_name_display = field_display_names.get(field_name, field_name)
                temp_message = await self.ui_manager.send_temp(
                    update, context,
                    f"✏️ Редактирование {field_name_display} для строки {line_number}\n\n"
                    f"Введите новое значение:",
                    duration=30
                )
                
                # Add to cleanup list for immediate deletion when user responds
                if 'messages_to_cleanup' not in context.user_data:
                    context.user_data['messages_to_cleanup'] = []
                context.user_data['messages_to_cleanup'].append(temp_message.message_id)
                return self.config.AWAITING_FIELD_EDIT
        elif action.startswith("apply_"):
            # Handle apply changes - show receipt menu
            line_number = int(action.split("_")[-1])
            context.user_data['applying_changes'] = line_number
            
            # Clear field editing context
            context.user_data.pop('field_to_edit', None)
            context.user_data.pop('line_to_edit', None)
            
            # Show receipt menu with edit buttons
            await self.receipt_edit_handler._show_final_report_with_edit_button_callback(update, context)
            return self.config.AWAITING_CORRECTION
        
        return self.config.AWAITING_CORRECTION
    
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
        elif action.startswith("match_item_"):
            item_index = int(action.split("_")[-1])
            await self.ingredient_matching_handler._handle_item_selection_for_matching(update, context, item_index)
        elif action.startswith("select_item_"):
            item_index = int(action.split("_")[-1])
            await self.ingredient_matching_handler._handle_item_selection_for_matching(update, context, item_index)
        elif action.startswith("select_suggestion_"):
            suggestion_number = int(action.split("_")[-1])
            await self.ingredient_matching_handler._handle_ingredient_selection(update, context, suggestion_number)
        elif action == "next_item":
            await self.ingredient_matching_handler._process_next_ingredient_match(update, context)
        elif action == "skip_item":
            await self.ingredient_matching_handler._process_next_ingredient_match(update, context)
        elif action == "manual_match_ingredients":
            await self.ingredient_matching_handler._show_manual_matching_overview(update, context)
        elif action == "rematch_ingredients":
            # Clear existing matching and start fresh
            context.user_data.pop('ingredient_matching_result', None)
            context.user_data.pop('changed_ingredient_indices', None)
            await self.ingredient_matching_handler._show_ingredient_matching_results(update, context)
        elif action == "apply_matching_changes":
            # Apply matching changes - delegate to message handlers
            await update.callback_query.edit_message_text(
                "✅ Изменения сопоставления применены!\n\n"
                "Переходим к следующему шагу..."
            )
            return self.config.AWAITING_CORRECTION
        elif action == "select_position_for_matching":
            await self.ingredient_matching_handler._show_position_selection_interface(update, context)
        elif action == "back_to_matching_overview":
            await self.ingredient_matching_handler._show_manual_matching_overview(update, context)
        elif action == "search_ingredient":
            # Handle ingredient search - delegate to message handlers
            await update.callback_query.edit_message_text(
                "🔍 Поиск ингредиента\n\n"
                "Введите название ингредиента для поиска:"
            )
            return self.config.AWAITING_MANUAL_MATCH
        elif action == "skip_ingredient":
            await self.ingredient_matching_handler._process_next_ingredient_match(update, context)
        elif action == "next_ingredient_match":
            await self.ingredient_matching_handler._process_next_ingredient_match(update, context)
        elif action == "confirm_back_without_changes":
            # Confirm back without changes
            await update.callback_query.edit_message_text(
                "✅ Возврат без сохранения изменений\n\n"
                "Изменения не были сохранены."
            )
            return self.config.AWAITING_CORRECTION
        elif action == "cancel_back":
            # Cancel back action
            await update.callback_query.edit_message_text(
                "❌ Отмена возврата\n\n"
                "Продолжаем работу с текущими данными."
            )
            return self.config.AWAITING_CORRECTION
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_google_sheets_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle Google Sheets related actions"""
        query = update.callback_query
        
        if action == "google_sheets_matching":
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context)
        elif action.startswith("gs_page_"):
            page = int(action.split("_")[-1])
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context, page)
        elif action == "gs_manual_matching":
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "gs_position_selection":
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "gs_upload" or action == "upload_to_google_sheets":
            # User wants to upload data to Google Sheets - restore from backup
            query = update.callback_query
            await query.answer("📊 Загружаю данные в Google Sheets...")
            
            # Get receipt data from context
            receipt_data = context.user_data.get('receipt_data')
            if not receipt_data:
                await query.edit_message_text(
                    "❌ **Нет данных для загрузки**\n\n"
                    "Сначала необходимо загрузить и проанализировать чек.\n"
                    "Нажмите 'Анализировать чек' и загрузите фото чека.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📸 Анализировать чек", callback_data="analyze_receipt")],
                        [InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            # Ensure Google Sheets ingredients are loaded
            if not await self.google_sheets_handler._ensure_google_sheets_ingredients_loaded(context):
                await query.edit_message_text(
                    "❌ **Ошибка загрузки в Google Sheets**\n\n"
                    "Не удалось загрузить справочник ингредиентов для Google Sheets.\n"
                    "Проверьте настройки конфигурации.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 Загрузить в Google Sheets", callback_data="upload_to_google_sheets")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            # Get Google Sheets ingredients from bot data
            google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
            
            # Convert format from {id: {'name': name}} to {name: id} for matching service (same as backup)
            google_sheets_ingredients_for_matching = {}
            for ingredient_id, ingredient_data in google_sheets_ingredients.items():
                ingredient_name = ingredient_data.get('name', '')
                if ingredient_name:
                    google_sheets_ingredients_for_matching[ingredient_name] = ingredient_id
            
            # Get current receipt hash
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            
            # Check if we have saved matching data
            saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
            if saved_data:
                # We have saved data, use it
                matching_result, changed_indices = saved_data
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = changed_indices
                print(f"DEBUG: Using saved matching data for receipt {receipt_hash}")
            else:
                # No saved data found - create new matching with Google Sheets ingredients
                print(f"DEBUG: No saved data found for receipt {receipt_hash}, creating new matching with Google Sheets ingredients")
                from services.ingredient_matching_service import IngredientMatchingService
                ingredient_matching_service = IngredientMatchingService()
                matching_result = ingredient_matching_service.match_ingredients(receipt_data, google_sheets_ingredients_for_matching)
                
                # Save matching result
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = set()
                print(f"DEBUG: Created new matching result with {len(matching_result.matches)} matches")
            
            # Save data for future use
            context.user_data['pending_google_sheets_upload'] = {
                'receipt_data': receipt_data,
                'matching_result': matching_result
            }
            
            # Show Google Sheets matching page (same as original backup)
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context, receipt_data, matching_result)
        elif action == "gs_show_table":
            matching_result = context.user_data.get('ingredient_matching_result')
            receipt_data = context.user_data.get('receipt_data')
            if matching_result:
                await self.google_sheets_handler._show_google_sheets_matching_table(update, context, receipt_data, matching_result)
        elif action == "gs_upload":
            # Direct upload to Google Sheets
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                await self.google_sheets_handler._upload_to_google_sheets(update, context, matching_result)
            else:
                await query.edit_message_text("❌ Результаты сопоставления не найдены")
        elif action.startswith("gs_select_item_"):
            item_index = int(action.split("_")[-1])
            context.user_data['current_gs_matching_item'] = item_index
            await self.google_sheets_handler._show_google_sheets_manual_matching_for_item(update, context, item_index)
        elif action.startswith("gs_select_suggestion_"):
            suggestion_number = int(action.split("_")[-1])
            await self.google_sheets_handler._handle_google_sheets_suggestion_selection(update, context, suggestion_number)
        elif action == "gs_next_item":
            # Process next Google Sheets item
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "edit_google_sheets_matching":
            # Delete the current message before showing position selection
            try:
                await update.callback_query.delete_message()
            except Exception as e:
                print(f"DEBUG: Error deleting message: {e}")
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "preview_google_sheets_upload":
            # User wants to preview Google Sheets upload
            await query.answer("👁️ Показываю предпросмотр...")
            
            # Get pending data
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if not pending_data:
                await query.edit_message_text(
                    "❌ **Ошибка предпросмотра**\n\n"
                    "Данные для предпросмотра не найдены.\n"
                    "Попробуйте начать процесс заново.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 Загрузить в Google Sheets", callback_data="upload_to_google_sheets")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            
            # Show Google Sheets preview
            await self.google_sheets_handler._show_google_sheets_preview(update, context, receipt_data, matching_result)
        elif action == "confirm_google_sheets_upload":
            # User confirmed Google Sheets upload
            await query.answer("📊 Загружаю данные в Google Sheets...")
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Get saved data
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if not pending_data:
                await self.ui_manager.send_menu(
                    update, context,
                    "❌ **Ошибка загрузки в Google Sheets**\n\n"
                    "Данные для загрузки не найдены.\n"
                    "Попробуйте начать процесс заново.",
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 Загрузить в Google Sheets", callback_data="upload_to_google_sheets")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            
            # Execute actual upload
            await self._execute_google_sheets_upload(update, context, receipt_data, matching_result)
            
            # Clear pending data
            context.user_data.pop('pending_google_sheets_upload', None)
            return self.config.AWAITING_CORRECTION
        elif action == "select_google_sheets_position":
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "back_to_google_sheets_matching":
            # Return to Google Sheets matching table
            await query.answer("◀️ Возвращаюсь к таблице сопоставления...")
            
            # Delete the current message (position selection interface) to make it disappear
            try:
                await query.delete_message()
            except Exception as e:
                print(f"DEBUG: Error deleting message: {e}")
            
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if pending_data:
                await self.google_sheets_handler._show_google_sheets_matching_table(update, context, 
                    pending_data['receipt_data'], pending_data['matching_result'])
        elif action == "edit_google_sheets_matching":
            # User wants to edit Google Sheets matching
            await query.answer("✏️ Открываю редактор сопоставления...")
            
            # Get pending data
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if not pending_data:
                await query.edit_message_text(
                    "❌ **Ошибка редактирования сопоставления**\n\n"
                    "Данные для редактирования не найдены.\n"
                    "Попробуйте начать процесс заново.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 Загрузить в Google Sheets", callback_data="upload_to_google_sheets")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            receipt_data = pending_data['receipt_data']
            matching_result = pending_data['matching_result']
            
            # Show Google Sheets matching table
            await self.google_sheets_handler._show_google_sheets_matching_table(update, context, receipt_data, matching_result)
        elif action == "back_to_google_sheets_preview":
            # Return to Google Sheets preview
            await query.answer("◀️ Возвращаюсь к предпросмотру...")
            pending_data = context.user_data.get('pending_google_sheets_upload')
            if pending_data:
                receipt_data = pending_data['receipt_data']
                matching_result = pending_data['matching_result']
                await self.google_sheets_handler._show_google_sheets_preview(update, context, receipt_data, matching_result)
        elif action == "undo_google_sheets_upload":
            # Handle undo upload
            await query.answer("↩️ Отменяю загрузку...")
            await self._handle_undo_google_sheets_upload(update, context)
        elif action == "start_new_receipt":
            # Handle start new receipt
            await update.callback_query.edit_message_text("📸 Загрузите фото нового чека для анализа")
        elif action == "generate_excel_file":
            # Generate Excel file
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                await self.google_sheets_handler._generate_excel_file(update, context)
            else:
                await update.callback_query.edit_message_text("❌ Результаты сопоставления не найдены")
        elif action.startswith("edit_google_sheets_item_"):
            # User wants to edit specific Google Sheets item
            item_index = int(action.split("_")[4])
            await query.answer("✏️ Открываю редактор сопоставления...")
            await self.google_sheets_handler._show_google_sheets_manual_matching_for_item(update, context, item_index)
        elif action.startswith("select_google_sheets_line_"):
            # User selected a line for Google Sheets matching
            line_number = int(action.split("_")[4])
            item_index = line_number - 1  # Convert to 0-based index
            await query.answer(f"Выбрана строка {line_number}")
            
            # Delete the current message (position selection interface) to make it disappear
            try:
                await query.delete_message()
            except Exception as e:
                print(f"DEBUG: Error deleting message: {e}")
            
            await self.google_sheets_handler._show_google_sheets_manual_matching_for_item(update, context, item_index)
        elif action.startswith("select_google_sheets_suggestion_"):
            # User selected a suggestion for Google Sheets matching
            parts = action.split("_")
            item_index = int(parts[4])
            suggestion_index = int(parts[5])
            await query.answer("✅ Выбрано предложение...")
            await self.google_sheets_handler._handle_google_sheets_suggestion_selection(update, context, item_index, suggestion_index)
        elif action.startswith("search_google_sheets_ingredient_"):
            # User wants to search for Google Sheets ingredient
            item_index = int(action.split("_")[4])
            await query.answer("🔍 Введите поисковый запрос...")
            
            print(f"DEBUG: search_google_sheets_ingredient_{item_index} button pressed")
            print(f"DEBUG: Setting google_sheets_search_mode = True for item_index = {item_index}")
            
            # Set search mode - use the correct flag for ingredient search
            context.user_data['google_sheets_search_mode'] = True
            context.user_data['google_sheets_search_item_index'] = item_index
            
            print(f"DEBUG: Flags set - google_sheets_search_mode: {context.user_data.get('google_sheets_search_mode')}")
            print(f"DEBUG: Flags set - google_sheets_search_item_index: {context.user_data.get('google_sheets_search_item_index')}")
            
            await self.ui_manager.send_temp(
                update, context, 
                "Введите наименование ингредиента для поиска в Google Таблицах:", 
                duration=10
            )
            return self.config.AWAITING_CORRECTION
        elif action.startswith("select_google_sheets_search_"):
            # User selected a search result for Google Sheets matching
            parts = action.split("_")
            item_index = int(parts[4])
            result_index = int(parts[5])
            await query.answer("✅ Выбран результат поиска...")
            await self.google_sheets_handler._handle_google_sheets_search_selection(update, context, item_index, result_index)
        elif action.startswith("select_google_sheets_position_match_"):
            # User selected a position match from search results
            parts = action.split("_")
            selected_line = int(parts[4])
            result_index = int(parts[5]) - 1
            await query.answer("✅ Выбрано совпадение...")
            await self.google_sheets_handler._handle_google_sheets_suggestion_selection(update, context, result_index)
        elif action == "gs_skip_item":
            # Skip current item
            await query.answer("⏭️ Пропускаю позицию...")
            await self.google_sheets_handler._handle_skip_item(update, context)
        elif action == "gs_next_item":
            # Move to next item
            await query.answer("➡️ Переход к следующей позиции...")
            await self.google_sheets_handler._handle_next_item(update, context)
        elif action == "skip_ingredient":
            # Skip current ingredient (legacy)
            await query.answer("⏭️ Пропускаю ингредиент...")
            await self.google_sheets_handler._handle_skip_item(update, context)
        elif action == "next_ingredient_match":
            # Move to next ingredient match (legacy)
            await query.answer("➡️ Переход к следующему ингредиенту...")
            await self.google_sheets_handler._handle_next_item(update, context)
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_file_generation_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle file generation related actions"""
        if action == "generate_supply_file":
            await self.file_generation_handler._generate_and_send_supply_file(update, context, "poster")
        elif action == "generate_poster_file":
            await self.file_generation_handler._generate_and_send_supply_file(update, context, "poster")
        elif action == "generate_google_sheets_file":
            await self.file_generation_handler._generate_and_send_supply_file(update, context, "google_sheets")
        elif action == "generate_file_xlsx":
            # Generate Excel file from matching result
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                await self.google_sheets_handler._generate_excel_file(update, context)
            else:
                await update.callback_query.edit_message_text("❌ Результаты сопоставления не найдены")
        elif action == "generate_file_from_table":
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                await self.file_generation_handler._show_matching_table_with_edit_button(update, context, matching_result)
        elif action == "match_ingredients":
            await self.ingredient_matching_handler._show_ingredient_matching_results(update, context)
        
        return self.config.AWAITING_CORRECTION
    
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
    
    async def _cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current operation"""
        query = update.callback_query
        await query.answer()
        
        # Clear all data
        self._clear_receipt_data(context)
        
        # Show start message - avoid circular import
        await query.edit_message_text(
            "❌ Операция отменена\n\n"
            "Используйте /start для начала новой работы."
        )
        
        return self.config.AWAITING_CORRECTION
    
    async def _execute_google_sheets_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                          receipt_data, matching_result):
        """Execute actual Google Sheets upload"""
        try:
            # Save Google Sheets matching result to context for Excel generation
            context.user_data['google_sheets_matching_result'] = matching_result
            
            # Show upload summary
            summary = self.google_sheets_service.get_upload_summary(receipt_data, matching_result)
            
            # Upload data
            success, message = self.google_sheets_service.upload_receipt_data(
                receipt_data, 
                matching_result,
                self.config.GOOGLE_SHEETS_WORKSHEET_NAME
            )
            
            if success:
                # Save upload data for potential undo
                context.user_data['last_google_sheets_upload'] = {
                    'worksheet_name': self.config.GOOGLE_SHEETS_WORKSHEET_NAME,
                    'row_count': len(receipt_data.items),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Show new success page interface
                await self._show_upload_success_page(update, context, summary, message)
            else:
                # Show error message
                error_text = f"❌ **Ошибка загрузки в Google Sheets**\n\n{message}\n\n{summary}"
                await self.ui_manager.send_menu(
                    update, context,
                    error_text,
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Попробовать снова", callback_data="upload_to_google_sheets")],
                        [InlineKeyboardButton("📄 Сгенерировать файл", callback_data="generate_file_from_table")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                    ]),
                    'Markdown'
                )
                
        except Exception as e:
            print(f"DEBUG: Error uploading to Google Sheets: {e}")
            await self.ui_manager.send_menu(
                update, context,
                f"❌ **Критическая ошибка**\n\nПроизошла неожиданная ошибка при загрузке в Google Sheets:\n`{str(e)}`",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
    
    async def _show_upload_success_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      summary: str, message: str):
        """Show the new upload success page interface"""
        # Clean up all messages except anchor first
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
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
        
        await self.ui_manager.send_menu(
            update, context,
            success_text,
            reply_markup,
            'Markdown'
        )
    
    async def _handle_undo_google_sheets_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle undo Google Sheets upload"""
        try:
            # Get last upload data
            last_upload = context.user_data.get('last_google_sheets_upload')
            if not last_upload:
                await update.callback_query.edit_message_text(
                    "❌ **Нет данных о последней загрузке для отмены**\n\n"
                    "Информация о последней загрузке не найдена.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            # Get upload details
            worksheet_name = last_upload.get('worksheet_name', 'Receipts')
            row_count = last_upload.get('row_count', 0)
            
            if row_count <= 0:
                await update.callback_query.edit_message_text(
                    "❌ **Нет данных для отмены**\n\n"
                    "Количество строк для отмены равно нулю.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
                    ]),
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_CORRECTION
            
            # Attempt to delete the uploaded rows
            success, message = self.google_sheets_service.delete_last_uploaded_rows(worksheet_name, row_count)
            
            if success:
                # Clear the last upload data
                context.user_data.pop('last_google_sheets_upload', None)
                
                # Get the data for preview
                pending_data = context.user_data.get('pending_google_sheets_upload')
                if pending_data:
                    receipt_data = pending_data['receipt_data']
                    matching_result = pending_data['matching_result']
                    
                    # Show regular preview (same as before upload)
                    await self.google_sheets_handler._show_google_sheets_preview(update, context, receipt_data, matching_result)
                else:
                    # Fallback if no pending data
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
            else:
                # Show error message
                await update.callback_query.edit_message_text(
                    f"❌ **Ошибка отмены загрузки**\n\n"
                    f"Не удалось отменить загрузку: {message}\n\n"
                    f"Попробуйте удалить данные вручную в Google Sheets.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")],
                        [InlineKeyboardButton("🔄 Попробовать снова", callback_data="undo_google_sheets_upload")]
                    ]),
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            print(f"DEBUG: Error in undo Google Sheets upload: {e}")
            await update.callback_query.edit_message_text(
                f"❌ **Произошла ошибка при отмене загрузки**\n\n"
                f"Неожиданная ошибка: {str(e)}\n\n"
                f"Попробуйте удалить данные вручную в Google Sheets.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Вернуться к чеку", callback_data="back_to_receipt")]
                ]),
                parse_mode='Markdown'
            )
        
        return self.config.AWAITING_CORRECTION
