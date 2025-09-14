"""
Admin Panel handlers for Telegram bot
Handles admin panel functionality including user management
"""
import asyncio
from typing import Optional, List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from services.user_service import get_user_service
from utils.role_initializer import check_user_permissions
from config.locales.locale_manager import get_global_locale_manager


class AdminPanelHandler:
    """Handler for admin panel functionality"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        self.config = config
        self.analysis_service = analysis_service
        self.locale_manager = get_global_locale_manager()
    
    async def is_admin(self, user_id: int, db_instance) -> bool:
        """Check if user is admin"""
        try:
            import main
            db = main.db if db_instance is None else db_instance
        except (ImportError, AttributeError):
            db = db_instance
        
        if not db:
            return False
        
        permissions = await check_user_permissions(user_id, None, db)
        return permissions['is_admin']
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show main admin panel screen"""
        query = update.callback_query
        await query.answer()
        
        # Check admin permissions
        user_id = update.effective_user.id
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not await self.is_admin(user_id, db):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Create admin panel keyboard
        keyboard = [
            [InlineKeyboardButton("👤 Добавить пользователя", callback_data="admin_add_user")],
            [InlineKeyboardButton("🗑️ Удалить пользователя", callback_data="admin_delete_user")],
            [InlineKeyboardButton("📋 Список пользователей", callback_data="admin_list_users")],
            [InlineKeyboardButton("⬅️ Назад в Дашборд", callback_data="dashboard_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👑 **Админ-панель**\nЗдесь вы можете управлять доступом пользователей к боту.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def show_add_user_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show add user screen and request username"""
        query = update.callback_query
        await query.answer()
        
        # Check admin permissions
        user_id = update.effective_user.id
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not await self.is_admin(user_id, db):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Create back button
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Пожалуйста, отправьте юзернейм пользователя, которому вы хотите предоставить доступ. Формат: `@username`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Set conversation state
        context.user_data['_conversation_state'] = self.config.AWAITING_ADMIN_USERNAME
        
        return self.config.AWAITING_ADMIN_USERNAME
    
    async def handle_username_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle username input for adding user"""
        # Check admin permissions
        user_id = update.effective_user.id
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not await self.is_admin(user_id, db):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Get username from message
        username = update.message.text.strip()
        
        # Validate username format
        if not username.startswith('@'):
            await update.message.reply_text(
                "❌ Неверный формат юзернейма. Пожалуйста, используйте формат `@username`",
                parse_mode='Markdown'
            )
            return self.config.AWAITING_ADMIN_USERNAME
        
        # Clean username (remove @ and convert to lowercase)
        clean_username = username[1:].lower()
        
        if not clean_username:
            await update.message.reply_text(
                "❌ Юзернейм не может быть пустым. Пожалуйста, используйте формат `@username`",
                parse_mode='Markdown'
            )
            return self.config.AWAITING_ADMIN_USERNAME
        
        # Add user to whitelist
        user_service = get_user_service(db)
        success = await user_service.add_to_whitelist(clean_username)
        
        if success:
            # Show success message and return to admin panel
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Пользователь @{clean_username} добавлен в белый список. Теперь он сможет активировать бота, отправив команду /start.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка при добавлении пользователя @{clean_username} в белый список.",
                parse_mode='Markdown'
            )
            return self.config.AWAITING_ADMIN_USERNAME
        
        return self.config.AWAITING_DASHBOARD
    
    async def show_list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show list of authorized users"""
        query = update.callback_query
        await query.answer()
        
        # Check admin permissions
        user_id = update.effective_user.id
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not await self.is_admin(user_id, db):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Get users with role "user"
        user_service = get_user_service(db)
        
        try:
            # Query users collection for documents with role "user"
            users_ref = db.collection('users')
            query_result = users_ref.where('role', '==', 'user').stream()
            
            users = []
            for doc in query_result:
                user_data = doc.to_dict()
                user_data['user_id'] = doc.id
                users.append(user_data)
            
            # Create message text
            if users:
                message_text = "**Авторизованные пользователи:**\n\n"
                for i, user in enumerate(users, 1):
                    username = user.get('username', f"User_{user.get('user_id', 'Unknown')}")
                    user_id = user.get('user_id', 'N/A')
                    message_text += f"{i}. {username} (@{username}) - ID: {user_id}\n"
            else:
                message_text = "📋 **Список пользователей пуст**\n\nНет авторизованных пользователей."
            
            # Create back button
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"❌ Error getting users list: {e}")
            await query.edit_message_text(
                "❌ Ошибка при получении списка пользователей.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")
                ]])
            )
        
        return self.config.AWAITING_DASHBOARD
    
    async def show_delete_user_screen(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show delete user screen with user selection buttons"""
        query = update.callback_query
        await query.answer()
        
        # Check admin permissions
        user_id = update.effective_user.id
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not await self.is_admin(user_id, db):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        try:
            # Query users collection for documents with role "user"
            users_ref = db.collection('users')
            query_result = users_ref.where('role', '==', 'user').stream()
            
            users = []
            for doc in query_result:
                user_data = doc.to_dict()
                user_data['user_id'] = doc.id
                users.append(user_data)
            
            if not users:
                # No users to delete
                keyboard = [
                    [InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📋 **Нет пользователей для удаления**\n\nСписок авторизованных пользователей пуст.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_DASHBOARD
            
            # Create keyboard with user buttons
            keyboard = []
            for user in users:
                username = user.get('username', f"User_{user.get('user_id', 'Unknown')}")
                user_id = user.get('user_id')
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 {username}",
                        callback_data=f"admin_delete_confirm_{user_id}"
                    )
                ])
            
            # Add back button
            keyboard.append([
                InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Кого вы хотите удалить? После удаления пользователь потеряет доступ к боту.",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            print(f"❌ Error getting users for deletion: {e}")
            await query.edit_message_text(
                "❌ Ошибка при получении списка пользователей.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")
                ]])
            )
        
        return self.config.AWAITING_DASHBOARD
    
    async def show_delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id_to_delete: str) -> int:
        """Show delete confirmation for specific user"""
        query = update.callback_query
        await query.answer()
        
        # Check admin permissions
        user_id = update.effective_user.id
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not await self.is_admin(user_id, db):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        try:
            # Get user info
            user_ref = db.collection('users').document(user_id_to_delete)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                await query.edit_message_text(
                    "❌ Пользователь не найден.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")
                    ]])
                )
                return self.config.AWAITING_DASHBOARD
            
            user_data = user_doc.to_dict()
            username = user_data.get('username', f"User_{user_id_to_delete}")
            
            # Store user info in context for deletion
            context.user_data['admin_delete_user_id'] = user_id_to_delete
            context.user_data['admin_delete_username'] = username
            
            # Create confirmation keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Да, удалить", callback_data="admin_delete_final"),
                    InlineKeyboardButton("❌ Отмена", callback_data="admin_delete_user")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Вы уверены, что хотите удалить пользователя @{username}?",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            print(f"❌ Error getting user info for deletion: {e}")
            await query.edit_message_text(
                "❌ Ошибка при получении информации о пользователе.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")
                ]])
            )
        
        return self.config.AWAITING_ADMIN_CONFIRM_DELETE
    
    async def confirm_user_deletion(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Confirm and execute user deletion"""
        query = update.callback_query
        await query.answer()
        
        # Check admin permissions
        user_id = update.effective_user.id
        try:
            import main
            db = main.db
        except (ImportError, AttributeError):
            db = None
        
        if not await self.is_admin(user_id, db):
            await query.edit_message_text("❌ Access denied. Admin privileges required.")
            return self.config.AWAITING_DASHBOARD
        
        # Get user info from context
        user_id_to_delete = context.user_data.get('admin_delete_user_id')
        username = context.user_data.get('admin_delete_username')
        
        if not user_id_to_delete:
            await query.edit_message_text(
                "❌ Ошибка: информация о пользователе не найдена.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")
                ]])
            )
            return self.config.AWAITING_DASHBOARD
        
        try:
            # Delete user document
            user_ref = db.collection('users').document(user_id_to_delete)
            user_ref.delete()
            
            # Clear context
            context.user_data.pop('admin_delete_user_id', None)
            context.user_data.pop('admin_delete_username', None)
            
            # Show success message and return to delete user screen
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к выбору пользователя", callback_data="admin_delete_user")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🗑️ Пользователь @{username} удален.",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            await query.edit_message_text(
                f"❌ Ошибка при удалении пользователя @{username}.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="admin_panel")
                ]])
            )
        
        return self.config.AWAITING_DASHBOARD
