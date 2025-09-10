"""
Base callback handler for Telegram bot
"""
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from config.locales.locale_manager import get_global_locale_manager
from services.ai_service import ReceiptAnalysisServiceCompat
from utils.formatters import ReceiptFormatter, NumberFormatter, TextParser
from utils.ingredient_storage import IngredientStorage
from utils.receipt_processor import ReceiptProcessor
from utils.ui_manager import UIManager
from utils.common_handlers import CommonHandlers
from utils.language_middleware import save_user_id_to_context
from validators.receipt_validator import ReceiptValidator


class BaseCallbackHandler:
    """Base class for callback handlers with common functionality"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        self.config = config
        self.analysis_service = analysis_service
        self.locale_manager = get_global_locale_manager()
        self.formatter = ReceiptFormatter()
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
        self.processor = ReceiptProcessor()
        self.validator = ReceiptValidator()
        self.ingredient_storage = IngredientStorage()
        self.ui_manager = UIManager(config)
        self.common_handlers = CommonHandlers(config, analysis_service)
    
    async def _ensure_poster_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Ensure poster ingredients are loaded, load them if necessary"""
        return await self.common_handlers.ensure_ingredients_loaded(context, "poster")
    
    async def _ensure_google_sheets_ingredients_loaded(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Ensure Google Sheets ingredients are loaded, load them if necessary"""
        return await self.common_handlers.ensure_ingredients_loaded(context, "google_sheets")
    
    def ensure_language_loaded(self, update, context):
        """Ensure user language is loaded from Firestore if not in context"""
        if not context or not hasattr(context, 'user_data'):
            return
        
        # Check if language is already loaded in context
        if context.user_data.get('language'):
            return
        
        # Load language from Firestore
        if update and hasattr(update, 'effective_user'):
            user_id = getattr(update.effective_user, 'id', None)
            if user_id:
                stored_language = self.locale_manager.language_service.get_user_language(user_id)
                if stored_language and self.locale_manager.is_language_supported(stored_language):
                    context.user_data['language'] = stored_language
                    print(f"DEBUG: Auto-loaded language '{stored_language}' for user {user_id}")
    
    def save_user_context(self, update, context):
        """Save user_id to context for language loading"""
        if update and context:
            save_user_id_to_context(update, context)
    
    def get_text_with_auto_load(self, key: str, update, context, language=None, **kwargs) -> str:
        """
        Получает переведенный текст по ключу с автоматической загрузкой языка.
        Теперь это просто алиас для get_text, так как автоматическая загрузка встроена.
        
        Args:
            key: Ключ для поиска перевода
            update: Update объект (обязательно)
            context: Контекст пользователя (обязательно)
            language: Язык (опционально)
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст с интерполяцией переменных
        """
        # get_text теперь автоматически загружает язык из Firestore
        return self.get_text(key, context, language, update, **kwargs)
    
    async def _send_long_message_with_keyboard_callback(self, message, text: str, reply_markup):
        """Send long message with keyboard (for callback query)"""
        await self.common_handlers.send_long_message_with_keyboard(message, text, reply_markup)
    
    def _save_ingredient_matching_data(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Save ingredient matching data to storage"""
        matching_result = context.user_data.get('ingredient_matching_result')
        changed_indices = context.user_data.get('changed_ingredient_indices', set())
        receipt_data = context.user_data.get('receipt_data')
        
        if matching_result and receipt_data:
            receipt_hash = receipt_data.get_receipt_hash()
            self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, receipt_hash)
            print(f"DEBUG: Saved ingredient matching data for user {user_id}, hash: {receipt_hash}")
    
    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear receipt data from context"""
        context.user_data.pop('receipt_data', None)
        context.user_data.pop('ingredient_matching_result', None)
        context.user_data.pop('changed_ingredient_indices', None)
        context.user_data.pop('original_data', None)
        print("DEBUG: Cleared receipt data from context")
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name if too long"""
        return self.common_handlers.truncate_name(name, max_length)
    
    async def _update_ingredient_matching_after_data_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                           receipt_data, change_type: str = "general") -> None:
        """Update ingredient matching after any data change"""
        try:
            # Get current matching result from context or storage
            matching_result = context.user_data.get('ingredient_matching_result')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if not matching_result:
                # Try to load from storage using old hash
                user_id = update.effective_user.id
                old_receipt_data = context.user_data.get('original_data')
                if old_receipt_data:
                    old_receipt_hash = old_receipt_data.get_receipt_hash()
                    saved_data = self.ingredient_storage.load_matching_result(user_id, old_receipt_hash)
                    if saved_data:
                        matching_result, changed_indices = saved_data
                        # Update context with loaded data
                        context.user_data['ingredient_matching_result'] = matching_result
                        context.user_data['changed_ingredient_indices'] = changed_indices
            
            if not matching_result:
                print(f"DEBUG: No matching result found to update after {change_type}")
                return
            
            # For different change types, we need different handling
            if change_type == "deletion":
                # This will be handled by the specific deletion function
                return
            elif change_type == "addition":
                # Add a new empty match for the new item
                from models.ingredient_matching import IngredientMatch, MatchStatus
                new_match = IngredientMatch(
                    receipt_item_name="Новый товар",
                    matched_ingredient_name="",
                    matched_ingredient_id="",
                    match_status=MatchStatus.NO_MATCH,
                    similarity_score=0.0,
                    suggested_matches=[]
                )
                matching_result.matches.append(new_match)
                
            elif change_type == "item_edit":
                # For item edits, we need to regenerate matching for that specific item
                # This is more complex, so for now we'll just mark that matching needs to be redone
                # The user will need to redo ingredient matching if they want accurate results
                print("DEBUG: Item edited - ingredient matching may need to be redone")
                return
                
            # Update context
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['changed_ingredient_indices'] = changed_indices
            
            # Save updated matching result with new receipt hash
            user_id = update.effective_user.id
            new_receipt_hash = receipt_data.get_receipt_hash()
            success = self.ingredient_storage.save_matching_result(user_id, matching_result, changed_indices, new_receipt_hash)
            
            # Clear old matching result file if hash changed
            if context.user_data.get('original_data'):
                old_receipt_hash = context.user_data['original_data'].get_receipt_hash()
                if old_receipt_hash != new_receipt_hash:
                    self.ingredient_storage.clear_matching_result(user_id, old_receipt_hash)
            
            print(f"DEBUG: Updated ingredient matching after {change_type}, new hash: {new_receipt_hash}, success: {success}")
                
        except Exception as e:
            print(f"DEBUG: Error updating ingredient matching after {change_type}: {e}")
    
    async def _update_ingredient_matching_after_deletion(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                       receipt_data, deleted_line_number: int) -> None:
        """Update ingredient matching after line deletion"""
        try:
            # Get current matching result from context or storage
            matching_result = context.user_data.get('ingredient_matching_result')
            changed_indices = context.user_data.get('changed_ingredient_indices', set())
            
            if not matching_result:
                # Try to load from storage using old hash
                user_id = update.effective_user.id
                old_receipt_data = context.user_data.get('original_data')
                if old_receipt_data:
                    old_receipt_hash = old_receipt_data.get_receipt_hash()
                    saved_data = self.ingredient_storage.load_matching_result(user_id, old_receipt_hash)
                    if saved_data:
                        matching_result, changed_indices = saved_data
                        # Update context with loaded data
                        context.user_data['ingredient_matching_result'] = matching_result
                        context.user_data['changed_ingredient_indices'] = changed_indices
            
            if not matching_result:
                print("DEBUG: No matching result found to update after deletion")
                return
            
            # Find the index of the deleted item in the matching result
            # The matching result should have the same order as the original receipt items
            deleted_index = None
            for i, match in enumerate(matching_result.matches):
                # We need to find the match that corresponds to the deleted line
                # Since we don't have direct mapping, we'll use the order
                if i == deleted_line_number - 1:  # Convert line number to 0-based index
                    deleted_index = i
                    break
            
            if deleted_index is not None:
                # Remove the match at the deleted index
                matching_result.matches.pop(deleted_index)
                
                # Update changed indices - remove any indices >= deleted_index and decrement others
                updated_changed_indices = set()
                for idx in changed_indices:
                    if idx < deleted_index:
                        updated_changed_indices.add(idx)
                    elif idx > deleted_index:
                        updated_changed_indices.add(idx - 1)
                # Don't add the deleted index itself
                
                # Update context
                context.user_data['ingredient_matching_result'] = matching_result
                context.user_data['changed_ingredient_indices'] = updated_changed_indices
                
                # Save updated matching result with new receipt hash
                user_id = update.effective_user.id
                new_receipt_hash = receipt_data.get_receipt_hash()
                success = self.ingredient_storage.save_matching_result(user_id, matching_result, updated_changed_indices, new_receipt_hash)
                
                # Clear old matching result file
                if context.user_data.get('original_data'):
                    old_receipt_hash = context.user_data['original_data'].get_receipt_hash()
                    if old_receipt_hash != new_receipt_hash:
                        self.ingredient_storage.clear_matching_result(user_id, old_receipt_hash)
                
                print(f"DEBUG: Updated ingredient matching after deletion, new hash: {new_receipt_hash}, success: {success}")
            else:
                print(f"DEBUG: Could not find matching index for deleted line {deleted_line_number}")
                
        except Exception as e:
            print(f"DEBUG: Error updating ingredient matching after deletion: {e}")
    
    async def _auto_match_ingredient_for_new_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                new_item, receipt_data) -> None:
        """Automatically match ingredient for new item"""
        try:
            # Ensure poster ingredients are loaded
            if not await self._ensure_poster_ingredients_loaded(context):
                print("DEBUG: Could not load poster ingredients for auto-matching")
                return
            
            # Get poster ingredients from bot data
            poster_ingredients = context.bot_data.get('poster_ingredients', {})
            if not poster_ingredients:
                print("DEBUG: No poster ingredients available for auto-matching")
                return
            
            # Create ingredient matching service
            from services.ingredient_matching_service import IngredientMatchingService
            ingredient_matching_service = IngredientMatchingService()
            
            # Match the new item
            matching_result = ingredient_matching_service.match_ingredients(receipt_data, poster_ingredients)
            
            # Find the match for our new item (should be the last one)
            if matching_result.matches:
                new_match = matching_result.matches[-1]  # Last match should be for our new item
                
                # Update the new item's match in the existing matching result
                existing_matching_result = context.user_data.get('ingredient_matching_result')
                if existing_matching_result:
                    # Add the new match to existing result
                    existing_matching_result.matches.append(new_match)
                    
                    # Update context
                    context.user_data['ingredient_matching_result'] = existing_matching_result
                    
                    # Save updated matching result
                    user_id = update.effective_user.id
                    receipt_hash = receipt_data.get_receipt_hash()
                    self.ingredient_storage.save_matching_result(user_id, existing_matching_result, 
                                                               context.user_data.get('changed_ingredient_indices', set()), 
                                                               receipt_hash)
                    
                    print(f"DEBUG: Auto-matched ingredient for new item: {new_item.name} -> {new_match.matched_ingredient_name}")
                else:
                    # No existing matching result, create new one
                    context.user_data['ingredient_matching_result'] = matching_result
                    context.user_data['changed_ingredient_indices'] = set()
                    
                    # Save new matching result
                    user_id = update.effective_user.id
                    receipt_hash = receipt_data.get_receipt_hash()
                    self.ingredient_storage.save_matching_result(user_id, matching_result, set(), receipt_hash)
                    
                    print(f"DEBUG: Created new matching result with auto-matched ingredient for new item")
            
        except Exception as e:
            print(f"DEBUG: Error auto-matching ingredient for new item: {e}")
    
    def get_text(self, key: str, context=None, language=None, update=None, **kwargs) -> str:
        """
        Получает переведенный текст по ключу с автоматической загрузкой языка.
        
        Args:
            key: Ключ для поиска перевода
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context или Firestore)
            update: Update объект для автоматической загрузки языка
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст с интерполяцией переменных
        """
        # LocaleManager теперь автоматически загружает язык из Firestore
        return self.locale_manager.get_text(key, context, language, update, **kwargs)
    
    def get_button_text(self, key: str, context=None, language=None, update=None, **kwargs) -> str:
        """
        Получает текст для кнопки по ключу с автоматической загрузкой языка.
        
        Args:
            key: Ключ для поиска перевода (обычно с префиксом 'button_')
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context или Firestore)
            update: Update объект для автоматической загрузки языка
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст кнопки с интерполяцией переменных
        """
        return self.locale_manager.get_text(key, context, language, update, **kwargs)
    
    def get_emoji(self, key: str, context=None, language=None, update=None) -> str:
        """
        Получает эмодзи по ключу с автоматической загрузкой языка.
        
        Args:
            key: Ключ для поиска эмодзи (обычно с префиксом 'emoji_')
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context или Firestore)
            update: Update объект для автоматической загрузки языка
            
        Returns:
            str: Эмодзи или пустая строка если не найдено
        """
        return self.locale_manager.get_text(key, context, language, update)