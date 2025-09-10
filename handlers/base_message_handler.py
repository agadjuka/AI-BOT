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
    
    def get_text(self, key: str, context=None, language=None, **kwargs) -> str:
        """
        Получает переведенный текст по ключу.
        
        Args:
            key: Ключ для поиска перевода
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context)
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст с интерполяцией переменных
        """
        return self.locale_manager.get_text(key, context, language, **kwargs)
    
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
