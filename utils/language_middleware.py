"""
Middleware для автоматического сохранения user_id в контексте
"""
from typing import Any
from telegram import Update
from telegram.ext import ContextTypes

def save_user_id_to_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Сохраняет user_id в контексте для последующего использования в get_text()
    """
    if update and hasattr(update, 'effective_user') and context:
        user_id = getattr(update.effective_user, 'id', None)
        if user_id and hasattr(context, 'user_data'):
            context.user_data['_current_user_id'] = user_id
            print(f"DEBUG: Saved user_id {user_id} to context")

def get_user_id_from_context(context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получает user_id из контекста
    """
    if context and hasattr(context, 'user_data'):
        return context.user_data.get('_current_user_id')
    return None

