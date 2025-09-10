"""
Language selection buttons for the AI Bot application.
These buttons are the same for all language versions and are not translated.
"""

try:
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
except ImportError:
    # Для тестирования без telegram
    InlineKeyboardMarkup = None
    InlineKeyboardButton = None


def get_language_keyboard():
    """
    Create language selection keyboard with flags and language names.
    
    Returns:
        InlineKeyboardMarkup: Keyboard with language selection buttons
    """
    if InlineKeyboardMarkup is None or InlineKeyboardButton is None:
        raise ImportError("python-telegram-bot is required for get_language_keyboard function")
    
    # Language buttons with flags and names (not translated)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="select_language_ru")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="select_language_en")],
        [InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="select_language_id")]
    ])
    
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
