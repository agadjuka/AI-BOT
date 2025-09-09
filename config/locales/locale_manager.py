"""
LocaleManager - класс для управления локализацией в AI Bot
"""

import re
from typing import Dict, Any, Optional, Union
from config.locales.ru import RU_TRANSLATIONS
from config.locales.en import EN_TRANSLATIONS


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
    }
    
    # Язык по умолчанию
    DEFAULT_LANGUAGE = 'ru'
    
    def __init__(self):
        """Инициализация LocaleManager."""
        self._translations = self.SUPPORTED_LANGUAGES
        self._default_lang = self.DEFAULT_LANGUAGE
    
    def get_language_from_context(self, context: Any) -> str:
        """
        Получает язык из context.user_data.
        
        Args:
            context: Контекст пользователя (обычно из Telegram bot)
            
        Returns:
            str: Код языка ('ru' или 'en') или язык по умолчанию
        """
        if not context or not hasattr(context, 'user_data'):
            return self._default_lang
        
        user_data = getattr(context, 'user_data', {})
        language = user_data.get('language', self._default_lang)
        
        # Проверяем, поддерживается ли язык
        if language not in self.SUPPORTED_LANGUAGES:
            return self._default_lang
        
        return language
    
    def get_text(self, key: str, context: Optional[Any] = None, 
                 language: Optional[str] = None, **kwargs) -> str:
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
        # Определяем язык
        if language is None and context is not None:
            language = self.get_language_from_context(context)
        elif language is None:
            language = self._default_lang
        
        # Получаем переводы для языка
        translations = self._translations.get(language, self._translations[self._default_lang])
        
        # Получаем текст
        text = translations.get(key, '')
        
        # Если текст не найден в текущем языке, пробуем fallback
        if not text and language != self._default_lang:
            fallback_translations = self._translations[self._default_lang]
            text = fallback_translations.get(key, key)  # Если и в fallback нет, возвращаем ключ
        
        # Если текст все еще пустой, возвращаем ключ
        if not text:
            text = key
        
        # Выполняем интерполяцию переменных
        if kwargs:
            text = self._interpolate_variables(text, kwargs)
        
        return text
    
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
    
    def set_user_language(self, context: Any, language: str) -> bool:
        """
        Устанавливает язык пользователя в context.user_data.
        
        Args:
            context: Контекст пользователя
            language: Код языка для установки
            
        Returns:
            bool: True если язык установлен успешно
        """
        if not self.is_language_supported(language):
            return False
        
        if not context or not hasattr(context, 'user_data'):
            return False
        
        context.user_data['language'] = language
        return True


# Создаем глобальный экземпляр для удобства использования
locale_manager = LocaleManager()