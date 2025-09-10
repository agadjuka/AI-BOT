"""
UI Manager for Telegram bot - manages menu messages and cleanup
Implements single anchor + single menu screen architecture
"""
import asyncio
from typing import Optional, List, Dict, Any
from telegram import Update, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from config.settings import BotConfig
from config.locales.locale_manager import LocaleManager


class UIManager:
    """
    Manages UI messages and cleanup for the bot.
    
    Architecture rules:
    - Anchor: First user message with receipt (never touched)
    - Single menu: One working bot message under anchor
    - All transitions via editMessageText/editMessageReplyMarkup
    - Temporary hints/errors as ephemeral messages with auto-delete
    - Every menu must have back to receipt button
    """
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.locale = LocaleManager()
        self.MAX_MESSAGE_LENGTH = config.MAX_MESSAGE_LENGTH
        self.MESSAGE_DELAY = config.MESSAGE_DELAY
    
    async def send_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                       text: str, reply_markup: InlineKeyboardMarkup, 
                       parse_mode: str = 'Markdown') -> Message:
        """
        Send a new menu message (single working message under anchor)
        
        Architecture: This replaces any existing menu message and becomes the single working message
        
        Args:
            update: Telegram update object
            context: Bot context
            text: Message text
            reply_markup: Inline keyboard markup
            parse_mode: Text parsing mode
            
        Returns:
            Sent message object
        """
        # Clean up any existing menu messages first
        await self.cleanup_all_except_anchor(update, context)
        
        # Determine chat_id and message sending method
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
            reply_method = update.callback_query.message.reply_text
        elif hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
            reply_method = update.message.reply_text
        else:
            raise ValueError(self.locale.get_text("errors.invalid_update_object", context))
        
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
        
        # Store as the single working menu message
        context.user_data['working_menu_message_id'] = sent_message.message_id
        
        return sent_message
    
    async def edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                       message_id: int, text: str, reply_markup: InlineKeyboardMarkup,
                       parse_mode: str = 'Markdown') -> bool:
        """
        Edit the working menu message (single working message under anchor)
        
        Architecture: This edits the single working menu message
        
        Args:
            update: Telegram update object
            context: Bot context
            message_id: ID of message to edit (should be working_menu_message_id)
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
            print(self.locale.get_text("errors.failed_to_edit_message", context, message_id=message_id, error=str(e)))
            return False
    
    async def send_temp(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                       text: str, duration: int = 3, parse_mode: str = 'Markdown') -> Message:
        """
        Send a temporary ephemeral message that auto-deletes after specified duration
        
        Architecture: These are temporary hints/errors that don't interfere with the single menu
        
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
            raise ValueError(self.locale.get_text("errors.invalid_update_object", context))
        
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
        
        Architecture: This is called when back to receipt button is pressed to clean up everything except anchor
        
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
        
        # Add working menu message ID
        working_menu_message_id = context.user_data.get('working_menu_message_id')
        if working_menu_message_id and working_menu_message_id != anchor_message_id:
            message_ids_to_delete.append(working_menu_message_id)
        
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
        
        # Add messages from cleanup list (like file messages)
        cleanup_messages = context.user_data.get('messages_to_cleanup', [])
        for message_id in cleanup_messages:
            if message_id != anchor_message_id:
                message_ids_to_delete.append(message_id)
        
        # Delete messages
        for message_id in message_ids_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                print(self.locale.get_text("errors.failed_to_delete_message", context, message_id=message_id, error=str(e)))
        
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
            'working_menu_message_id', 'menu_message_ids', 'table_message_id', 'edit_menu_message_id', 
            'total_edit_menu_message_id', 'instruction_message_id', 
            'line_number_instruction_message_id', 'delete_line_number_instruction_message_id',
            'total_edit_instruction_message_id', 'processing_message_id', 'messages_to_cleanup'
        ]
        
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    def get_working_menu_id(self, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        """
        Get the working menu message ID
        
        Args:
            context: Bot context
            
        Returns:
            Working menu message ID or None
        """
        return context.user_data.get('working_menu_message_id')
    
    async def back_to_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle back to receipt button - clean up everything and show fresh root menu
        
        Architecture: This is the core method that implements the "back to receipt" functionality
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        # Clean up all messages except anchor
        await self.cleanup_all_except_anchor(update, context)
        
        # Clear only temporary/UI data, keep core receipt data
        self._clear_temporary_data(context)
        
        # Show fresh root menu (this will be implemented by the caller)
        # The caller should call show_final_report_with_edit_button or similar
    
    def _clear_temporary_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear only temporary/UI data, keep core receipt data"""
        keys_to_clear = [
            'line_to_edit', 'field_to_edit', 'cached_final_report', 'table_message_id', 
            'edit_menu_message_id', 'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id', 'ingredient_matching_result', 'current_match_index',
            'processing_message_id', 'changed_ingredient_indices', 'search_results',
            'position_search_results', 'awaiting_search', 'awaiting_position_search',
            'in_position_selection_mode', 'selected_line_number', 'position_match_search_results',
            'awaiting_ingredient_name_for_position', 'google_sheets_search_mode',
            'google_sheets_search_item_index', 'google_sheets_search_results',
            'selected_google_sheets_line', 'awaiting_google_sheets_ingredient_name',
            'pending_google_sheets_upload', 'pending_file_generation'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all receipt-related data from context"""
        keys_to_clear = [
            'receipt_data', 'original_data', 'line_to_edit', 'field_to_edit',
            'cached_final_report', 'table_message_id', 'edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id', 'ingredient_matching_result', 'current_match_index',
            'processing_message_id', 'changed_ingredient_indices', 'search_results',
            'position_search_results', 'awaiting_search', 'awaiting_position_search',
            'in_position_selection_mode', 'selected_line_number', 'position_match_search_results',
            'awaiting_ingredient_name_for_position', 'google_sheets_search_mode',
            'google_sheets_search_item_index', 'google_sheets_search_results',
            'selected_google_sheets_line', 'awaiting_google_sheets_ingredient_name'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    async def clear_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Clear all messages including anchor (for new page transitions)
        
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
        
        # Get all stored message IDs to delete
        message_ids_to_delete = []
        
        # Add working menu message ID
        working_menu_message_id = context.user_data.get('working_menu_message_id')
        if working_menu_message_id:
            message_ids_to_delete.append(working_menu_message_id)
        
        # Add anchor message ID
        anchor_message_id = context.user_data.get('anchor_message_id')
        if anchor_message_id:
            message_ids_to_delete.append(anchor_message_id)
        
        # Add other specific message IDs
        specific_message_ids = [
            'table_message_id', 'edit_menu_message_id', 'total_edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'processing_message_id'
        ]
        
        for key in specific_message_ids:
            message_id = context.user_data.get(key)
            if message_id:
                message_ids_to_delete.append(message_id)
        
        # Add messages from cleanup list (like file messages)
        cleanup_messages = context.user_data.get('messages_to_cleanup', [])
        for message_id in cleanup_messages:
            message_ids_to_delete.append(message_id)
        
        # Delete messages
        for message_id in message_ids_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                print(self.locale.get_text("errors.failed_to_delete_message", context, message_id=message_id, error=str(e)))
        
        # Clear all stored message IDs
        self._clear_stored_message_ids(context)
        context.user_data.pop('anchor_message_id', None)
    
    async def _delete_message_after_delay(self, context: ContextTypes.DEFAULT_TYPE, 
                                        chat_id: int, message_id: int, delay: int) -> None:
        """Delete a message after specified delay"""
        await asyncio.sleep(delay)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(self.locale.get_text("errors.failed_to_delete_temporary_message", context, message_id=message_id, error=str(e)))
