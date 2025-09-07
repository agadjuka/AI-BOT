"""
Message sender utility for centralized message sending in Telegram bot
"""
import asyncio
from typing import Optional, List, Dict, Any
from telegram import Update, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from config.settings import BotConfig


class MessageSender:
    """
    Centralized message sender for Telegram bot.
    
    Provides methods for sending different types of messages:
    - Long messages with keyboard (split if needed)
    - Temporary messages (auto-delete)
    - Error messages (with error styling)
    - Success messages (with success styling)
    """
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.MAX_MESSAGE_LENGTH = config.MAX_MESSAGE_LENGTH
        self.MESSAGE_DELAY = config.MESSAGE_DELAY
    
    async def send_long_message_with_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                            text: str, reply_markup: InlineKeyboardMarkup,
                                            parse_mode: str = 'Markdown') -> Message:
        """
        Send a long message with keyboard, splitting if necessary.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Message text
            reply_markup: Inline keyboard markup
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Determine reply method
        if hasattr(update, 'callback_query') and update.callback_query:
            reply_method = update.callback_query.message.reply_text
        elif hasattr(update, 'message') and update.message:
            reply_method = update.message.reply_text
        else:
            raise ValueError("Invalid update object")
        
        # Send message with keyboard
        if len(text) <= self.MAX_MESSAGE_LENGTH:
            sent_message = await reply_method(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            # Split into parts
            parts = [text[i:i + self.MAX_MESSAGE_LENGTH] for i in range(0, len(text), self.MAX_MESSAGE_LENGTH)]
            
            # Send all parts except last
            for part in parts[:-1]:
                await reply_method(part, parse_mode=parse_mode)
                await asyncio.sleep(self.MESSAGE_DELAY)
            
            # Send last part with keyboard
            sent_message = await reply_method(parts[-1], reply_markup=reply_markup, parse_mode=parse_mode)
        
        return sent_message
    
    async def send_temp_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              text: str, duration: int = 3, parse_mode: str = 'Markdown') -> Message:
        """
        Send a temporary message that auto-deletes after specified duration.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Message text
            duration: Auto-delete duration in seconds
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Determine reply method
        if hasattr(update, 'callback_query') and update.callback_query:
            reply_method = update.callback_query.message.reply_text
        elif hasattr(update, 'message') and update.message:
            reply_method = update.message.reply_text
        else:
            raise ValueError("Invalid update object")
        
        # Send message
        sent_message = await reply_method(text, parse_mode=parse_mode)
        
        # Schedule deletion
        asyncio.create_task(self._delete_message_after_delay(
            context, sent_message.chat_id, sent_message.message_id, duration
        ))
        
        return sent_message
    
    async def send_error_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               text: str, duration: int = 5, parse_mode: str = 'Markdown') -> Message:
        """
        Send an error message with error styling and auto-delete.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Error message text
            duration: Auto-delete duration in seconds
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Add error styling
        error_text = f"❌ **Ошибка**\n\n{text}"
        
        return await self.send_temp_message(update, context, error_text, duration, parse_mode)
    
    async def send_success_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 text: str, duration: int = 3, parse_mode: str = 'Markdown') -> Message:
        """
        Send a success message with success styling and auto-delete.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Success message text
            duration: Auto-delete duration in seconds
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Add success styling
        success_text = f"✅ **Успешно**\n\n{text}"
        
        return await self.send_temp_message(update, context, success_text, duration, parse_mode)
    
    async def send_info_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              text: str, duration: int = 4, parse_mode: str = 'Markdown') -> Message:
        """
        Send an info message with info styling and auto-delete.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Info message text
            duration: Auto-delete duration in seconds
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Add info styling
        info_text = f"ℹ️ **Информация**\n\n{text}"
        
        return await self.send_temp_message(update, context, info_text, duration, parse_mode)
    
    async def send_warning_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 text: str, duration: int = 4, parse_mode: str = 'Markdown') -> Message:
        """
        Send a warning message with warning styling and auto-delete.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Warning message text
            duration: Auto-delete duration in seconds
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Add warning styling
        warning_text = f"⚠️ **Предупреждение**\n\n{text}"
        
        return await self.send_temp_message(update, context, warning_text, duration, parse_mode)
    
    async def send_processing_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    text: str = "Обрабатываю...", duration: int = 10) -> Message:
        """
        Send a processing message with loading indicator.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Processing message text
            duration: Auto-delete duration in seconds
            
        Returns:
            Sent message object
        """
        # Add processing styling
        processing_text = f"🔄 {text}"
        
        return await self.send_temp_message(update, context, processing_text, duration)
    
    async def send_confirmation_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      text: str, duration: int = 5) -> Message:
        """
        Send a confirmation message with confirmation styling.
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Confirmation message text
            duration: Auto-delete duration in seconds
            
        Returns:
            Sent message object
        """
        # Add confirmation styling
        confirmation_text = f"✅ {text}"
        
        return await self.send_temp_message(update, context, confirmation_text, duration)
    
    async def _delete_message_after_delay(self, context: ContextTypes.DEFAULT_TYPE, 
                                        chat_id: int, message_id: int, delay: int) -> None:
        """Delete a message after specified delay"""
        await asyncio.sleep(delay)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Failed to delete temporary message {message_id}: {e}")
    
    def format_error_message(self, error: Exception, context: str = "") -> str:
        """
        Format an exception into a user-friendly error message.
        
        Args:
            error: Exception object
            context: Additional context about where the error occurred
            
        Returns:
            Formatted error message
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        if context:
            return f"**{context}**\n\n**Тип ошибки:** {error_type}\n**Описание:** {error_message}"
        else:
            return f"**Тип ошибки:** {error_type}\n**Описание:** {error_message}"
    
    def format_success_message(self, action: str, details: str = "") -> str:
        """
        Format a success message with action and optional details.
        
        Args:
            action: Action that was completed successfully
            details: Optional additional details
            
        Returns:
            Formatted success message
        """
        if details:
            return f"**{action}**\n\n{details}"
        else:
            return f"**{action}**"
    
    def format_info_message(self, title: str, content: str) -> str:
        """
        Format an info message with title and content.
        
        Args:
            title: Message title
            content: Message content
            
        Returns:
            Formatted info message
        """
        return f"**{title}**\n\n{content}"
    
    def format_warning_message(self, warning: str, suggestion: str = "") -> str:
        """
        Format a warning message with warning and optional suggestion.
        
        Args:
            warning: Warning text
            suggestion: Optional suggestion for user
            
        Returns:
            Formatted warning message
        """
        if suggestion:
            return f"**{warning}**\n\n💡 **Рекомендация:** {suggestion}"
        else:
            return f"**{warning}**"
