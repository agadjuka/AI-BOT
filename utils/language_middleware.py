"""
Middleware для автоматического сохранения user_id в контексте
"""
import asyncio
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
            
            # Load turbo mode from Firestore if not already loaded
            if 'turbo_mode' not in context.user_data:
                asyncio.create_task(load_turbo_mode_from_firestore(user_id, context))

async def load_turbo_mode_from_firestore(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Load turbo mode setting from Firestore and save to context"""
    try:
        # Import Firestore client
        from google.cloud import firestore
        
        # Get global Firestore instance
        import main
        db = main.db
        
        if not db:
            print("❌ Firestore not available for loading turbo mode")
            return
        
        # Load from users/{user_id}/settings/turbo_mode
        user_ref = db.collection('users').document(str(user_id))
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            turbo_mode = user_data.get('turbo_mode', False)
            context.user_data['turbo_mode'] = turbo_mode
            print(f"✅ Turbo mode loaded from Firestore: user {user_id}, turbo={turbo_mode}")
        else:
            print(f"ℹ️ User {user_id} not found in Firestore, using default turbo=False")
            context.user_data['turbo_mode'] = False
            
    except Exception as e:
        print(f"❌ Error loading turbo mode from Firestore: {e}")
        context.user_data['turbo_mode'] = False

def get_user_id_from_context(context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получает user_id из контекста
    """
    if context and hasattr(context, 'user_data'):
        return context.user_data.get('_current_user_id')
    return None

