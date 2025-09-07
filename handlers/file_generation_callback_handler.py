"""
File generation callback handler for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import IngredientMatchingResult
from services.file_generator_service import FileGeneratorService


class FileGenerationCallbackHandler(BaseCallbackHandler):
    """Handler for file generation callbacks"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.file_generator = FileGeneratorService()
    
    async def _generate_and_send_supply_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                           file_type: str = "poster"):
        """Generate and send supply file"""
        query = update.callback_query
        await query.answer()
        
        receipt_data = context.user_data.get('receipt_data')
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not receipt_data:
            await query.edit_message_text("❌ Данные чека не найдены")
            return
        
        if not matching_result:
            await query.edit_message_text("❌ Результаты сопоставления не найдены")
            return
        
        try:
            # Show generating message
            await query.edit_message_text("📄 Генерируем файл...")
            
            if file_type == "poster":
                # Generate poster file
                file_content = self.file_generator.generate_poster_file(receipt_data, matching_result)
                filename = f"poster_supply_{receipt_data.timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
            else:
                # Generate Google Sheets file
                file_content = self.file_generator.generate_google_sheets_file(receipt_data, matching_result)
                filename = f"google_sheets_supply_{receipt_data.timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
            
            # Send file
            from io import StringIO
            file_obj = StringIO(file_content)
            
            await query.message.reply_document(
                document=file_obj,
                filename=filename,
                caption=f"📄 Файл для загрузки в {file_type} готов!"
            )
            
            # Show success message
            success_text = f"✅ **Файл {file_type} успешно сгенерирован!**\n\n"
            success_text += f"📁 **Имя файла:** {filename}\n"
            success_text += f"📊 **Позиций:** {len(matching_result.matches)}\n"
            success_text += f"📅 **Дата:** {receipt_data.timestamp.strftime('%d.%m.%Y %H:%M')}"
            
            keyboard = [
                [InlineKeyboardButton("📊 Показать таблицу", callback_data="show_matching_table")],
                [InlineKeyboardButton("◀️ Назад к редактированию", callback_data="back_to_edit")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            print(f"DEBUG: Error generating {file_type} file: {e}")
            await query.edit_message_text(f"❌ Ошибка при генерации файла: {str(e)}")
    
    async def _show_matching_table_with_edit_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                  matching_result: IngredientMatchingResult):
        """Show matching table with edit button"""
        query = update.callback_query
        await query.answer()
        
        # Format matching table
        table_text = self._format_matching_table(matching_result)
        
        keyboard = [
            [InlineKeyboardButton("📄 Скачать файл для постера", callback_data="generate_poster_file")],
            [InlineKeyboardButton("📊 Скачать файл для Google Sheets", callback_data="generate_google_sheets_file")],
            [InlineKeyboardButton("◀️ Назад к редактированию", callback_data="back_to_edit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_long_message_with_keyboard_callback(query.message, table_text, reply_markup)
    
    def _format_matching_table(self, matching_result: IngredientMatchingResult) -> str:
        """Format matching table for display"""
        table_text = "📊 **Таблица сопоставления ингредиентов:**\n\n"
        
        # Create table header
        table_text += "| № | Товар из чека | Ингредиент | Статус | Сходство |\n"
        table_text += "|---|---|---|---|---|\n"
        
        # Add table rows
        for i, match in enumerate(matching_result.matches):
            status_emoji = self._get_status_emoji(match.match_status)
            ingredient_name = self._truncate_name(match.matched_ingredient_name or 'Не сопоставлено', 20)
            item_name = self._truncate_name(match.receipt_item_name, 25)
            
            table_text += f"| {i+1} | {item_name} | {ingredient_name} | {status_emoji} | {match.similarity_score:.2f} |\n"
        
        table_text += "\n💡 **Легенда:**\n"
        table_text += "✅ - Сопоставлено\n"
        table_text += "⚠️ - Частично сопоставлено\n"
        table_text += "❌ - Не сопоставлено\n"
        
        return table_text
    
    def _get_status_emoji(self, status) -> str:
        """Get emoji for status"""
        from models.ingredient_matching import MatchStatus
        
        if status == MatchStatus.MATCHED:
            return "✅"
        elif status == MatchStatus.PARTIAL_MATCH:
            return "⚠️"
        else:
            return "❌"
