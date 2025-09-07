"""
Google Sheets dispatcher for handling Google Sheets related callback actions
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisService
from services.google_sheets_service import GoogleSheetsService
from services.ingredient_matching_service import IngredientMatchingService
from models.ingredient_matching import IngredientMatchingResult
from handlers.base_callback_handler import BaseCallbackHandler
from utils.common_handlers import CommonHandlers
from utils.ingredient_storage import IngredientStorage


class GoogleSheetsDispatcher(BaseCallbackHandler):
    """Dispatcher for Google Sheets related callback actions"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService, google_sheets_handler=None):
        super().__init__(config, analysis_service)
        
        # Initialize services
        self.google_sheets_service = GoogleSheetsService(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
            spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        self.ingredient_storage = IngredientStorage()
        self.common_handlers = CommonHandlers(config, analysis_service)
        self.google_sheets_handler = google_sheets_handler
        
        # ui_manager is already initialized in BaseCallbackHandler
    
    async def _ensure_google_sheets_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Ensure Google Sheets ingredients are loaded, load them if necessary"""
        return await self.common_handlers.ensure_ingredients_loaded(context, "google_sheets")
    
    async def _handle_google_sheets_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle Google Sheets related actions - EXACT COPY from original callback_handlers.py"""
        query = update.callback_query
        
        if action == "google_sheets_matching":
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context)
        elif action.startswith("gs_page_"):
            page = int(action.split("_")[-1])
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context, page)
        elif action in ["gs_manual_matching", "gs_position_selection"]:
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action in ["gs_upload", "upload_to_google_sheets"]:
            query = update.callback_query
            await query.answer("📊 Загружаю данные в Google Sheets...")
            
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
            
            google_sheets_ingredients = context.bot_data.get('google_sheets_ingredients', {})
            
            google_sheets_ingredients_for_matching = {}
            for ingredient_id, ingredient_data in google_sheets_ingredients.items():
                ingredient_name = ingredient_data.get('name', '')
                if ingredient_name:
                    google_sheets_ingredients_for_matching[ingredient_name] = ingredient_id
            
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            
            saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
            if saved_data:
                matching_result, changed_indices = saved_data
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = changed_indices
            else:
                ingredient_matching_service = IngredientMatchingService()
                matching_result = ingredient_matching_service.match_ingredients(receipt_data, google_sheets_ingredients_for_matching)
                
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = set()
            
            context.user_data['pending_google_sheets_upload'] = {
                'receipt_data': receipt_data,
                'matching_result': matching_result
            }
            
            # Save Google Sheets matching result to context for Excel generation
            context.user_data['google_sheets_matching_result'] = matching_result
            
            await self.google_sheets_handler._show_google_sheets_matching_page(update, context, receipt_data, matching_result)
        elif action == "gs_show_table":
            matching_result = context.user_data.get('ingredient_matching_result')
            receipt_data = context.user_data.get('receipt_data')
            if matching_result:
                await self.google_sheets_handler._show_google_sheets_matching_table(update, context, receipt_data, matching_result)
        elif action.startswith("gs_select_item_"):
            item_index = int(action.split("_")[-1])
            context.user_data['current_gs_matching_item'] = item_index
            await self.google_sheets_handler._show_google_sheets_manual_matching_for_item(update, context, item_index)
        elif action.startswith("gs_select_suggestion_"):
            suggestion_number = int(action.split("_")[-1])
            await self.google_sheets_handler._handle_google_sheets_suggestion_selection(update, context, suggestion_number)
        elif action == "gs_next_item":
            await self.google_sheets_handler._show_google_sheets_position_selection(update, context)
        elif action == "edit_google_sheets_matching":
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
            await self.google_sheets_handler._handle_undo_google_sheets_upload(update, context)
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
        elif action in ["gs_skip_item", "skip_ingredient"]:
            await query.answer("⏭️ Пропускаю позицию...")
            await self.google_sheets_handler._handle_skip_item(update, context)
        elif action in ["gs_next_item", "next_ingredient_match"]:
            await query.answer("➡️ Переход к следующей позиции...")
            await self.google_sheets_handler._handle_next_item(update, context)
        
        return self.config.AWAITING_CORRECTION
    
    async def _execute_google_sheets_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                          receipt_data, matching_result):
        """Execute actual Google Sheets upload - EXACT COPY from original callback_handlers.py"""
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
        """Show upload success page - EXACT COPY from original callback_handlers.py"""
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
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name to max length"""
        return self.common_handlers.truncate_name(name, max_length)
    
    def _get_google_sheets_status_emoji(self, match_status) -> str:
        """Get emoji for Google Sheets match status"""
        status_emojis = {
            'exact': '✅',
            'partial': '⚠️',
            'no_match': '❌'
        }
        return status_emojis.get(match_status.value, '❓')
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        await self.common_handlers.send_long_message_with_keyboard(message, text, reply_markup)