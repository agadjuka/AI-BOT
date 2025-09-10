"""
Модуль локализации для AI Bot
Содержит переводы и управление языковыми настройками
"""

from .locale_manager import LocaleManager
from .language_buttons import get_language_keyboard, LANGUAGE_CODES, DISPLAY_TO_CODE
from .ru import RU_TRANSLATIONS
from .en import EN_TRANSLATIONS
from .id import ID_TRANSLATIONS

# Создаем глобальный экземпляр LocaleManager
locale_manager = LocaleManager()

__all__ = [
    'LocaleManager', 
    'locale_manager',
    'get_language_keyboard',
    'LANGUAGE_CODES',
    'DISPLAY_TO_CODE',
    'RU_TRANSLATIONS', 
    'EN_TRANSLATIONS',
    'ID_TRANSLATIONS'
]
