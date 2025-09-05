"""
Callback handlers for Telegram bot
"""
import asyncio
import json
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from models.receipt import ReceiptData, ReceiptItem
from models.ingredient_matching import IngredientMatchingResult
from services.ai_service import ReceiptAnalysisService
from services.ingredient_matching_service import IngredientMatchingService
from utils.formatters import ReceiptFormatter, NumberFormatter, TextParser
from utils.ingredient_formatter import IngredientFormatter
from utils.ingredient_storage import IngredientStorage
from utils.receipt_processor import ReceiptProcessor
from utils.ui_manager import UIManager
from validators.receipt_validator import ReceiptValidator


class CallbackHandlers:
    """Handlers for Telegram callback queries"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.formatter = ReceiptFormatter()
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
        self.processor = ReceiptProcessor()
        self.validator = ReceiptValidator()
        self.ingredient_matching_service = IngredientMatchingService()
        self.ingredient_formatter = IngredientFormatter()
        self.ingredient_storage = IngredientStorage()
        self.ui_manager = UIManager(config)
    
    async def handle_correction_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle correction choice callback"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        print(f"DEBUG: Callback action: {action}")
        
        if action == "finish":
            # "finish" button no longer needed as report is already shown
            await query.answer("Отчет уже готов!")
            return self.config.AWAITING_CORRECTION
        
        if action == "add_row":
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Add new row
            await self._add_new_row(update, context)
            return self.config.AWAITING_FIELD_EDIT
        
        if action == "delete_row":
            # Request line number for deletion
            await self.ui_manager.send_temp(
                update, context,
                "Введите номер строки для удаления:\n\n"
                "Например: `3` (для удаления строки 3)",
                duration=30
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        
        if action == "edit_total":
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Show total edit menu
            await self._show_total_edit_menu(update, context)
            return self.config.AWAITING_CORRECTION
        
        if action == "auto_calculate_total":
            # Automatically calculate total
            await self._auto_calculate_total(update, context)
            return self.config.AWAITING_CORRECTION
        
        if action == "manual_edit_total":
            # Request new total sum manually
            current_total = context.user_data.get('receipt_data', {}).grand_total_text
            formatted_total = self.number_formatter.format_number_with_spaces(self.text_parser.parse_number_from_text(current_total))
            
            await self.ui_manager.send_temp(
                update, context,
                f"Текущая итоговая сумма: **{formatted_total}**\n\n"
                "Введите новую итоговую сумму:",
                duration=30
            )
            return self.config.AWAITING_TOTAL_EDIT
        
        if action == "edit_line_number":
            # Request line number for editing
            await self.ui_manager.send_temp(
                update, context,
                "Введите номер строки для редактирования:\n\n"
                "Например: `3` (для редактирования строки 3)",
                duration=30
            )
            return self.config.AWAITING_LINE_NUMBER
        
        if action == "reanalyze":
            # Delete old report
            await query.answer("🔄 Анализирую фото заново...")
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Clear all old data
            self._clear_receipt_data(context)
            
            # Send photo to Gemini again
            try:
                analysis_data = self.analysis_service.analyze_receipt(self.config.PHOTO_FILE_NAME)
                
                # Convert to ReceiptData model
                receipt_data = ReceiptData.from_dict(analysis_data)
                
                # Validate and correct data
                is_valid, message = self.validator.validate_receipt_data(receipt_data)
                if not is_valid:
                    print(f"Предупреждение валидации: {message}")
                
                context.user_data['receipt_data'] = receipt_data
                # Save original data for change tracking
                context.user_data['original_data'] = ReceiptData.from_dict(receipt_data.to_dict())  # Deep copy
                
                # Show new report
                await self._show_final_report_with_edit_button_callback(update, context)
                return self.config.AWAITING_CORRECTION
                
            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
                print(f"Ошибка парсинга JSON или структуры данных от Gemini: {e}")
                await query.message.reply_text("Не удалось распознать структуру чека. Попробуйте сделать фото более четким.")
                return self.config.AWAITING_CORRECTION
        
        if action == "match_ingredients":
            # Start ingredient matching process
            await query.answer("🔍 Загружаю таблицу сопоставления ингредиентов...")
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Get receipt data and poster ingredients
            receipt_data = context.user_data.get('receipt_data')
            poster_ingredients = context.bot_data.get('poster_ingredients', {})
            
            if not receipt_data:
                await query.message.reply_text("Ошибка: данные чека не найдены.")
                return self.config.AWAITING_CORRECTION
            
            if not poster_ingredients:
                await query.message.reply_text("Ошибка: справочник ингредиентов не загружен.")
                return self.config.AWAITING_CORRECTION
            
            # Get current receipt hash
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            print(f"DEBUG: Looking for saved data for user {user_id}, receipt {receipt_hash}")
            
            # ALWAYS try to load from persistent storage first (this ensures we get the correct data for this specific receipt)
            saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
            
            if saved_data:
                # Load existing matching data for this specific receipt
                matching_result, changed_indices = saved_data
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = changed_indices
                context.user_data['current_match_index'] = 0
                print(f"DEBUG: Loaded existing matching data from storage with {len(matching_result.matches)} matches, {len(changed_indices)} changed indices")
            else:
                # No saved data found - this should not happen if auto-creation works correctly
                print(f"DEBUG: No saved data found for receipt {receipt_hash}, creating new matching")
                matching_result = self.ingredient_matching_service.match_ingredients(receipt_data, poster_ingredients)
                
                # Save matching result
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['current_match_index'] = 0
                context.user_data['changed_ingredient_indices'] = set()
                
                # Save to persistent storage
                self._save_ingredient_matching_data(user_id, context)
                print(f"DEBUG: Created new matching data with {len(matching_result.matches)} matches")
            
            # Show matching results
            await self._show_ingredient_matching_results(update, context)
            return self.config.AWAITING_INGREDIENT_MATCHING
        
        if action == "manual_match_ingredients":
            # Start manual matching process
            await query.answer("✋ Начинаю ручное сопоставление...")
            
            matching_result = context.user_data.get('ingredient_matching_result')
            if not matching_result:
                await query.message.reply_text("Ошибка: результаты сопоставления не найдены.")
                return self.config.AWAITING_CORRECTION
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Show new manual matching interface with all items that need matching
            await self._show_manual_matching_overview(update, context)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action == "rematch_ingredients":
            # Restart ingredient matching
            await query.answer("🔄 Перезапускаю сопоставление...")
            
            receipt_data = context.user_data.get('receipt_data')
            poster_ingredients = context.bot_data.get('poster_ingredients', {})
            
            if not receipt_data or not poster_ingredients:
                await query.message.reply_text("Ошибка: данные не найдены.")
                return self.config.AWAITING_CORRECTION
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Perform ingredient matching again
            matching_result = self.ingredient_matching_service.match_ingredients(receipt_data, poster_ingredients)
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['current_match_index'] = 0
            context.user_data['changed_ingredient_indices'] = set()
            
            # Save to persistent storage
            user_id = update.effective_user.id
            self._save_ingredient_matching_data(user_id, context)
            
            # Clear matching data from context so it will be loaded from storage next time
            context.user_data.pop('ingredient_matching_result', None)
            context.user_data.pop('changed_ingredient_indices', None)
            context.user_data.pop('current_match_index', None)
            
            # Show matching results (will load from storage)
            await self._show_ingredient_matching_results(update, context)
            return self.config.AWAITING_INGREDIENT_MATCHING
        
        if action == "back_to_receipt":
            # Check if there are any changes made
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            has_changes = len(changed_indices) > 0
            
            if has_changes:
                # Show confirmation dialog
                await self._show_back_confirmation_dialog(update, context)
                return self.config.AWAITING_INGREDIENT_MATCHING
            else:
                # No changes, but still save current state before returning
                matching_result = context.user_data.get('ingredient_matching_result')
                receipt_data = context.user_data.get('receipt_data')
                
                if matching_result and receipt_data:
                    # Save current state to persistent storage
                    user_id = update.effective_user.id
                    receipt_hash = receipt_data.get_receipt_hash()
                    success = self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, receipt_hash)
                    print(f"DEBUG: Saved state before returning - success: {success}")
                
                # Always clear matching data from context so it will be loaded from storage next time
                context.user_data.pop('ingredient_matching_result', None)
                context.user_data.pop('changed_ingredient_indices', None)
                context.user_data.pop('current_match_index', None)
                
                await query.answer("📋 Возвращаюсь к чеку...")
                await self.ui_manager.cleanup_all_except_anchor(update, context)
                await self._show_final_report_with_edit_button_callback(update, context)
                return self.config.AWAITING_CORRECTION
        
        if action == "next_ingredient_match":
            # Move to next ingredient match
            await query.answer("➡️ Переход к следующему ингредиенту...")
            
            current_match_index = context.user_data.get('current_match_index', 0)
            matching_result = context.user_data.get('ingredient_matching_result')
            
            if not matching_result:
                await query.message.reply_text("Ошибка: данные сопоставления не найдены.")
                return self.config.AWAITING_CORRECTION
            
            current_match_index += 1
            context.user_data['current_match_index'] = current_match_index
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            if current_match_index >= len(matching_result.matches):
                # All matches processed, show final result
                await self._show_final_ingredient_matching_result(update, context)
            else:
                # Show next match
                await self._show_manual_matching_for_current_item(update, context)
            
            return self.config.AWAITING_MANUAL_MATCH
        
        if action.startswith("select_ingredient_"):
            # Handle ingredient selection
            suggestion_number = int(action.split('_')[2])
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._handle_ingredient_selection(update, context, suggestion_number)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action == "search_ingredient":
            # Handle search request
            await self.ui_manager.send_temp(
                update, context, "🔍 Введите поисковый запрос в текстовом сообщении", duration=10
            )
            context.user_data['awaiting_search'] = True
            return self.config.AWAITING_MANUAL_MATCH
        
        if action == "skip_ingredient":
            # Skip current ingredient
            await query.answer("⏭️ Пропускаю ингредиент...")
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._process_next_ingredient_match(update, context)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action.startswith("select_search_"):
            # Handle search result selection
            suggestion_number = int(action.split('_')[2])
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._handle_search_result_selection(update, context, suggestion_number)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action.startswith("select_item_"):
            # Handle item selection for manual matching
            item_index = int(action.split('_')[2])
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._handle_item_selection_for_matching(update, context, item_index)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action == "select_position_for_matching":
            # Handle position selection request
            print(f"DEBUG: select_position_for_matching called")
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Show the same table as before, but with position selection interface
            await self._show_position_selection_interface(update, context)
            return self.config.AWAITING_MANUAL_MATCH
        
        
        if action == "back_to_matching_overview":
            # Return to matching overview
            await query.answer("📋 Возвращаюсь к обзору сопоставления...")
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Clear position selection mode flag
            context.user_data.pop('in_position_selection_mode', None)
            context.user_data.pop('selected_line_number', None)
            context.user_data.pop('position_match_search_results', None)
            
            await self._show_manual_matching_overview(update, context)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action.startswith("select_position_match_"):
            # Handle position match selection from search results
            position_number = int(action.split('_')[3])
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._handle_position_match_selection(update, context, position_number)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action.startswith("select_position_"):
            # Handle position selection from search results
            position_number = int(action.split('_')[2])
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._handle_position_selection(update, context, position_number)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action.startswith("match_item_"):
            # Handle item matching with selected position
            parts = action.split('_')
            item_index = int(parts[2])
            position_id = parts[3]
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._handle_item_position_matching(update, context, item_index, position_id)
            return self.config.AWAITING_MANUAL_MATCH
        
        if action == "confirm_back_without_changes":
            # User confirmed to go back without saving changes
            # But we still save the current state to preserve any work done
            matching_result = context.user_data.get('ingredient_matching_result')
            receipt_data = context.user_data.get('receipt_data')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if matching_result and receipt_data:
                # Save current state to persistent storage
                user_id = update.effective_user.id
                receipt_hash = receipt_data.get_receipt_hash()
                success = self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, receipt_hash)
                print(f"DEBUG: Saved state before returning without applying - success: {success}")
            
            # Always clear matching data from context so it will be loaded from storage next time
            context.user_data.pop('ingredient_matching_result', None)
            context.user_data.pop('changed_ingredient_indices', None)
            context.user_data.pop('current_match_index', None)
            
            await query.answer("📋 Возвращаюсь к чеку...")
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            await self._show_final_report_with_edit_button_callback(update, context)
            return self.config.AWAITING_CORRECTION
        
        if action == "cancel_back":
            # User cancelled going back, return to ingredient matching
            await query.answer("❌ Отменено")
            await self._show_ingredient_matching_results(update, context)
            return self.config.AWAITING_INGREDIENT_MATCHING
        
        if action == "apply_matching_changes":
            # Apply matching changes and return to main receipt
            await query.answer("✅ Применяю изменения...")
            
            # Get matching result and receipt data
            matching_result = context.user_data.get('ingredient_matching_result')
            receipt_data = context.user_data.get('receipt_data')
            
            if not matching_result or not receipt_data:
                await query.message.reply_text("Ошибка: данные сопоставления или чека не найдены.")
                return self.config.AWAITING_CORRECTION
            
            # Save matching data to persistent storage
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            print(f"DEBUG: Before saving - user_id: {user_id}, receipt_hash: {receipt_hash}")
            print(f"DEBUG: Before saving - changed_indices: {changed_indices}")
            success = self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, receipt_hash)
            print(f"DEBUG: Applied changes - saved {len(matching_result.matches)} matches, {len(changed_indices)} changed indices, success: {success}")
            
            # Clear matching data from context so it will be loaded from storage next time
            # This ensures we always get the latest saved version
            context.user_data.pop('ingredient_matching_result', None)
            context.user_data.pop('changed_ingredient_indices', None)
            context.user_data.pop('current_match_index', None)
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Return to main receipt
            await self._show_final_report_with_edit_button_callback(update, context)
            return self.config.AWAITING_CORRECTION
        
        if action == "cancel":
            # Check if we're in edit menu
            if context.user_data.get('line_to_edit'):
                # Clean up all messages except anchor before showing new menu
                await self.ui_manager.cleanup_all_except_anchor(update, context)
                
                # Return to updated report
                await self._show_final_report_with_edit_button_callback(update, context)
                return self.config.AWAITING_CORRECTION
            else:
                # Clear position selection mode flag
                context.user_data.pop('in_position_selection_mode', None)
                context.user_data.pop('selected_line_number', None)
                context.user_data.pop('position_match_search_results', None)
                
                # Regular cancellation
                await self._cancel(update, context)
                return self.config.AWAITING_CORRECTION
        
        if action.startswith("edit_"):
            line_number_to_edit = int(action.split('_')[1])
            context.user_data['line_to_edit'] = line_number_to_edit
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            await self._send_edit_menu(update, context)
            return self.config.AWAITING_FIELD_EDIT
        
        if action.startswith("field_"):
            # Handle field selection for editing
            parts = action.split('_')
            line_number = int(parts[1])
            field_name = parts[2]
            
            context.user_data['line_to_edit'] = line_number
            context.user_data['field_to_edit'] = field_name
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            data: ReceiptData = context.user_data['receipt_data']
            item_to_edit = data.get_item(line_number)
            
            field_labels = {
                'name': 'название товара',
                'quantity': 'количество',
                'price': 'цену за единицу',
                'total': 'сумму'
            }
            
            current_value = getattr(item_to_edit, field_name, '')
            if field_name in ['quantity', 'price', 'total'] and isinstance(current_value, (int, float)):
                current_value = self.number_formatter.format_number_with_spaces(current_value)
            
            await self.ui_manager.send_temp(
                update, context,
                f"Редактируете строку {line_number}\n"
                f"Текущее {field_labels[field_name]}: **{current_value}**\n\n"
                f"Введите новое {field_labels[field_name]}:",
                duration=30
            )
            return self.config.AWAITING_FIELD_EDIT
        
        if action.startswith("apply_"):
            line_number = int(action.split('_')[1])
            
            # Automatically update item status before applying
            data: ReceiptData = context.user_data.get('receipt_data', {})
            item_to_apply = data.get_item(line_number)
            if item_to_apply:
                item_to_apply = self.processor.auto_update_item_status(item_to_apply)
            
            # Clean up all messages except anchor before showing new menu
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Show message about applying changes
            await self.ui_manager.send_temp(
                update, context, "✅ Изменения применены! Обновляю таблицу...", duration=2
            )
            
            # Apply changes and return to updated report
            await self._show_final_report_with_edit_button_callback(update, context)
            
            return self.config.AWAITING_CORRECTION
        
        # Handle old format for compatibility
        line_number_to_edit = int(action.split('_')[1])
        context.user_data['line_to_edit'] = line_number_to_edit
        
        # Clean up all messages except anchor before showing new menu
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number_to_edit)
        
        await self.ui_manager.send_temp(
            update, context,
            f"Вы исправляете строку: **{item_to_edit.name}**.\n\n"
            "Введите правильные данные в формате:\n"
            "`Название, Количество, Цена за единицу, Сумма`\n\n"
            "Пример: `Udang Kupas, 4, 150000, 600000`",
            duration=30
        )
        
        return self.config.AWAITING_INPUT
    
    async def _add_new_row(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add new row to table"""
        data: ReceiptData = context.user_data.get('receipt_data')
        
        # Find maximum line number
        max_line_number = data.get_max_line_number()
        new_line_number = max_line_number + 1
        
        # Create new row with empty data
        new_item = ReceiptItem(
            line_number=new_line_number,
            name='Новый товар',
            quantity=1.0,
            price=0.0,
            total=0.0,
            status='needs_review',
            auto_calculated=False
        )
        
        # Add new row to data
        data.add_item(new_item)
        
        # Set new row for editing
        context.user_data['line_to_edit'] = new_line_number
        
        # Show edit menu for new row
        await self._send_edit_menu(update, context)
    
    async def _show_total_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show total edit menu"""
        data: ReceiptData = context.user_data.get('receipt_data', {})
        current_total = data.grand_total_text
        formatted_total = self.number_formatter.format_number_with_spaces(self.text_parser.parse_number_from_text(current_total))
        
        # Calculate automatic sum
        calculated_total = self.formatter.calculate_total_sum(data)
        formatted_calculated_total = self.number_formatter.format_number_with_spaces(calculated_total)
        
        text = f"**Редактирование итого:**\n\n"
        text += f"💰 **Текущая итоговая сумма:** {formatted_total}\n"
        text += f"🧮 **Автоматически рассчитанная сумма:** {formatted_calculated_total}\n\n"
        text += "Выберите действие:"
        
        keyboard = [
            [
                InlineKeyboardButton("🧮 Рассчитать автоматически", callback_data="auto_calculate_total"),
                InlineKeyboardButton("✏️ Ввести вручную", callback_data="manual_edit_total")
            ],
            [
                InlineKeyboardButton("❌ Отмена", callback_data="cancel")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Determine chat_id and message sending method
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
            reply_method = update.callback_query.message.reply_text
        elif hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
            reply_method = update.message.reply_text
        else:
            return
        
        message = await self.ui_manager.send_menu(
            update, context, text, reply_markup, 'Markdown'
        )
        
        # Save message ID for subsequent deletion
        context.user_data['total_edit_menu_message_id'] = message.message_id
    
    async def _auto_calculate_total(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Automatically calculate total based on all line sums"""
        data: ReceiptData = context.user_data.get('receipt_data', {})
        
        # Calculate total sum of all positions
        calculated_total = self.formatter.calculate_total_sum(data)
        
        # Update total sum in data
        data.grand_total_text = str(int(calculated_total)) if calculated_total == int(calculated_total) else str(calculated_total)
        
        # Delete total edit menu message
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=context.user_data.get('total_edit_menu_message_id')
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение с меню редактирования итого: {e}")
        
        # Show success message
        formatted_total = self.number_formatter.format_number_with_spaces(calculated_total)
        await self.ui_manager.send_temp(
            update, context, f"✅ Итого автоматически рассчитано: **{formatted_total}**", duration=2
        )
        
        # Return to updated report
        await self._show_final_report_with_edit_button_callback(update, context)
    
    async def _send_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id_to_edit: int = None):
        """Send edit menu for specific line"""
        line_number = context.user_data.get('line_to_edit')
        data: ReceiptData = context.user_data['receipt_data']
        item_to_edit = data.get_item(line_number)
        
        if not item_to_edit:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: строка не найдена")
            return
        
        # Automatically calculate sum and update status before display
        item_to_edit = self.processor.auto_calculate_total_if_needed(item_to_edit)
        item_to_edit = self.processor.auto_update_item_status(item_to_edit)
        
        # Format current values
        name = item_to_edit.name
        quantity = self.number_formatter.format_number_with_spaces(item_to_edit.quantity)
        price = self.number_formatter.format_number_with_spaces(item_to_edit.price)
        total = self.number_formatter.format_number_with_spaces(item_to_edit.total)
        
        # Check if sum was automatically calculated
        is_auto_calculated = item_to_edit.auto_calculated
        
        # Determine current status (flag)
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
        
        # Show sum with note about whether it was automatically calculated
        if is_auto_calculated:
            text += f"💵 **Сумма:** {total} *(автоматически рассчитана)*\n\n"
        else:
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
        
        # Determine chat_id and message sending method
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
            reply_method = update.callback_query.message.reply_text
        elif hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
            reply_method = update.message.reply_text
        else:
            return
        
        if message_id_to_edit:
            # Edit existing message
            success = await self.ui_manager.edit_menu(
                update, context, message_id_to_edit, text, reply_markup, 'Markdown'
            )
            if not success:
                # If couldn't edit, send new message
                message = await self.ui_manager.send_menu(
                    update, context, text, reply_markup, 'Markdown'
                )
                context.user_data['edit_menu_message_id'] = message.message_id
        else:
            # Create new message
            message = await self.ui_manager.send_menu(
                update, context, text, reply_markup, 'Markdown'
            )
            # Save message ID for subsequent editing
            context.user_data['edit_menu_message_id'] = message.message_id
    
    async def _show_final_report_with_edit_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons (for callback query)"""
        final_data: ReceiptData = context.user_data.get('receipt_data')
        
        if not final_data:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Произошла ошибка, данные не найдены.")
            return

        try:
            # Automatically update statuses of all elements
            final_data = self.processor.auto_update_all_statuses(final_data)
            context.user_data['receipt_data'] = final_data
            
            # Check if there are errors
            has_errors = not self.processor.check_all_items_confirmed(final_data)
            
            # Create aligned table programmatically
            aligned_table = self.formatter.format_aligned_table(final_data)
            
            # Calculate total sum
            calculated_total = self.formatter.calculate_total_sum(final_data)
            receipt_total = self.text_parser.parse_number_from_text(final_data.grand_total_text)
            
            # Form final report
            final_report = ""
            
            # Add red marker if there are errors
            if has_errors:
                final_report += "🔴 **Обнаружены ошибки в данных чека**\n\n"
            
            final_report += f"```\n{aligned_table}\n```\n\n"
            
            if abs(calculated_total - receipt_total) < 0.01:
                final_report += "✅ **Итоговая сумма соответствует!**\n"
            else:
                difference = abs(calculated_total - receipt_total)
                final_report += f"❗ **Несоответствие итоговой суммы! Разница: {self.number_formatter.format_number_with_spaces(difference)}**\n"
            
            # Save report in cache for quick access
            context.user_data['cached_final_report'] = final_report
            
            # Create buttons
            keyboard = []
            
            # If there are errors, add buttons for fixing problematic lines
            if has_errors:
                for item in final_data.items:
                    status = item.status
                    
                    # Check calculation mismatch
                    quantity = item.quantity
                    price = item.price
                    total = item.total
                    has_calculation_error = False
                    
                    if quantity is not None and price is not None and total is not None and quantity > 0 and price > 0 and total > 0:
                        expected_total = quantity * price
                        has_calculation_error = abs(expected_total - total) > 0.01
                    
                    # Check if name is unreadable
                    item_name = item.name
                    is_unreadable = item_name == "???" or item_name == "**не распознано**"
                    
                    # If there are calculation errors, unreadable data or status not confirmed
                    if status != 'confirmed' or has_calculation_error or is_unreadable:
                        keyboard.append([InlineKeyboardButton(
                            f"Исправить строку {item.line_number}",
                            callback_data=f"edit_{item.line_number}"
                        )])
            
            # Add line management buttons
            keyboard.append([
                InlineKeyboardButton("➕ Добавить строку", callback_data="add_row"),
                InlineKeyboardButton("➖ Удалить строку", callback_data="delete_row")
            ])
            
            # Add total edit button
            keyboard.append([InlineKeyboardButton("💰 Редактировать Итого", callback_data="edit_total")])
            
            # Add reanalysis button
            keyboard.append([InlineKeyboardButton("🔄 Проанализировать заново", callback_data="reanalyze")])
            
            # Add ingredient matching button
            keyboard.append([InlineKeyboardButton("🔍 Сопоставить ингредиенты", callback_data="match_ingredients")])
            
            # Add general buttons
            keyboard.append([InlineKeyboardButton("🔢 Редактировать строку по номеру", callback_data="edit_line_number")])
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Check if there's saved table message
            table_message_id = context.user_data.get('table_message_id')
            
            if table_message_id:
                # Try to edit existing table message
                success = await self.ui_manager.edit_menu(
                    update, context, table_message_id, final_report, reply_markup
                )
                if not success:
                    # If couldn't edit, send new message
                    message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
                    context.user_data['table_message_id'] = message.message_id
            else:
                # If no saved ID, send new message
                message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
                context.user_data['table_message_id'] = message.message_id
        
        except Exception as e:
            print(f"Ошибка при формировании отчета: {e}")
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(f"Произошла ошибка при формировании отчета: {e}")
    
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
    
    async def _cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancellation"""
        # Handle both regular message and callback query
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text("Операция отменена.")
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.edit_text("Операция отменена.")
        
        context.user_data.clear()
        return self.config.AWAITING_CORRECTION
    
    def _save_ingredient_matching_data(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Save ingredient matching data to persistent storage"""
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        receipt_data = context.user_data.get('receipt_data')
        
        if matching_result and receipt_data:
            receipt_hash = receipt_data.get_receipt_hash()
            success = self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, receipt_hash)
            print(f"DEBUG: Saved matching data for user {user_id}, receipt {receipt_hash}, success: {success}")
            print(f"DEBUG: Saved {len(matching_result.matches)} matches, {len(changed_indices)} changed indices")
        else:
            print(f"DEBUG: Cannot save matching data - matching_result: {matching_result is not None}, receipt_data: {receipt_data is not None}")
    
    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all receipt-related data from context"""
        keys_to_clear = [
            'receipt_data', 'original_data', 'line_to_edit', 'field_to_edit',
            'cached_final_report', 'table_message_id', 'edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id', 'ingredient_matching_result', 'current_match_index',
            'changed_ingredient_indices', 'search_results', 'position_search_results',
            'awaiting_search', 'awaiting_position_search', 'in_position_selection_mode',
            'selected_line_number', 'position_match_search_results', 'awaiting_ingredient_name_for_position'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    async def _show_ingredient_matching_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ingredient matching results"""
        # Always load from persistent storage to ensure we have the correct data for this receipt
        user_id = update.effective_user.id
        receipt_data = context.user_data.get('receipt_data')
        
        if not receipt_data:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: данные чека не найдены.")
            return
        
        # Get current receipt hash
        current_receipt_hash = receipt_data.get_receipt_hash()
        
        # Try to load from persistent storage for current receipt
        saved_data = self.ingredient_storage.load_matching_result(user_id, current_receipt_hash)
        
        if saved_data:
            # Load existing matching data for current receipt
            matching_result, changed_indices = saved_data
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['changed_ingredient_indices'] = changed_indices
            print(f"DEBUG: Loaded matching data from storage for current receipt with {len(matching_result.matches)} matches, {len(changed_indices)} changed indices")
        else:
            print(f"DEBUG: No saved data for current receipt")
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: результаты сопоставления не найдены.")
            return
        
        # Format results
        print(f"DEBUG: Formatting table with changed_indices: {changed_indices}")
        results_text = self.ingredient_formatter.format_matching_table(matching_result, changed_indices)
        
        # Create action buttons
        keyboard = []
        
        # Manual matching button is now always available as "Сопоставить вручную"
        
        # Check if all items are matched
        all_matched = all(
            match.match_status.value == 'exact' 
            for match in matching_result.matches
        )
        
        # Check if there are any changes made
        has_changes = len(changed_indices) > 0
        
        if all_matched:
            # All items are matched, show Apply button only if there are changes
            if has_changes:
                keyboard.extend([
                    [InlineKeyboardButton("✋ Сопоставить вручную", callback_data="manual_match_ingredients")],
                    [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
                    [InlineKeyboardButton("✅ Применить", callback_data="apply_matching_changes")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ])
            else:
                keyboard.extend([
                    [InlineKeyboardButton("✋ Сопоставить вручную", callback_data="manual_match_ingredients")],
                    [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ])
        else:
            # Some items need matching, show regular buttons
            keyboard.extend([
                [InlineKeyboardButton("✋ Сопоставить вручную", callback_data="manual_match_ingredients")],
                [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await self.ui_manager.send_menu(
                update, context, results_text, reply_markup, 'Markdown'
            )
    
    async def _show_manual_matching_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching overview with all items that need matching"""
        # First check if we have data in context
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        
        if not matching_result:
            # Try to load from persistent storage
            user_id = update.effective_user.id
            receipt_data = context.user_data.get('receipt_data')
            
            if receipt_data:
                receipt_hash = receipt_data.get_receipt_hash()
                saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
                if saved_data:
                    matching_result, changed_indices = saved_data
                    # Update context with loaded data
                    context.user_data['ingredient_matching_result'] = matching_result
                    context.user_data['changed_ingredient_indices'] = changed_indices
                    # Reset current match index when loading from storage
                    context.user_data['current_match_index'] = 0
        
        if not matching_result:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return
        
        # Delete previous menu messages if they exist
        await self._cleanup_previous_menus(update, context)
        
        # Show the same table as before, but with manual matching interface
        # Format results
        print(f"DEBUG: Formatting table with changed_indices: {changed_indices}")
        results_text = self.ingredient_formatter.format_matching_table(matching_result, changed_indices)
        
        # Find items that need manual matching (yellow/red status)
        items_needing_matching = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status.value in ['partial', 'no_match']:
                items_needing_matching.append((i, match))
        
        # Create action buttons
        keyboard = []
        
        # Add buttons for items that need matching (max 2 per row)
        for i, (index, match) in enumerate(items_needing_matching):
            # Check if this item was manually changed
            is_changed = index in changed_indices
            if is_changed:
                status_emoji = "✏️"
            else:
                status_emoji = self.ingredient_formatter._get_status_emoji(match.match_status)
            button_text = f"{status_emoji} {self.ingredient_formatter._truncate_name(match.receipt_item_name, 15)}"
            
            if i % 2 == 0:
                # Start new row
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_item_{index}")])
            else:
                # Add to existing row
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_item_{index}"))
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Выбрать позицию для сопоставления", callback_data="select_position_for_matching")],
            [InlineKeyboardButton("✅ Применить", callback_data="apply_matching_changes")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await self.ui_manager.send_menu(
                update, context, results_text, reply_markup, 'Markdown'
            )
    
    async def _show_position_selection_interface(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show position selection interface with the same table as before"""
        # First check if we have data in context
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        
        if not matching_result:
            # Try to load from persistent storage
            user_id = update.effective_user.id
            receipt_data = context.user_data.get('receipt_data')
            
            if receipt_data:
                receipt_hash = receipt_data.get_receipt_hash()
                saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
                if saved_data:
                    matching_result, changed_indices = saved_data
                    # Update context with loaded data
                    context.user_data['ingredient_matching_result'] = matching_result
                    context.user_data['changed_ingredient_indices'] = changed_indices
                    # Reset current match index when loading from storage
                    context.user_data['current_match_index'] = 0
        
        if not matching_result:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return
        
        # Show the same table as before
        # Format results
        print(f"DEBUG: Formatting table with changed_indices: {changed_indices}")
        results_text = self.ingredient_formatter.format_matching_table(matching_result, changed_indices)
        
        # Add instruction text
        results_text += "\n\n**Введите номер строки элемента для сопоставления:**"
        
        # Set position selection mode flag
        context.user_data['in_position_selection_mode'] = True
        
        # Create action buttons
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_matching_overview")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await self.ui_manager.send_menu(
                update, context, results_text, reply_markup, 'Markdown'
            )
    
    async def _handle_item_selection_for_matching(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int):
        """Handle selection of specific item for manual matching"""
        # First check if we have data in context
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        
        if not matching_result:
            # Try to load from persistent storage
            user_id = update.effective_user.id
            receipt_data = context.user_data.get('receipt_data')
            
            if receipt_data:
                receipt_hash = receipt_data.get_receipt_hash()
                saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
                if saved_data:
                    matching_result, changed_indices = saved_data
                    # Update context with loaded data
                    context.user_data['ingredient_matching_result'] = matching_result
                    context.user_data['changed_ingredient_indices'] = changed_indices
                    # Reset current match index when loading from storage
                    context.user_data['current_match_index'] = 0
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or item_index >= len(matching_result.matches):
            await update.callback_query.answer("Ошибка: элемент не найден")
            return
        
        current_match = matching_result.matches[item_index]
        
        # Show current match info
        progress_text = f"**Сопоставление ингредиента**\n\n"
        progress_text += f"**Товар:** {current_match.receipt_item_name}\n\n"
        
        # Get filtered suggestions (score >= 50%)
        filtered_suggestions = self.ingredient_formatter.format_suggestions_for_manual_matching(current_match, min_score=0.5)
        
        if filtered_suggestions:
            progress_text += "**Выберите подходящий ингредиент:**\n"
            
            # Create horizontal buttons for suggestions (max 2 per row)
            keyboard = []
            for i, suggestion in enumerate(filtered_suggestions[:6], 1):  # Show up to 6 suggestions
                name = self.ingredient_formatter._truncate_name(suggestion['name'], 15)
                score = int(suggestion['score'] * 100)
                button_text = f"{name} ({score}%)"
                
                if i % 2 == 1:
                    # Start new row
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_ingredient_{i}")])
                else:
                    # Add to existing row
                    keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_ingredient_{i}"))
            
            # Add control buttons
            keyboard.extend([
                [InlineKeyboardButton("🔍 Поиск", callback_data="search_ingredient")],
                [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_ingredient")],
                [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_matching_overview")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
            ])
        else:
            progress_text += "❌ **Подходящих вариантов не найдено**\n\n"
            progress_text += "Попробуйте поиск или пропустите этот товар."
            
            keyboard = [
                [InlineKeyboardButton("🔍 Поиск", callback_data="search_ingredient")],
                [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_ingredient")],
                [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_matching_overview")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Save current item index for later processing
        context.user_data['current_match_index'] = item_index
        
        await self.ui_manager.send_menu(
            update, context, progress_text, reply_markup, 'Markdown'
        )
    
    async def _handle_position_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, position_number: int):
        """Handle position selection from search results"""
        # First check if we have data in context
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        
        if not matching_result:
            # Try to load from persistent storage
            user_id = update.effective_user.id
            receipt_data = context.user_data.get('receipt_data')
            
            if receipt_data:
                receipt_hash = receipt_data.get_receipt_hash()
                saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
                if saved_data:
                    matching_result, changed_indices = saved_data
                    # Update context with loaded data
                    context.user_data['ingredient_matching_result'] = matching_result
                    context.user_data['changed_ingredient_indices'] = changed_indices
                    # Reset current match index when loading from storage
                    context.user_data['current_match_index'] = 0
        
        position_search_results = context.user_data.get('position_search_results', [])
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not position_search_results or position_number < 1 or position_number > len(position_search_results):
            await update.callback_query.answer("Ошибка: позиция не найдена")
            return
        
        if not matching_result:
            await update.callback_query.answer("Ошибка: данные сопоставления не найдены")
            return
        
        # Get selected position
        selected_position = position_search_results[position_number - 1]
        
        # Show all items that can be matched with this position
        items_text = f"**Выбранный ингредиент:** {selected_position['name']}\n\n"
        items_text += "**Выберите товар из чека для сопоставления:**\n\n"
        
        # Create horizontal buttons for all items (max 2 per row)
        keyboard = []
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        for i, match in enumerate(matching_result.matches):
            # Check if this item was manually changed
            is_changed = i in changed_indices
            if is_changed:
                status_emoji = "✏️"
            else:
                status_emoji = self.ingredient_formatter._get_status_emoji(match.match_status)
            button_text = f"{status_emoji} {self.ingredient_formatter._truncate_name(match.receipt_item_name, 15)}"
            
            if i % 2 == 0:
                # Start new row
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"match_item_{i}_{selected_position['id']}")])
            else:
                # Add to existing row
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"match_item_{i}_{selected_position['id']}"))
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Выбрать другую позицию", callback_data="select_position_for_matching")],
            [InlineKeyboardButton("📋 Назад к обзору", callback_data="back_to_matching_overview")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(
            update, context, items_text, reply_markup, 'Markdown'
        )
    
    async def _handle_position_match_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, position_number: int):
        """Handle position match selection from search results"""
        position_match_search_results = context.user_data.get('position_match_search_results', [])
        matching_result = context.user_data.get('ingredient_matching_result')
        selected_line_number = context.user_data.get('selected_line_number')
        
        if not position_match_search_results or position_number < 1 or position_number > len(position_match_search_results):
            await update.callback_query.answer("Ошибка: позиция не найдена")
            return
        
        if not matching_result or not selected_line_number or selected_line_number < 1 or selected_line_number > len(matching_result.matches):
            await update.callback_query.answer("Ошибка: данные сопоставления не найдены")
            return
        
        # Get selected position
        selected_position = position_match_search_results[position_number - 1]
        
        # Get the item to match (convert to 0-based index)
        item_index = selected_line_number - 1
        item_to_match = matching_result.matches[item_index]
        
        # Create manual match
        manual_match = self.ingredient_matching_service.manual_match_ingredient(
            item_to_match.receipt_item_name,
            selected_position['id'],
            context.bot_data.get('poster_ingredients', {})
        )
        
        # Update the match in the result
        matching_result.matches[item_index] = manual_match
        context.user_data['ingredient_matching_result'] = matching_result
        
        # Add this index to changed indices for pencil emoji display
        if 'changed_ingredient_indices' not in context.user_data:
            context.user_data['changed_ingredient_indices'] = set()
        context.user_data['changed_ingredient_indices'].add(item_index)
        print(f"DEBUG: Added item_index {item_index} to changed_indices. Current changed_indices: {context.user_data['changed_ingredient_indices']}")
        
        # Save to persistent storage
        user_id = update.effective_user.id
        self._save_ingredient_matching_data(user_id, context)
        
        # Clear search results and selected line number
        context.user_data.pop('position_match_search_results', None)
        context.user_data.pop('selected_line_number', None)
        
        # Show confirmation
        await update.callback_query.answer(f"✅ Сопоставлено: {item_to_match.receipt_item_name} → {manual_match.matched_ingredient_name}")
        
        # Return to main ingredient matching results
        await self._show_ingredient_matching_results(update, context)
    
    async def _handle_item_position_matching(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_index: int, position_id: str):
        """Handle matching of item with selected position"""
        # First check if we have data in context
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        
        if not matching_result:
            # Try to load from persistent storage
            user_id = update.effective_user.id
            receipt_data = context.user_data.get('receipt_data')
            
            if receipt_data:
                receipt_hash = receipt_data.get_receipt_hash()
                saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
                if saved_data:
                    matching_result, changed_indices = saved_data
                    # Update context with loaded data
                    context.user_data['ingredient_matching_result'] = matching_result
                    context.user_data['changed_ingredient_indices'] = changed_indices
                    # Reset current match index when loading from storage
                    context.user_data['current_match_index'] = 0
        
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or item_index >= len(matching_result.matches):
            await update.callback_query.answer("Ошибка: элемент не найден")
            return
        
        if not poster_ingredients:
            await update.callback_query.answer("Ошибка: справочник ингредиентов не загружен")
            return
        
        # Get the item to match
        item_to_match = matching_result.matches[item_index]
        
        # Create manual match
        manual_match = self.ingredient_matching_service.manual_match_ingredient(
            item_to_match.receipt_item_name,
            position_id,
            poster_ingredients
        )
        
        # Update the match in the result
        matching_result.matches[item_index] = manual_match
        context.user_data['ingredient_matching_result'] = matching_result
        
        # Add this index to changed indices for pencil emoji display
        if 'changed_ingredient_indices' not in context.user_data:
            context.user_data['changed_ingredient_indices'] = set()
        context.user_data['changed_ingredient_indices'].add(item_index)
        print(f"DEBUG: Added item_index {item_index} to changed_indices. Current changed_indices: {context.user_data['changed_ingredient_indices']}")
        
        # Save to persistent storage
        user_id = update.effective_user.id
        self._save_ingredient_matching_data(user_id, context)
        
        # Clear search results
        context.user_data.pop('position_search_results', None)
        
        # Show confirmation
        await update.callback_query.answer(f"✅ Сопоставлено: {item_to_match.receipt_item_name} → {manual_match.matched_ingredient_name}")
        
        # Return to main ingredient matching results
        await self._show_ingredient_matching_results(update, context)
    
    async def _cleanup_previous_menus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clean up previous menu messages to avoid clutter"""
        try:
            # Get the current message ID
            current_message_id = None
            if hasattr(update, 'callback_query') and update.callback_query:
                current_message_id = update.callback_query.message.message_id
            elif hasattr(update, 'message') and update.message:
                current_message_id = update.message.message_id
            
            if not current_message_id:
                return
            
            # Get chat ID
            chat_id = None
            if hasattr(update, 'callback_query') and update.callback_query:
                chat_id = update.callback_query.message.chat_id
            elif hasattr(update, 'message') and update.message:
                chat_id = update.message.chat_id
            
            if not chat_id:
                return
            
            # Get stored menu message IDs to delete
            menu_message_ids = context.user_data.get('menu_message_ids', [])
            
            # Delete previous menu messages (but not the current one)
            for message_id in menu_message_ids:
                if message_id != current_message_id:
                    try:
                        await context.bot.delete_message(
                            chat_id=chat_id,
                            message_id=message_id
                        )
                    except Exception as e:
                        print(f"Не удалось удалить сообщение меню {message_id}: {e}")
            
            # Clear the stored message IDs
            context.user_data['menu_message_ids'] = []
            
        except Exception as e:
            print(f"Ошибка при очистке меню: {e}")
    
    async def _show_manual_matching_for_current_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show manual matching interface for current item"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return
        
        current_match = matching_result.matches[current_match_index]
        
        # Show current match info
        progress_text = f"**Сопоставление ингредиентов** ({current_match_index + 1}/{len(matching_result.matches)})\n\n"
        progress_text += f"**Текущий товар:** {current_match.receipt_item_name}\n\n"
        
        if current_match.match_status.value == "exact":
            # Already matched, show confirmation
            progress_text += f"✅ **Автоматически сопоставлено:** {current_match.matched_ingredient_name}\n\n"
            progress_text += "Нажмите кнопку 'Продолжить' для перехода к следующему товару."
            
            keyboard = [
                [InlineKeyboardButton("➡️ Продолжить", callback_data="next_ingredient_match")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
            ]
        else:
            # Get filtered suggestions (score >= 50%)
            filtered_suggestions = self.ingredient_formatter.format_suggestions_for_manual_matching(current_match, min_score=0.5)
            
            if filtered_suggestions:
                progress_text += "**Выберите подходящий ингредиент:**\n"
                
                # Create buttons for suggestions (max 4 buttons)
                keyboard = []
                for i, suggestion in enumerate(filtered_suggestions[:4], 1):
                    name = self.ingredient_formatter._truncate_name(suggestion['name'], 20)
                    score = int(suggestion['score'] * 100)
                    button_text = f"{name} ({score}%)"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_ingredient_{i}")])
                
                # Add control buttons
                keyboard.append([InlineKeyboardButton("🔍 Поиск", callback_data="search_ingredient")])
                keyboard.append([InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_ingredient")])
                keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")])
            else:
                progress_text += "❌ **Подходящих вариантов не найдено**\n\n"
                progress_text += "Попробуйте поиск или пропустите этот товар."
                
                keyboard = [
                    [InlineKeyboardButton("🔍 Поиск", callback_data="search_ingredient")],
                    [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_ingredient")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
                ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                progress_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def _show_final_ingredient_matching_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final ingredient matching result"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return
        
        # Format final result
        final_text = self.ingredient_formatter.format_matching_table(matching_result)
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                final_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def _handle_ingredient_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, suggestion_number: int):
        """Handle ingredient selection from suggestions"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return
        
        current_match = matching_result.matches[current_match_index]
        
        # Get filtered suggestions
        filtered_suggestions = self.ingredient_formatter.format_suggestions_for_manual_matching(current_match, min_score=0.5)
        
        if suggestion_number < 1 or suggestion_number > len(filtered_suggestions):
            await update.callback_query.answer("Неверный номер предложения")
            return
        
        # Get selected suggestion
        selected_suggestion = filtered_suggestions[suggestion_number - 1]
        
        # Create manual match
        manual_match = self.ingredient_matching_service.manual_match_ingredient(
            current_match.receipt_item_name,
            selected_suggestion['id'],
            poster_ingredients
        )
        
        # Update the match in the result
        matching_result.matches[current_match_index] = manual_match
        context.user_data['ingredient_matching_result'] = matching_result
        
        # Add this index to changed indices for pencil emoji display
        if 'changed_ingredient_indices' not in context.user_data:
            context.user_data['changed_ingredient_indices'] = set()
        context.user_data['changed_ingredient_indices'].add(current_match_index)
        
        # Save to persistent storage
        user_id = update.effective_user.id
        self._save_ingredient_matching_data(user_id, context)
        
        # Show confirmation and immediately return to main ingredient matching results
        await update.callback_query.answer(f"✅ Сопоставлено: {current_match.receipt_item_name} → {selected_suggestion['name']}")
        
        # Delete current message and show updated main results
        try:
            await context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id
            )
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
        
        # Return to main ingredient matching results (not manual overview)
        await self._show_ingredient_matching_results(update, context)
    
    async def _process_next_ingredient_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process next ingredient match or finish matching"""
        # Return to matching overview instead of sequential processing
        await self._show_manual_matching_overview(update, context)
    
    async def _handle_search_result_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, suggestion_number: int):
        """Handle search result selection"""
        current_match_index = context.user_data.get('current_match_index', 0)
        matching_result = context.user_data.get('ingredient_matching_result')
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        search_results = context.user_data.get('search_results', [])
        
        if not matching_result or current_match_index >= len(matching_result.matches):
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text("Ошибка: данные сопоставления не найдены.")
            return
        
        if suggestion_number < 1 or suggestion_number > len(search_results):
            await update.callback_query.answer("Неверный номер предложения")
            return
        
        # Get selected search result
        selected_result = search_results[suggestion_number - 1]
        
        # Create manual match
        manual_match = self.ingredient_matching_service.manual_match_ingredient(
            matching_result.matches[current_match_index].receipt_item_name,
            selected_result['id'],
            poster_ingredients
        )
        
        # Update the match in the result
        matching_result.matches[current_match_index] = manual_match
        context.user_data['ingredient_matching_result'] = matching_result
        
        # Add this index to changed indices for pencil emoji display
        if 'changed_ingredient_indices' not in context.user_data:
            context.user_data['changed_ingredient_indices'] = set()
        context.user_data['changed_ingredient_indices'].add(current_match_index)
        
        # Save to persistent storage
        user_id = update.effective_user.id
        self._save_ingredient_matching_data(user_id, context)
        
        # Clear search results
        context.user_data.pop('search_results', None)
        
        # Show confirmation
        await update.callback_query.answer(f"✅ Сопоставлено: {selected_result['name']}")
        
        # Return to main ingredient matching results
        await self._show_ingredient_matching_results(update, context)
    
    async def _show_back_confirmation_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show confirmation dialog for going back without saving changes"""
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        
        text = f"⚠️ **Внимание!**\n\n"
        text += f"У вас есть несохраненные изменения в сопоставлении ингредиентов.\n"
        text += f"Количество измененных элементов: **{len(changed_indices)}**\n\n"
        text += "Вернуться назад без сохранения изменений?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Да", callback_data="confirm_back_without_changes")],
            [InlineKeyboardButton("❌ Нет", callback_data="cancel_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await self.ui_manager.send_menu(
                update, context, text, reply_markup, 'Markdown'
            )
