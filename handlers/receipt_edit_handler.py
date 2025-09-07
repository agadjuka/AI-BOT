"""
Receipt editing callback handlers
"""
import json
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from models.receipt import ReceiptData, ReceiptItem
from services.ai_service import ReceiptAnalysisService
from utils.formatters import ReceiptFormatter, NumberFormatter, TextParser
from utils.receipt_processor import ReceiptProcessor
from utils.ui_manager import UIManager
from validators.receipt_validator import ReceiptValidator


class ReceiptEditHandler:
    """Handler for receipt editing operations"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.formatter = ReceiptFormatter()
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
        self.processor = ReceiptProcessor()
        self.validator = ReceiptValidator()
        self.ui_manager = UIManager(config)
    
    async def handle_correction_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle correction choice actions"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        if action == "add_row":
            await self._add_new_row(update, context)
            return self.config.AWAITING_FIELD_EDIT
        
        elif action == "delete_row":
            await self.ui_manager.send_temp(
                update, context,
                "Введите номер строки для удаления:\n\n"
                "Например: `3` (для удаления строки 3)",
                duration=30
            )
            return self.config.AWAITING_DELETE_LINE_NUMBER
        
        elif action == "edit_total":
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            await self._show_total_edit_menu(update, context)
            return self.config.AWAITING_CORRECTION
        
        elif action == "edit_line_number":
            await self.ui_manager.send_temp(
                update, context,
                "Введите номер строки для редактирования:\n\n"
                "Например: `3` (для редактирования строки 3)",
                duration=30
            )
            return self.config.AWAITING_LINE_NUMBER
        
        elif action == "reanalyze":
            await query.answer("🔄 Анализирую фото заново...")
            
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            self._clear_receipt_data(context)
            
            try:
                analysis_data = self.analysis_service.analyze_receipt(self.config.PHOTO_FILE_NAME)
                receipt_data = ReceiptData.from_dict(analysis_data)
                
                is_valid, message = self.validator.validate_receipt_data(receipt_data)
                if not is_valid:
                    print(f"Предупреждение валидации: {message}")
                
                context.user_data['receipt_data'] = receipt_data
                context.user_data['original_data'] = ReceiptData.from_dict(receipt_data.to_dict())
                
                await self._show_final_report_with_edit_button_callback(update, context)
                return self.config.AWAITING_CORRECTION
                
            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
                print(f"Ошибка парсинга JSON или структуры данных от Gemini: {e}")
                await query.message.reply_text("Не удалось распознать структуру чека. Попробуйте сделать фото более четким.")
                return self.config.AWAITING_CORRECTION
        
        elif action == "auto_calculate_total":
            await self._auto_calculate_total(update, context)
            return self.config.AWAITING_CORRECTION
        
        elif action == "manual_edit_total":
            current_total = context.user_data.get('receipt_data', {}).grand_total_text
            formatted_total = self.number_formatter.format_number_with_spaces(
                self.text_parser.parse_number_from_text(current_total)
            )
            
            await self.ui_manager.send_temp(
                update, context,
                f"Текущая итоговая сумма: **{formatted_total}**\n\n"
                "Введите новую итоговую сумму:",
                duration=30
            )
            return self.config.AWAITING_TOTAL_EDIT
        
        return self.config.AWAITING_CORRECTION
    
    async def _add_new_row(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Add new row to receipt"""
        data: ReceiptData = context.user_data.get('receipt_data')
        if not data:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные чека не найдены.", duration=5
            )
            return
        
        # Get next line number
        next_line_number = data.get_max_line_number() + 1
        
        # Create new item
        new_item = ReceiptItem(
            line_number=next_line_number,
            name="Новый товар",
            quantity=None,
            price=None,
            total=None,
            status="needs_review"
        )
        
        # Add to data
        data.add_item(new_item)
        
        # Update original_data
        if context.user_data.get('original_data'):
            context.user_data['original_data'].add_item(new_item)
        
        # Show edit menu for new item
        context.user_data['line_to_edit'] = next_line_number
        await self._send_edit_menu(update, context)
    
    async def _show_total_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show total edit menu"""
        data: ReceiptData = context.user_data.get('receipt_data')
        if not data:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные чека не найдены.", duration=5
            )
            return
        
        # Calculate current total
        calculated_total = self.formatter.calculate_total_sum(data)
        receipt_total = self.text_parser.parse_number_from_text(data.grand_total_text)
        
        # Format totals
        formatted_calculated = self.number_formatter.format_number_with_spaces(calculated_total)
        formatted_receipt = self.number_formatter.format_number_with_spaces(receipt_total)
        
        # Check if totals match
        is_match = abs(calculated_total - receipt_total) < 0.01
        
        text = f"**Редактирование итоговой суммы:**\n\n"
        text += f"📊 **Рассчитанная сумма:** {formatted_calculated}\n"
        text += f"📄 **Сумма из чека:** {formatted_receipt}\n\n"
        
        if is_match:
            text += "✅ **Суммы совпадают!**\n\n"
        else:
            difference = abs(calculated_total - receipt_total)
            formatted_difference = self.number_formatter.format_number_with_spaces(difference)
            text += f"❗ **Разница:** {formatted_difference}\n\n"
        
        text += "Выберите действие:"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Пересчитать автоматически", callback_data="auto_calculate_total")],
            [InlineKeyboardButton("✏️ Ввести вручную", callback_data="manual_edit_total")],
            [InlineKeyboardButton("◀️ Назад к чеку", callback_data="back_to_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await self.ui_manager.send_menu(
            update, context, text, reply_markup, 'Markdown'
        )
        context.user_data['total_edit_menu_message_id'] = message.message_id
    
    async def _auto_calculate_total(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Automatically calculate total"""
        data: ReceiptData = context.user_data.get('receipt_data')
        if not data:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные чека не найдены.", duration=5
            )
            return
        
        # Calculate total from all items
        calculated_total = self.formatter.calculate_total_sum(data)
        
        # Update total in data
        data.grand_total_text = str(int(calculated_total)) if calculated_total == int(calculated_total) else str(calculated_total)
        
        # Update original_data
        if context.user_data.get('original_data'):
            context.user_data['original_data'].grand_total_text = data.grand_total_text
        
        # Show success message
        formatted_total = self.number_formatter.format_number_with_spaces(calculated_total)
        await self.ui_manager.send_temp(
            update, context, f"✅ Итоговая сумма пересчитана: **{formatted_total}**", duration=2
        )
        
        # Return to report
        await self._show_final_report_with_edit_button_callback(update, context)
    
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
    
    async def _show_final_report_with_edit_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show final report with edit buttons (callback version)"""
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        final_data: ReceiptData = context.user_data.get('receipt_data')
        if not final_data:
            await self.ui_manager.send_temp(
                update, context, "Произошла ошибка, данные не найдены.", duration=5
            )
            return
        
        try:
            # Auto update statuses
            final_data = self.processor.auto_update_all_statuses(final_data)
            context.user_data['receipt_data'] = final_data
            
            # Check for errors
            has_errors = not self.processor.check_all_items_confirmed(final_data)
            
            # Create table
            aligned_table = self.formatter.format_aligned_table(final_data)
            calculated_total = self.formatter.calculate_total_sum(final_data)
            receipt_total = self.text_parser.parse_number_from_text(final_data.grand_total_text)
            
            # Form report
            final_report = ""
            if has_errors:
                final_report += "🔴 **Обнаружены ошибки в данных чека**\n\n"
            
            final_report += f"```\n{aligned_table}\n```\n\n"
            
            if abs(calculated_total - receipt_total) < 0.01:
                final_report += "✅ **Итоговая сумма соответствует!**\n"
            else:
                difference = abs(calculated_total - receipt_total)
                final_report += f"❗ **Несоответствие итоговой суммы! Разница: {self.number_formatter.format_number_with_spaces(difference)}**\n"
            
            # Cache report
            context.user_data['cached_final_report'] = final_report
            
            # Create buttons
            keyboard = []
            
            # Fix buttons for problematic lines
            if has_errors:
                fix_buttons = []
                for item in final_data.items:
                    status = item.status
                    quantity = item.quantity
                    price = item.price
                    total = item.total
                    has_calculation_error = False
                    
                    if quantity is not None and price is not None and total is not None and quantity > 0 and price > 0 and total > 0:
                        expected_total = quantity * price
                        has_calculation_error = abs(expected_total - total) > 0.01
                    
                    item_name = item.name
                    is_unreadable = item_name == "???" or item_name == "**не распознано**"
                    
                    if status != 'confirmed' or has_calculation_error or is_unreadable:
                        fix_buttons.append(InlineKeyboardButton(
                            f"Исправить строку {item.line_number}",
                            callback_data=f"edit_{item.line_number}"
                        ))
                
                # Distribute fix buttons
                if fix_buttons:
                    if len(fix_buttons) <= 3:
                        for button in fix_buttons:
                            keyboard.append([button])
                    elif len(fix_buttons) <= 6:
                        for i in range(0, len(fix_buttons), 2):
                            row = fix_buttons[i:i+2]
                            if len(row) == 1:
                                row.append(InlineKeyboardButton("", callback_data="noop"))
                            keyboard.append(row)
                    else:
                        for i in range(0, len(fix_buttons), 3):
                            row = fix_buttons[i:i+3]
                            while len(row) < 3:
                                row.append(InlineKeyboardButton("", callback_data="noop"))
                            keyboard.append(row)
            
            # Management buttons
            keyboard.append([
                InlineKeyboardButton("➕ Добавить строку", callback_data="add_row"),
                InlineKeyboardButton("➖ Удалить строку", callback_data="delete_row")
            ])
            keyboard.append([InlineKeyboardButton("🔢 Редактировать строку по номеру", callback_data="edit_line_number")])
            keyboard.append([
                InlineKeyboardButton("💰 Редактировать Итого", callback_data="edit_total"),
                InlineKeyboardButton("🔄 Проанализировать заново", callback_data="reanalyze")
            ])
            # Add Google Sheets upload button
            keyboard.append([InlineKeyboardButton("📊 Загрузить в Google Таблицы", callback_data="upload_to_google_sheets")])
            
            keyboard.append([InlineKeyboardButton("📄 Получить файл для загрузки в постер", callback_data="generate_supply_file")])
            keyboard.append([InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
            context.user_data['table_message_id'] = message.message_id
        
        except Exception as e:
            print(f"Ошибка при формировании отчета: {e}")
            await self.ui_manager.send_temp(
                update, context, f"Произошла ошибка при формировании отчета: {e}", duration=5
            )
    
    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all receipt-related data from context"""
        keys_to_clear = [
            'receipt_data', 'original_data', 'line_to_edit', 'field_to_edit',
            'cached_final_report', 'table_message_id', 'edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id', 'ingredient_matching_result', 'current_match_index',
            'processing_message_id', 'changed_ingredient_indices', 'search_results',
            'position_search_results', 'awaiting_search', 'awaiting_position_search',
            'in_position_selection_mode', 'selected_line_number', 'position_match_search_results',
            'awaiting_ingredient_name_for_position'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
