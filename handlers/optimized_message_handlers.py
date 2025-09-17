"""
Optimized message handlers for Telegram bot with performance improvements
"""
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from handlers.base_message_handler import BaseMessageHandler
from handlers.optimized_photo_handler import OptimizedPhotoHandler
from handlers.input_handler import InputHandler
from handlers.ingredient_matching_input_handler import IngredientMatchingInputHandler
from handlers.google_sheets_input_handler import GoogleSheetsInputHandler
from handlers.ingredients_file_handler import IngredientsFileHandler
from handlers.ingredients_text_handler import IngredientsTextHandler
from handlers.admin_panel import AdminPanelHandler
from utils.common_handlers import CommonHandlers
from utils.access_control import access_check
from config.locales.locale_manager import get_global_locale_manager
from config.locales.language_buttons import get_language_keyboard
from services.user_service import get_user_service
from utils.performance_utils import measure_performance, cache_manager


class OptimizedMessageHandlers(BaseMessageHandler):
    """Optimized message handlers with performance improvements"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        
        # Initialize LocaleManager
        self.locale_manager = get_global_locale_manager()
        
        # Initialize handlers with performance optimizations
        self.photo_handler = OptimizedPhotoHandler(config, analysis_service)
        self.input_handler = InputHandler(config, analysis_service)
        self.ingredient_matching_input_handler = IngredientMatchingInputHandler(config, analysis_service)
        self.google_sheets_input_handler = GoogleSheetsInputHandler(config, analysis_service)
        self.ingredients_file_handler = IngredientsFileHandler(config, analysis_service)
        self.ingredients_text_handler = IngredientsTextHandler(config, analysis_service)
        self.admin_panel_handler = AdminPanelHandler(config, analysis_service)
        self.common_handlers = CommonHandlers(config, analysis_service)
    
    @access_check
    @measure_performance("message_handlers.handle_photo")
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle photo upload with optimized processing"""
        return await self.photo_handler.handle_photo(update, context)
    
    @access_check
    @measure_performance("message_handlers.handle_text")
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle text messages with caching"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check for admin commands first
        if text.startswith('/admin'):
            return await self.admin_panel_handler.handle_admin_command(update, context)
        
        # Check for language selection
        if text.startswith('/language'):
            return await self._handle_language_selection(update, context)
        
        # Check for help commands
        if text.startswith('/help'):
            return await self._handle_help_command(update, context)
        
        # Check for start command
        if text.startswith('/start'):
            return await self._handle_start_command(update, context)
        
        # Route to appropriate handler based on context
        return await self._route_text_message(update, context)
    
    async def _handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle language selection with caching"""
        user_id = update.effective_user.id
        
        # Show language selection with cached keyboard
        language_keyboard = await cache_manager.get_or_set(
            "language_keyboard",
            lambda: get_language_keyboard(),
            ttl=3600  # Cache for 1 hour
        )
        
        await update.message.reply_text(
            self.get_text("welcome.choose_language", context, update=update),
            reply_markup=language_keyboard
        )
        
        return self.config.AWAITING_CORRECTION
    
    async def _handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle help command with cached content"""
        help_text = await cache_manager.get_or_set(
            "help_text",
            lambda: self._generate_help_text(context, update),
            ttl=1800  # Cache for 30 minutes
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return self.config.AWAITING_CORRECTION
    
    async def _handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle start command with optimized dashboard creation"""
        user_id = update.effective_user.id
        
        # Get user data with caching
        user_data = await self._get_user_data_cached(user_id)
        
        # Create dashboard with cached keyboard
        keyboard, is_admin = await self._create_dashboard_keyboard_cached(update, context, user_data)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = self.get_text(
            "welcome.dashboard.welcome_message", 
            context, 
            update=update,
            user=update.effective_user.mention_html()
        )
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_CORRECTION
    
    async def _route_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Route text message to appropriate handler"""
        # Check current conversation state
        current_state = context.user_data.get('conversation_state', 'idle')
        
        if current_state == 'awaiting_column_input':
            return await self.input_handler.handle_column_input(update, context)
        elif current_state == 'awaiting_ingredient_input':
            return await self.ingredient_matching_input_handler.handle_ingredient_input(update, context)
        elif current_state == 'awaiting_google_sheets_input':
            return await self.google_sheets_input_handler.handle_google_sheets_input(update, context)
        elif current_state == 'awaiting_ingredients_file':
            return await self.ingredients_file_handler.handle_ingredients_file(update, context)
        elif current_state == 'awaiting_ingredients_text':
            return await self.ingredients_text_handler.handle_ingredients_text(update, context)
        else:
            # Default: show help
            return await self._handle_help_command(update, context)
    
    async def _get_user_data_cached(self, user_id: int) -> dict:
        """Get user data with caching"""
        cache_key = f"user_data_{user_id}"
        
        return await cache_manager.get_or_set(
            cache_key,
            lambda: self._fetch_user_data(user_id),
            ttl=300  # Cache for 5 minutes
        )
    
    async def _fetch_user_data(self, user_id: int) -> dict:
        """Actually fetch user data from database"""
        try:
            user_service = get_user_service()
            
            # Get user data in parallel
            display_mode_task = user_service.get_user_display_mode(user_id)
            language_task = user_service.get_user_language(user_id)
            role_task = user_service.get_user_role(user_id)
            
            display_mode, language, role = await asyncio.gather(
                display_mode_task,
                language_task,
                role_task,
                return_exceptions=True
            )
            
            return {
                'display_mode': display_mode if not isinstance(display_mode, Exception) else 'mobile',
                'language': language if not isinstance(language, Exception) else 'ru',
                'role': role if not isinstance(role, Exception) else 'user'
            }
            
        except Exception as e:
            print(f"❌ Error fetching user data: {e}")
            return {
                'display_mode': 'mobile',
                'language': 'ru',
                'role': 'user'
            }
    
    async def _create_dashboard_keyboard_cached(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: dict) -> tuple:
        """Create dashboard keyboard with caching"""
        cache_key = f"dashboard_keyboard_{user_data.get('role', 'user')}"
        
        return await cache_manager.get_or_set(
            cache_key,
            lambda: self._create_dashboard_keyboard(update, context, user_data),
            ttl=600  # Cache for 10 minutes
        )
    
    async def _create_dashboard_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: dict) -> tuple:
        """Actually create dashboard keyboard"""
        keyboard = []
        is_admin = user_data.get('role') == 'admin'
        
        # Main buttons
        keyboard.append([
            InlineKeyboardButton(
                self.get_text("buttons.upload_photo", context, update=update),
                callback_data="upload_photo"
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                self.get_text("buttons.ingredients_management", context, update=update),
                callback_data="ingredients_management"
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                self.get_text("buttons.google_sheets_management", context, update=update),
                callback_data="dashboard_google_sheets_management"
            )
        ])
        
        # Admin buttons
        if is_admin:
            keyboard.append([
                InlineKeyboardButton(
                    self.get_text("buttons.admin_panel", context, update=update),
                    callback_data="admin_panel"
                )
            ])
        
        # Settings buttons
        keyboard.append([
            InlineKeyboardButton(
                self.get_text("buttons.language_settings", context, update=update),
                callback_data="dashboard_language_settings"
            ),
            InlineKeyboardButton(
                self.get_text("buttons.display_mode", context, update=update),
                callback_data="toggle_display_mode"
            )
        ])
        
        return keyboard, is_admin
    
    async def _generate_help_text(self, context: ContextTypes.DEFAULT_TYPE, update: Update) -> str:
        """Generate help text"""
        return f"""
🤖 **Помощь по боту**

**Основные команды:**
• `/start` - Главное меню
• `/help` - Эта справка
• `/language` - Выбор языка

**Как использовать:**
1. 📸 Загрузите фото чека
2. 🔍 Бот проанализирует товары
3. ✏️ Отредактируйте при необходимости
4. 📊 Сохраните в Google Sheets

**Поддержка:** @your_support_username
        """
    
    @measure_performance("message_handlers.create_dashboard_keyboard")
    async def _create_dashboard_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
        """Create dashboard keyboard - public method for compatibility"""
        user_id = update.effective_user.id
        user_data = await self._get_user_data_cached(user_id)
        return await self._create_dashboard_keyboard(update, context, user_data)
