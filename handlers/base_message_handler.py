"""
Base message handler with common dependencies
"""
from config.settings import BotConfig
from config.locales.locale_manager import get_global_locale_manager
from services.ai_service import ReceiptAnalysisService
from services.ingredient_matching_service import IngredientMatchingService
from utils.formatters import ReceiptFormatter, NumberFormatter, TextParser
from utils.ingredient_formatter import IngredientFormatter
from utils.ingredient_storage import IngredientStorage
from utils.receipt_processor import ReceiptProcessor
from utils.ui_manager import UIManager
from utils.language_middleware import save_user_id_to_context
from validators.receipt_validator import ReceiptValidator


class BaseMessageHandler:
    """Base class for message handlers with common dependencies"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisService):
        self.config = config
        self.analysis_service = analysis_service
        self.locale_manager = get_global_locale_manager()
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
    
    def save_user_context(self, update, context):
        """Save user_id to context for language loading"""
        if update and context:
            save_user_id_to_context(update, context)

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
    
    def get_text_auto_update(self, key: str, context=None, language=None, **kwargs) -> str:
        """
        Получает переведенный текст с автоматическим определением update из контекста.
        Используется когда update недоступен напрямую.
        
        Args:
            key: Ключ для поиска перевода
            context: Контекст пользователя (должен содержать update)
            language: Язык (опционально)
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст с интерполяцией переменных
        """
        # Пытаемся получить update из контекста
        update = None
        if context and hasattr(context, 'user_data'):
            update = context.user_data.get('_current_update')
        
        return self.locale_manager.get_text(key, context, language, update, **kwargs)
    
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
