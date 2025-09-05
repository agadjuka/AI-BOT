"""
UI Manager for Telegram bot - manages menu messages and cleanup
"""
import asyncio
from typing import Optional, List, Dict, Any
from telegram import Update, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from config.settings import BotConfig


class UIManager:
    """Manages UI messages and cleanup for the bot"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.MAX_MESSAGE_LENGTH = config.MAX_MESSAGE_LENGTH
        self.MESSAGE_DELAY = config.MESSAGE_DELAY
    
    async def send_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                       text: str, reply_markup: InlineKeyboardMarkup, 
                       parse_mode: str = 'Markdown') -> Message:
        """
        Send a new menu message and store its ID for cleanup
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Message text
            reply_markup: Inline keyboard markup
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Determine chat_id and message sending method
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
            reply_method = update.callback_query.message.reply_text
        elif hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
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
        
        # Store message ID for cleanup
        self._store_menu_message_id(context, sent_message.message_id)
        
        return sent_message
    
    async def edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                       message_id: int, text: str, reply_markup: InlineKeyboardMarkup,
                       parse_mode: str = 'Markdown') -> bool:
        """
        Edit an existing menu message
        
        Args:
            update: Telegram update object
            context: Bot context
            message_id: ID of message to edit
            text: New message text
            reply_markup: New inline keyboard markup
            parse_mode: Text parsing mode
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine chat_id
            if hasattr(update, 'callback_query') and update.callback_query:
                chat_id = update.callback_query.message.chat_id
            elif hasattr(update, 'message') and update.message:
                chat_id = update.message.chat_id
            else:
                return False
            
            # Edit message
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to edit message {message_id}: {e}")
            return False
    
    async def send_temp(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                       text: str, duration: int = 3, parse_mode: str = 'Markdown') -> Message:
        """
        Send a temporary message that auto-deletes after specified duration
        
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
    
    async def cleanup_all_except_anchor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Clean up all messages except the anchor (first receipt message)
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        # Get chat_id
        chat_id = None
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
        elif hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
        
        if not chat_id:
            return
        
        # Get anchor message ID
        anchor_message_id = context.user_data.get('anchor_message_id')
        
        # Get all stored message IDs to delete
        message_ids_to_delete = []
        
        # Add menu message IDs
        menu_message_ids = context.user_data.get('menu_message_ids', [])
        message_ids_to_delete.extend(menu_message_ids)
        
        # Add other specific message IDs
        specific_message_ids = [
            'table_message_id', 'edit_menu_message_id', 'total_edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'processing_message_id'
        ]
        
        for key in specific_message_ids:
            message_id = context.user_data.get(key)
            if message_id and message_id != anchor_message_id:
                message_ids_to_delete.append(message_id)
        
        # Delete messages
        for message_id in message_ids_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                print(f"Failed to delete message {message_id}: {e}")
        
        # Clear stored message IDs
        self._clear_stored_message_ids(context)
    
    def set_anchor(self, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
        """
        Set the anchor message ID (first receipt message)
        
        Args:
            context: Bot context
            message_id: ID of the anchor message
        """
        context.user_data['anchor_message_id'] = message_id
    
    def get_anchor_id(self, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        """
        Get the anchor message ID
        
        Args:
            context: Bot context
            
        Returns:
            Anchor message ID or None
        """
        return context.user_data.get('anchor_message_id')
    
    def _store_menu_message_id(self, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
        """Store a menu message ID for cleanup"""
        if 'menu_message_ids' not in context.user_data:
            context.user_data['menu_message_ids'] = []
        context.user_data['menu_message_ids'].append(message_id)
    
    def _clear_stored_message_ids(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all stored message IDs except anchor"""
        keys_to_clear = [
            'menu_message_ids', 'table_message_id', 'edit_menu_message_id', 
            'total_edit_menu_message_id', 'instruction_message_id', 
            'line_number_instruction_message_id', 'delete_line_number_instruction_message_id',
            'total_edit_instruction_message_id', 'processing_message_id'
        ]
        
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    async def _delete_message_after_delay(self, context: ContextTypes.DEFAULT_TYPE, 
                                        chat_id: int, message_id: int, delay: int) -> None:
        """Delete a message after specified delay"""
        await asyncio.sleep(delay)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Failed to delete temporary message {message_id}: {e}")
