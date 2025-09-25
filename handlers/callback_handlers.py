"""
Callback handlers for Telegram bot - Template version
Simplified version for basic bot functionality
"""
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from config.locales.locale_manager import get_global_locale_manager


class CallbackHandlers:
    """Main callback handlers coordinator - Template version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        self.config = config
        self.analysis_service = analysis_service
        self.locale_manager = get_global_locale_manager()
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        callback_data = query.data
        
        if callback_data == "help":
            await self._handle_help_callback(update, context, language)
        elif callback_data == "language":
            await self._handle_language_callback(update, context, language)
        elif callback_data.startswith("lang_"):
            await self._handle_language_selection(update, context, callback_data)
        else:
            await self._handle_unknown_callback(update, context, language)
        
        return self.config.AWAITING_INPUT
    
    async def _handle_help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Handle help callback"""
        help_text = self._get_help_message(language)
        
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode='HTML'
        )
    
    async def _handle_language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Handle language selection callback"""
        keyboard = self._get_language_keyboard()
        
        await update.callback_query.edit_message_text(
            self._get_language_selection_message(language),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def _handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Handle language selection"""
        language = callback_data.replace("lang_", "")
        user_id = update.effective_user.id
        
        # Set user language
        self.locale_manager.set_user_language(user_id, language)
        
        # Send confirmation
        confirmation_text = self._get_language_confirmation_message(language)
        
        await update.callback_query.edit_message_text(
            confirmation_text,
            parse_mode='HTML'
        )
    
    async def _handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Handle unknown callback"""
        error_text = self._get_unknown_callback_message(language)
        
        await update.callback_query.edit_message_text(
            error_text,
            parse_mode='HTML'
        )
    
    def _get_language_keyboard(self) -> InlineKeyboardMarkup:
        """Get language selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("English", callback_data="lang_en")],
            [InlineKeyboardButton("Русский", callback_data="lang_ru")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_help_message(self, language: str) -> str:
        """Get help message based on language"""
        messages = {
            'en': """
<b>Help - AI Bot Template</b>

This bot can:
• Respond to text messages using AI
• Support multiple languages
• Provide basic conversation capabilities

<b>Commands:</b>
/start - Start the bot
/help - Show this help

<b>Usage:</b>
Just send any text message and the bot will respond using AI!
            """,
            'ru': """
<b>Справка - AI Bot Template</b>

Этот бот может:
• Отвечать на текстовые сообщения с помощью ИИ
• Поддерживать несколько языков
• Обеспечивать базовые возможности общения

<b>Команды:</b>
/start - Запустить бота
/help - Показать эту справку

<b>Использование:</b>
Просто отправьте любое текстовое сообщение, и бот ответит с помощью ИИ!
            """
        }
        return messages.get(language, messages['en'])
    
    def _get_language_selection_message(self, language: str) -> str:
        """Get language selection message based on language"""
        messages = {
            'en': "Please select your language:",
            'ru': "Пожалуйста, выберите ваш язык:"
        }
        return messages.get(language, messages['en'])
    
    def _get_language_confirmation_message(self, language: str) -> str:
        """Get language confirmation message based on language"""
        messages = {
            'en': f"Language set to: {language.upper()}",
            'ru': f"Язык установлен: {language.upper()}"
        }
        return messages.get(language, messages['en'])
    
    def _get_unknown_callback_message(self, language: str) -> str:
        """Get unknown callback message based on language"""
        messages = {
            'en': "Unknown command. Please try again.",
            'ru': "Неизвестная команда. Попробуйте еще раз."
        }
        return messages.get(language, messages['en'])