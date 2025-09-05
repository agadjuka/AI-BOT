"""
Ingredient matching callback handlers
"""
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from models.receipt import ReceiptData
from models.ingredient_matching import IngredientMatchingResult
from services.ai_service import ReceiptAnalysisService
from services.ingredient_matching_service import IngredientMatchingService
from utils.ingredient_formatter import IngredientFormatter
from utils.ingredient_storage import IngredientStorage
from utils.ui_manager import UIManager


class IngredientMatchingHandler:
    """Handler for ingredient matching operations"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.ingredient_matching_service = IngredientMatchingService()
        self.ingredient_formatter = IngredientFormatter()
        self.ingredient_storage = IngredientStorage()
        self.ui_manager = UIManager(config)
    
    async def handle_correction_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle correction choice actions"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        if action == "match_ingredients":
            await query.answer("🔍 Загружаю таблицу сопоставления ингредиентов...")
            
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            receipt_data = context.user_data.get('receipt_data')
            if not receipt_data:
                await query.message.reply_text("Ошибка: данные чека не найдены.")
                return self.config.AWAITING_CORRECTION
            
            if not await self._ensure_poster_ingredients_loaded(context):
                await query.message.reply_text("❌ Ошибка: не удалось загрузить справочник ингредиентов из Poster.\nПроверьте подключение к интернету и попробуйте снова.")
                return self.config.AWAITING_CORRECTION
            
            poster_ingredients = context.bot_data.get('poster_ingredients', {})
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            
            # Try to load from storage first
            saved_data = self.ingredient_storage.load_matching_result(user_id, receipt_hash)
            
            if saved_data:
                matching_result, changed_indices = saved_data
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = changed_indices
                context.user_data['current_match_index'] = 0
            else:
                matching_result = self.ingredient_matching_service.match_ingredients(receipt_data, poster_ingredients)
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['current_match_index'] = 0
                context.user_data['changed_ingredient_indices'] = set()
                self._save_ingredient_matching_data(user_id, context)
            
            await self._show_ingredient_matching_results(update, context)
            return self.config.AWAITING_INGREDIENT_MATCHING
        
        elif action == "manual_match_ingredients":
            await query.answer("✋ Начинаю ручное сопоставление...")
            
            matching_result = context.user_data.get('ingredient_matching_result')
            if not matching_result:
                await query.message.reply_text("Ошибка: результаты сопоставления не найдены.")
                return self.config.AWAITING_CORRECTION
            
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            await self._show_manual_matching_overview(update, context)
            return self.config.AWAITING_MANUAL_MATCH
        
        elif action == "rematch_ingredients":
            await query.answer("🔄 Перезапускаю сопоставление...")
            
            receipt_data = context.user_data.get('receipt_data')
            if not receipt_data:
                await query.message.reply_text("Ошибка: данные чека не найдены.")
                return self.config.AWAITING_CORRECTION
            
            if not await self._ensure_poster_ingredients_loaded(context):
                await query.message.reply_text("❌ Ошибка: не удалось загрузить справочник ингредиентов из Poster.\nПроверьте подключение к интернету и попробуйте снова.")
                return self.config.AWAITING_CORRECTION
            
            poster_ingredients = context.bot_data.get('poster_ingredients', {})
            await self.ui_manager.cleanup_all_except_anchor(update, context)
            
            # Perform matching again
            matching_result = self.ingredient_matching_service.match_ingredients(receipt_data, poster_ingredients)
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['current_match_index'] = 0
            context.user_data['changed_ingredient_indices'] = set()
            
            user_id = update.effective_user.id
            self._save_ingredient_matching_data(user_id, context)
            
            # Clear from context so it will be loaded from storage next time
            context.user_data.pop('ingredient_matching_result', None)
            context.user_data.pop('changed_ingredient_indices', None)
            context.user_data.pop('current_match_index', None)
            
            await self._show_ingredient_matching_results(update, context)
            return self.config.AWAITING_INGREDIENT_MATCHING
        
        elif action == "upload_to_google_sheets":
            await query.answer("📊 Загружаю данные в Google Таблицы...")
            
            receipt_data = context.user_data.get('receipt_data')
            matching_result = context.user_data.get('ingredient_matching_result')
            
            if not receipt_data or not matching_result:
                await query.message.reply_text("Ошибка: данные чека или сопоставления не найдены.")
                return self.config.AWAITING_CORRECTION
            
            # Import here to avoid circular imports
            from services.google_sheets_service import GoogleSheetsService
            
            google_sheets_service = GoogleSheetsService(
                credentials_path=self.config.GOOGLE_SHEETS_CREDENTIALS,
                spreadsheet_id=self.config.GOOGLE_SHEETS_SPREADSHEET_ID
            )
            
            if not google_sheets_service.is_available():
                await query.message.reply_text("❌ Google Sheets сервис недоступен. Проверьте настройки.")
                return self.config.AWAITING_CORRECTION
            
            success, message = google_sheets_service.upload_receipt_data(
                receipt_data, matching_result, self.config.GOOGLE_SHEETS_WORKSHEET_NAME
            )
            
            if success:
                await query.message.reply_text(f"✅ {message}")
            else:
                await query.message.reply_text(f"❌ {message}")
            
            return self.config.AWAITING_CORRECTION
        
        elif action == "generate_supply_file":
            await query.answer("📄 Генерирую файл для загрузки в постер...")
            
            receipt_data = context.user_data.get('receipt_data')
            matching_result = context.user_data.get('ingredient_matching_result')
            
            if not receipt_data or not matching_result:
                await query.message.reply_text("Ошибка: данные чека или сопоставления не найдены.")
                return self.config.AWAITING_CORRECTION
            
            # Import here to avoid circular imports
            from services.file_generator_service import FileGeneratorService
            
            file_generator = FileGeneratorService()
            
            # Validate data
            is_valid, error_message = file_generator.validate_data(receipt_data, matching_result)
            if not is_valid:
                await query.message.reply_text(f"❌ {error_message}")
                return self.config.AWAITING_CORRECTION
            
            try:
                # Generate file
                file_content = file_generator.generate_supply_file(
                    receipt_data, matching_result, 'xlsx'
                )
                
                # Send file
                from telegram import InputFile
                import io
                
                file_buffer = io.BytesIO(file_content)
                file_buffer.name = f"supply_receipt_{receipt_data.get_receipt_hash()}.xlsx"
                
                await query.message.reply_document(
                    document=InputFile(file_buffer),
                    caption="📄 Файл для загрузки в постер готов!"
                )
                
            except Exception as e:
                print(f"Ошибка при генерации файла: {e}")
                await query.message.reply_text(f"❌ Ошибка при генерации файла: {e}")
            
            return self.config.AWAITING_CORRECTION
        
        return self.config.AWAITING_CORRECTION
    
    async def _ensure_poster_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Ensure poster ingredients are loaded"""
        poster_ingredients = context.bot_data.get('poster_ingredients', {})
        
        if not poster_ingredients:
            from poster_handler import get_all_poster_ingredients
            poster_ingredients = get_all_poster_ingredients()
            
            if not poster_ingredients:
                return False
            
            context.bot_data["poster_ingredients"] = poster_ingredients
            print(f"DEBUG: Loaded {len(poster_ingredients)} poster ingredients")
        
        return True
    
    async def _show_ingredient_matching_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show ingredient matching results"""
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        # Format results
        result_text = self.ingredient_formatter.format_matching_table(matching_result, changed_indices)
        
        # Create buttons
        keyboard = [
            [InlineKeyboardButton("✏️ Ручное сопоставление", callback_data="manual_match_ingredients")],
            [InlineKeyboardButton("🔄 Сопоставить заново", callback_data="rematch_ingredients")],
            [InlineKeyboardButton("📊 Загрузить в Google Таблицы", callback_data="upload_to_google_sheets")],
            [InlineKeyboardButton("📄 Получить файл для постер", callback_data="generate_supply_file")],
            [InlineKeyboardButton("◀️ Вернуться к чеку", callback_data="back_to_receipt")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(update, context, result_text, reply_markup, 'Markdown')
    
    async def _show_manual_matching_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show manual matching overview"""
        matching_result = context.user_data.get('ingredient_matching_result')
        
        if not matching_result:
            await self.ui_manager.send_temp(
                update, context, "Ошибка: данные сопоставления не найдены.", duration=5
            )
            return
        
        # Filter items that need matching (not exact matches)
        items_needing_match = []
        for i, match in enumerate(matching_result.matches):
            if match.match_status.value != 'exact':
                items_needing_match.append((i, match))
        
        if not items_needing_match:
            await self.ui_manager.send_menu(
                update, context,
                "✅ **Все ингредиенты уже сопоставлены!**\n\n"
                "Все товары имеют точные совпадения с ингредиентами Poster.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Вернуться к обзору", callback_data="back_to_receipt")]
                ]),
                'Markdown'
            )
            return
        
        # Create overview text
        overview_text = f"**Ручное сопоставление ингредиентов**\n\n"
        overview_text += f"📊 **Требуют сопоставления:** {len(items_needing_match)} из {len(matching_result.matches)}\n\n"
        overview_text += "**Выберите товар для сопоставления:**\n"
        
        # Create buttons for items needing match (2 per row)
        keyboard = []
        for i, (match_index, match) in enumerate(items_needing_match):
            status_emoji = "🟡" if match.match_status.value == 'partial' else "🔴"
            button_text = f"{status_emoji} {match.receipt_item_name[:15]}"
            
            if i % 2 == 0:
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_item_{match_index}")])
            else:
                keyboard[-1].append(InlineKeyboardButton(button_text, callback_data=f"select_item_{match_index}"))
        
        # Add control buttons
        keyboard.extend([
            [InlineKeyboardButton("🔍 Выбрать позицию для сопоставления", callback_data="select_position_for_matching")],
            [InlineKeyboardButton("◀️ Вернуться к обзору", callback_data="back_to_receipt")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.ui_manager.send_menu(update, context, overview_text, reply_markup, 'Markdown')
    
    def _save_ingredient_matching_data(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Save ingredient matching data to storage"""
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        receipt_data = context.user_data.get('receipt_data')
        
        if matching_result and receipt_data:
            receipt_hash = receipt_data.get_receipt_hash()
            self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, receipt_hash)
