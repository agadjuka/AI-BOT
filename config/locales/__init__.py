"""
Модуль локализации для AI Bot
Содержит переводы и управление языковыми настройками
"""

from .locale_manager import LocaleManager
from .ru_flat import RU_TRANSLATIONS
from .en_flat import EN_TRANSLATIONS
from .id import ID_TRANSLATIONS

# Создаем глобальный экземпляр LocaleManager
locale_manager = LocaleManager()

__all__ = [
    'LocaleManager', 
    'locale_manager',
    'RU_TRANSLATIONS', 
    'EN_TRANSLATIONS',
    'ID_TRANSLATIONS'
]
