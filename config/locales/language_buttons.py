"""
Language selection buttons for the AI Bot application.
These buttons are the same for all language versions and are not translated.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Create language selection keyboard with flags and language names.
    
    Returns:
        InlineKeyboardMarkup: Keyboard with language selection buttons
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Language buttons with flags and names (not translated)
    keyboard.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="lang_id")
    )
    
    return keyboard


# Language codes mapping for easy reference
LANGUAGE_CODES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English", 
    "id": "🇮🇩 Bahasa Indonesia"
}

# Reverse mapping for getting language code from display name
DISPLAY_TO_CODE = {
    "🇷🇺 Русский": "ru",
    "🇺🇸 English": "en",
    "🇮🇩 Bahasa Indonesia": "id"
}
