"""
LocaleManager - класс для управления локализацией в AI Bot
"""

import re
from typing import Dict, Any, Optional, Union
from config.locales.ru import RU_TRANSLATIONS
from config.locales.en import EN_TRANSLATIONS
from config.locales.id import ID_TRANSLATIONS
from services.language_service import get_language_service


class LocaleManager:
    """
    Менеджер локализации для AI Bot.
    
    Поддерживает:
    - Получение языка из context.user_data
    - Возврат текстов по ключам
    - Интерполяцию переменных в формате {variable}
    - Fallback на русский язык
    """
    
    # Поддерживаемые языки
    SUPPORTED_LANGUAGES = {
        'ru': RU_TRANSLATIONS,
        'en': EN_TRANSLATIONS,
        'id': ID_TRANSLATIONS,
    }
    
    # Язык по умолчанию
    DEFAULT_LANGUAGE = 'ru'
    
    def __init__(self):
        """Инициализация LocaleManager."""
        if hasattr(self, '_initialized'):
            return
        self._translations = self.SUPPORTED_LANGUAGES
        self._default_lang = self.DEFAULT_LANGUAGE
        self.language_service = get_language_service()
        self._initialized = True
    
    def get_user_language_from_storage(self, user_id: int) -> str:
        """Get user language from Firestore"""
        if not user_id:
            return self._default_lang
        stored_language = self.language_service.get_user_language(user_id)
        if stored_language and self.is_language_supported(stored_language):
            return stored_language
        return self._default_lang
    
    def load_user_language_on_start(self, context: Any, update: Any = None) -> str:
        """Load user language from Firestore when user starts interaction"""
        # Try to get user_id from update first, then from context
        user_id = None
        if update and hasattr(update, 'effective_user'):
            user_id = getattr(update.effective_user, 'id', None)
            print(f"DEBUG: Got user_id from update: {user_id}")
        elif context and hasattr(context, 'effective_user'):
            user_id = getattr(context, 'effective_user', {}).get('id')
            print(f"DEBUG: Got user_id from context: {user_id}")
        
        if not user_id:
            print(f"DEBUG: No user_id found in update or context")
            return self._default_lang
        
        print(f"DEBUG: Loading language for user {user_id} from Firestore...")
        
        # Try to get from Firestore first
        stored_language = self.language_service.get_user_language(user_id)
        print(f"DEBUG: Retrieved language from Firestore: '{stored_language}'")
        
        if stored_language and self.is_language_supported(stored_language):
            # Save to context for this session
            if context and hasattr(context, 'user_data'):
                context.user_data['language'] = stored_language
            print(f"DEBUG: Language '{stored_language}' loaded and saved to context")
            return stored_language
        
        # Fallback to default
        print(f"DEBUG: No valid language found, using default: '{self._default_lang}'")
        return self._default_lang
    
    def get_language_from_context(self, context: Any, update: Any = None) -> str:
        """
        Получает язык из context.user_data или Firestore.
        
        Args:
            context: Контекст пользователя (обычно из Telegram bot)
            update: Update объект для получения user_id
            
        Returns:
            str: Код языка или язык по умолчанию
        """
        if not context:
            return self._default_lang
        
        # First try to get from context.user_data
        if hasattr(context, 'user_data'):
            user_data = getattr(context, 'user_data', {})
            language = user_data.get('language')
            
            if language and self.is_language_supported(language):
                return language
        
        # If not in context, try to load from Firestore
        user_id = None
        if update and hasattr(update, 'effective_user'):
            user_id = getattr(update.effective_user, 'id', None)
        elif hasattr(context, 'effective_user') and context.effective_user:
            user_id = getattr(context.effective_user, 'id', None)
        elif hasattr(context, 'user_data'):
            # Try to get user_id from stored in context
            user_id = context.user_data.get('_current_user_id')
        
        if user_id:
            print(f"DEBUG: Loading language from Firestore for user {user_id}")
            stored_language = self.language_service.get_user_language(user_id)
            print(f"DEBUG: Retrieved language from Firestore: '{stored_language}'")
            
            if stored_language and self.is_language_supported(stored_language):
                # Save to context for this session
                if hasattr(context, 'user_data'):
                    context.user_data['language'] = stored_language
                    print(f"DEBUG: Language '{stored_language}' saved to context for user {user_id}")
                return stored_language
            else:
                print(f"DEBUG: No valid language found in Firestore for user {user_id}, using default")
        else:
            print(f"DEBUG: No user_id found, using default language")
        
        return self._default_lang
    
    def get_text(self, key: str, context: Optional[Any] = None, 
                 language: Optional[str] = None, update: Optional[Any] = None, **kwargs) -> str:
        """
        Получает переведенный текст по ключу.
        
        Args:
            key: Ключ для поиска перевода (поддерживает вложенные ключи через точку, например "buttons.analyze_receipt")
            context: Контекст пользователя (опционально)
            language: Язык (опционально, если не указан, берется из context)
            update: Update объект для получения user_id (опционально)
            **kwargs: Переменные для интерполяции
            
        Returns:
            str: Переведенный текст с интерполяцией переменных
        """
        # Определяем язык
        if language is None and context is not None:
            language = self.get_language_from_context(context, update)
        elif language is None:
            language = self._default_lang
        
        # Получаем переводы для языка
        translations = self._translations.get(language, self._translations[self._default_lang])
        
        # Получаем текст с поддержкой вложенных ключей
        text = self._get_nested_value(translations, key)
        
        # Если текст не найден в текущем языке, пробуем fallback
        if not text and language != self._default_lang:
            fallback_translations = self._translations[self._default_lang]
            text = self._get_nested_value(fallback_translations, key)
        
        # Если текст все еще пустой, возвращаем ключ
        if not text:
            text = key
        
        # Выполняем интерполяцию переменных
        if kwargs:
            text = self._interpolate_variables(text, kwargs)
        
        return text
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> str:
        """
        Получает значение из вложенного словаря по ключу с поддержкой точечной нотации.
        
        Args:
            data: Словарь с переводами
            key: Ключ для поиска (например, "buttons.analyze_receipt")
            
        Returns:
            str: Найденное значение или пустая строка
        """
        if not key:
            return ""
        
        keys = key.split('.')
        current = data
        
        try:
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return ""
            
            return str(current) if current is not None else ""
        except (TypeError, AttributeError):
            return ""
    
    def _interpolate_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """
        Выполняет интерполяцию переменных в тексте.
        
        Поддерживает формат {variable} и {variable:format}.
        
        Args:
            text: Текст с плейсхолдерами
            variables: Словарь переменных для подстановки
            
        Returns:
            str: Текст с подставленными переменными
        """
        def replace_variable(match):
            var_name = match.group(1)
            format_spec = match.group(2) if match.group(2) else None
            
            if var_name in variables:
                value = variables[var_name]
                
                # Если указан формат, применяем его
                if format_spec:
                    try:
                        return f"{{value:{format_spec}}}".format(value=value)
                    except (ValueError, TypeError):
                        return str(value)
                else:
                    return str(value)
            else:
                # Если переменная не найдена, оставляем плейсхолдер
                return match.group(0)
        
        # Паттерн для поиска {variable} и {variable:format}
        pattern = r'\{([^}:]+)(?::([^}]+))?\}'
        return re.sub(pattern, replace_variable, text)
    
    def get_available_languages(self) -> list:
        """
        Возвращает список доступных языков.
        
        Returns:
            list: Список кодов языков
        """
        return list(self.SUPPORTED_LANGUAGES.keys())
    
    def is_language_supported(self, language: str) -> bool:
        """
        Проверяет, поддерживается ли язык.
        
        Args:
            language: Код языка для проверки
            
        Returns:
            bool: True если язык поддерживается
        """
        return language in self.SUPPORTED_LANGUAGES
    
    def get_translation_keys(self, language: Optional[str] = None) -> list:
        """
        Возвращает список всех ключей переводов для указанного языка.
        
        Args:
            language: Код языка (по умолчанию - язык по умолчанию)
            
        Returns:
            list: Список ключей переводов
        """
        if language is None:
            language = self._default_lang
        
        translations = self._translations.get(language, self._translations[self._default_lang])
        return list(translations.keys())
    
    def set_user_language(self, update_or_context: Any, context: Any = None, language: str = None) -> bool:
        """Set user language in context and save to Firestore"""
        # Handle both old and new calling conventions
        if context is None and language is None:
            # Old calling convention: set_user_language(context, language)
            context = update_or_context
            language = context
            update = None
        else:
            # New calling convention: set_user_language(update, context, language)
            update = update_or_context
            language = language
        
        if not self.is_language_supported(language):
            return False
        if not context or not hasattr(context, 'user_data'):
            return False

        # Save to context
        context.user_data['language'] = language

        # Get user_id from update or context
        user_id = None
        if update and hasattr(update, 'effective_user'):
            user_id = getattr(update.effective_user, 'id', None)
        elif hasattr(context, 'effective_user'):
            user_id = getattr(context.effective_user, 'id', None)
        
        if user_id:
            success = self.language_service.save_user_language(user_id, language)
            if success:
                print(f"✅ Language '{language}' saved to Firestore for user {user_id}")
            else:
                print(f"❌ Failed to save language '{language}' to Firestore for user {user_id}")
        else:
            print(f"⚠️ No user_id found, language '{language}' saved only to context")

        return True


# Global LocaleManager instance
_global_locale_manager = None
locale_manager = None


def get_global_locale_manager() -> LocaleManager:
    """
    Get the global LocaleManager instance (singleton pattern).
    
    Returns:
        LocaleManager: The global LocaleManager instance
    """
    global _global_locale_manager
    if _global_locale_manager is None:
        # LocaleManager должен быть инициализирован через initialize_locale_manager()
        # в main.py после инициализации Firestore
        raise RuntimeError("LocaleManager not initialized! Call initialize_locale_manager() first.")
    return _global_locale_manager


def initialize_locale_manager(db_instance=None):
    """Initialize the global LocaleManager at startup"""
    global _global_locale_manager, locale_manager
    
    # Initialize LanguageService with Firestore instance
    from services.language_service import get_language_service
    language_service = get_language_service(db_instance)
    
    # Create LocaleManager with the correct LanguageService
    _global_locale_manager = LocaleManager()
    _global_locale_manager.language_service = language_service
    
    # Update the global locale_manager variable for backward compatibility
    locale_manager = _global_locale_manager
    
    print("✅ Global LocaleManager initialized with Firestore instance")
    return _global_locale_manager
