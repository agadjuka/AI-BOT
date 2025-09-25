"""
Base message handler for template bot
Simplified version without complex dependencies
"""
from config.settings import BotConfig
from config.locales.locale_manager import get_global_locale_manager
from services.ai_service import ReceiptAnalysisServiceCompat


class BaseMessageHandler:
    """Base class for message handlers - Template version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        self.config = config
        self.analysis_service = analysis_service
        self.locale_manager = get_global_locale_manager()
    
    def get_text(self, key: str, context=None, language=None, update=None, **kwargs) -> str:
        """
        Get translated text by key with automatic language loading.
        
        Args:
            key: Key for translation lookup
            context: User context (optional)
            language: Language (optional, if not specified, taken from context or Firestore)
            update: Update object for automatic language loading
            **kwargs: Variables for interpolation
            
        Returns:
            str: Translated text with variable interpolation
        """
        return self.locale_manager.get_text(key, context, language, update, **kwargs)
    
    def get_button_text(self, key: str, context=None, language=None, update=None, **kwargs) -> str:
        """
        Get button text by key with automatic language loading.
        
        Args:
            key: Key for translation lookup (usually with 'button_' prefix)
            context: User context (optional)
            language: Language (optional, if not specified, taken from context or Firestore)
            update: Update object for automatic language loading
            **kwargs: Variables for interpolation
            
        Returns:
            str: Translated button text with variable interpolation
        """
        return self.locale_manager.get_text(key, context, language, update, **kwargs)