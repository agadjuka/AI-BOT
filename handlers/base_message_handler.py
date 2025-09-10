"""
Base message handler with common dependencies
"""
from config.settings import BotConfig
from config.locales.locale_manager import LocaleManager
from services.ai_service import ReceiptAnalysisService
from services.ingredient_matching_service import IngredientMatchingService
from utils.formatters import ReceiptFormatter, NumberFormatter, TextParser
from utils.ingredient_formatter import IngredientFormatter
from utils.ingredient_storage import IngredientStorage
from utils.receipt_processor import ReceiptProcessor
from utils.ui_manager import UIManager
from validators.receipt_validator import ReceiptValidator


class BaseMessageHandler:
    """Base class for message handlers with common dependencies"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.locale_manager = LocaleManager()
        self.formatter = ReceiptFormatter()
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
        self.processor = ReceiptProcessor()
        self.validator = ReceiptValidator()
        self.ingredient_matching_service = IngredientMatchingService()
        self.ingredient_formatter = IngredientFormatter()
        self.ingredient_storage = IngredientStorage()
        self.ui_manager = UIManager(config)
    
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

    def get_text(self, key: str, context=None, language=None, update=None, **kwargs) -> str:
        """
        Получает переведенный текст по ключу.
        
        Args:
            key: Ключ для поиска перевода
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context)
            update: Update объект для автоматической загрузки языка
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст с интерполяцией переменных
        """
        # Auto-load language if update is provided
        if update and context:
            self.ensure_language_loaded(update, context)
        
        return self.locale_manager.get_text(key, context, language, update, **kwargs)
    
    def get_text_with_auto_load(self, key: str, update, context, language=None, **kwargs) -> str:
        """
        Получает переведенный текст по ключу с автоматической загрузкой языка.
        
        Args:
            key: Ключ для поиска перевода
            update: Update объект (обязательно)
            context: Контекст пользователя (обязательно)
            language: Язык (опционально)
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст с интерполяцией переменных
        """
        # Always ensure language is loaded
        self.ensure_language_loaded(update, context)
        
        return self.locale_manager.get_text(key, context, language, update, **kwargs)
    
    def get_button_text(self, key: str, context=None, language=None, **kwargs) -> str:
        """
        Получает текст для кнопки по ключу.
        
        Args:
            key: Ключ для поиска перевода (обычно с префиксом 'button_')
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context)
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст кнопки с интерполяцией переменных
        """
        return self.locale_manager.get_text(key, context, language, **kwargs)
    
    def get_emoji(self, key: str, context=None, language=None) -> str:
        """
        Получает эмодзи по ключу.
        
        Args:
            key: Ключ для поиска эмодзи (обычно с префиксом 'emoji_')
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context)
            
        Returns:
            str: Эмодзи или пустая строка если не найдено
        """
        return self.locale_manager.get_text(key, context, language)
