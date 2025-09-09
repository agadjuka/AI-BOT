"""
Модуль локализации для AI Bot
Содержит переводы и управление языковыми настройками
"""

from .locale_manager import LocaleManager
from .ru import RU_TRANSLATIONS
from .en import EN_TRANSLATIONS

# Создаем глобальный экземпляр LocaleManager
locale_manager = LocaleManager()

__all__ = [
    'LocaleManager', 
    'locale_manager',
    'RU_TRANSLATIONS', 
    'EN_TRANSLATIONS'
]
