"""
File generation dispatcher for Telegram bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from models.ingredient_matching import IngredientMatchingResult
from services.file_generator_service import FileGeneratorService
from utils.common_handlers import CommonHandlers
from config.locales.locale_manager import get_global_locale_manager


class FileGenerationDispatcher(BaseCallbackHandler):
    """Dispatcher for file generation related callbacks"""
    
    def __init__(self, config, analysis_service, google_sheets_handler=None, ingredient_matching_handler=None):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.file_generator = FileGeneratorService()
        self.common_handlers = CommonHandlers(config, analysis_service)
        self.google_sheets_handler = google_sheets_handler
        self.ingredient_matching_handler = ingredient_matching_handler
    
    async def _handle_file_generation_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Handle file generation related actions"""
        if action == "generate_supply_file":
            await self._generate_and_send_supply_file(update, context, "poster")
        elif action == "generate_poster_file":
            await self._generate_and_send_supply_file(update, context, "poster")
        elif action == "generate_google_sheets_file":
            await self._generate_and_send_supply_file(update, context, "google_sheets")
        elif action == "generate_file_xlsx":
            # Generate Excel file from matching result
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                if self.google_sheets_handler:
                    await self.google_sheets_handler._generate_excel_file(update, context)
                else:
                    await update.callback_query.edit_message_text(
                        self.locale_manager.get_text("file_generation.google_sheets_handler_unavailable", context)
                    )
            else:
                await update.callback_query.edit_message_text(
                    self.locale_manager.get_text("file_generation.matching_results_not_found", context)
                )
        elif action == "generate_file_from_table":
            matching_result = context.user_data.get('ingredient_matching_result')
            if matching_result:
                await self._show_matching_table_with_edit_button(update, context, matching_result)
        elif action == "match_ingredients":
            if self.ingredient_matching_handler:
                await self.ingredient_matching_handler._show_ingredient_matching_results(update, context)
            else:
                await update.callback_query.edit_message_text(
                    self.locale_manager.get_text("file_generation.ingredient_matching_handler_unavailable", context)
                )
        
        return self.config.AWAITING_CORRECTION
    
    async def _generate_and_send_supply_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                           file_type: str = "poster"):
        """Generate and send supply file"""
        query = update.callback_query
        await query.answer()
        
        receipt_data = context.user_data.get('receipt_data')
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not receipt_data:
            await query.edit_message_text(
                self.locale_manager.get_text("file_generation.receipt_data_not_found", context)
            )
            return
        
        if not matching_result:
            await query.edit_message_text(
                self.locale_manager.get_text("file_generation.matching_results_not_found", context)
            )
            return
        
        try:
            # Show generating message
            await query.edit_message_text(
                self.locale_manager.get_text("file_generation.generating_file", context)
            )
            
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
                caption=self.locale_manager.get_text("file_generation.file_ready", context, file_type=file_type)
            )
            
            # Show success message
            success_text = self.locale_manager.get_text("file_generation.success_title", context, file_type=file_type) + "\n\n"
            success_text += self.locale_manager.get_text("file_generation.filename", context, filename=filename) + "\n"
            success_text += self.locale_manager.get_text("file_generation.positions_count", context, count=len(matching_result.matches)) + "\n"
            success_text += self.locale_manager.get_text("file_generation.generation_date", context, date=receipt_data.timestamp.strftime('%d.%m.%Y %H:%M'))
            
            keyboard = [
                [InlineKeyboardButton(
                    self.locale_manager.get_text("file_generation.show_table", context), 
                    callback_data="show_matching_table"
                )],
                [InlineKeyboardButton(
                    self.locale_manager.get_text("file_generation.back_to_edit", context), 
                    callback_data="back_to_edit"
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            print(f"DEBUG: Error generating {file_type} file: {e}")
            await query.edit_message_text(
                self.locale_manager.get_text("file_generation.error_generating_file", context, error=str(e))
            )
    
    async def _show_matching_table_with_edit_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                  matching_result: IngredientMatchingResult):
        """Show matching table with edit button"""
        query = update.callback_query
        await query.answer()
        
        # Format matching table
        table_text = await self._format_matching_table(matching_result, context)
        
        keyboard = [
            [InlineKeyboardButton(
                self.locale_manager.get_text("file_generation.download_poster_file", context), 
                callback_data="generate_poster_file"
            )],
            [InlineKeyboardButton(
                self.locale_manager.get_text("file_generation.download_google_sheets_file", context), 
                callback_data="generate_google_sheets_file"
            )],
            [InlineKeyboardButton(
                self.locale_manager.get_text("file_generation.back_to_edit", context), 
                callback_data="back_to_edit"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.common_handlers.send_long_message_with_keyboard(query.message, table_text, reply_markup)
    
    async def _format_matching_table(self, matching_result: IngredientMatchingResult, context) -> str:
        """Format matching table for display"""
        table_text = self.locale_manager.get_text("file_generation.matching_table_title", context) + "\n\n"
        
        # Create table header
        table_text += self.locale_manager.get_text("file_generation.table_header", context) + "\n"
        table_text += self.locale_manager.get_text("file_generation.table_separator", context) + "\n"
        
        # Add table rows
        for i, match in enumerate(matching_result.matches):
            status_emoji = self._get_status_emoji(match.match_status)
            # Для красных маркеров (NO_MATCH) используем название из чека (Gemini recognition)
            # Для зеленых и желтых маркеров используем сопоставленное название
            if match.match_status.value == 'no_match':
                ingredient_name = self.common_handlers.truncate_name(match.receipt_item_name, 20)
            else:
                ingredient_name = self.common_handlers.truncate_name(
                    match.matched_ingredient_name or self.locale_manager.get_text("file_generation.not_matched", context), 
                    20
                )
            item_name = self.common_handlers.truncate_name(match.receipt_item_name, 25)
            
            table_text += f"| {i+1} | {item_name} | {ingredient_name} | {status_emoji} | {match.similarity_score:.2f} |\n"
        
        table_text += "\n" + self.locale_manager.get_text("file_generation.legend_title", context) + "\n"
        table_text += self.locale_manager.get_text("file_generation.legend_matched", context) + "\n"
        table_text += self.locale_manager.get_text("file_generation.legend_partial", context) + "\n"
        table_text += self.locale_manager.get_text("file_generation.legend_not_matched", context) + "\n"
        
        return table_text
    
    def _get_status_emoji(self, status) -> str:
        """Get emoji for status"""
        return self.common_handlers.get_status_emoji(str(status))
