"""
Main entry point for the AI Bot application with webhook support for Cloud Run
Using FastAPI for better performance and modern async support
"""
import os
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.error import Conflict, NetworkError
from config.locales.locale_manager import initialize_locale_manager

# Инициализация клиента Firestore
# Этот код будет работать автоматически в Cloud Run
# и при локальной настройке с переменной окружения.
from google.cloud import firestore

# Инициализация клиента Firestore с обработкой ошибок
# В Cloud Run используется Application Default Credentials (ADC)
db = None
try:
    # Попробуем инициализировать Firestore
    db = firestore.Client(database='billscaner')
    print("✅ Firestore клиент инициализирован успешно (база: billscaner)")
except Exception as e:
    print(f"❌ Ошибка инициализации Firestore: {e}")
    print("💡 В Cloud Run используется Application Default Credentials (ADC)")
    print("💡 Firestore может быть недоступен, но бот будет работать без сохранения языков")
    db = None

# КРИТИЧЕСКИ ВАЖНО: Инициализируем LocaleManager СРАЗУ после Firestore
# Это должно произойти ДО импорта handlers, чтобы избежать race condition
from config.locales.locale_manager import initialize_locale_manager
initialize_locale_manager(db)

# Role initialization will be done in initialize_bot function

# Проверяем совместимость numpy/pandas перед импортом других модулей
try:
    import numpy as np
    import pandas as pd
    print(f"✅ numpy версия: {np.__version__}")
    print(f"✅ pandas версия: {pd.__version__}")
except ImportError as e:
    print(f"❌ Ошибка импорта numpy/pandas: {e}")
    # Не прерываем запуск, если numpy/pandas недоступны
    np = None
    pd = None

# Проверяем доступность OpenCV без его загрузки
try:
    from utils.opencv_lazy_loader import check_opencv_availability
    opencv_available = check_opencv_availability()
    print(f"✅ OpenCV доступен: {opencv_available}")
    if not opencv_available:
        print("⚠️ OpenCV недоступен - анализ изображений будет ограничен")
except Exception as e:
    print(f"⚠️ Не удалось проверить доступность OpenCV: {e}")
    opencv_available = False

# Импорты с обработкой ошибок
try:
    from config.settings import BotConfig
    from config.prompts import PromptManager
    from services.ai_service import AIService, ReceiptAnalysisServiceCompat, AIServiceFactory
    from handlers.message_handlers import MessageHandlers
    from handlers.callback_handlers import CallbackHandlers
    from utils.ingredient_storage import IngredientStorage
    from utils.message_sender import MessageSender
    from google_sheets_handler import get_google_sheets_ingredients
    print("✅ Все модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    # Устанавливаем None для всех модулей
    BotConfig = None
    PromptManager = None
    AIService = None
    ReceiptAnalysisServiceCompat = None
    MessageHandlers = None
    CallbackHandlers = None
    IngredientStorage = None
    MessageSender = None
    get_google_sheets_ingredients = None

# Bot configuration - будет инициализирован позже
TOKEN = None
TELEGRAM_API = None

# FastAPI app
app = FastAPI(title="AI Bot", description="Telegram Bot for receipt processing")

# Global variables
application: Optional[Application] = None
ingredient_storage: Optional[IngredientStorage] = None
keep_alive_task_obj: Optional[asyncio.Task] = None
locale_manager_cache: Optional[object] = None

async def cleanup_old_files_periodically(ingredient_storage: IngredientStorage) -> None:
    """Async background task to clean up old files every 30 minutes"""
    while True:
        try:
            await asyncio.sleep(1800)  # 30 minutes = 1800 seconds
            ingredient_storage.cleanup_old_files()
            print("🧹 Выполнена очистка старых файлов сопоставления")
        except asyncio.CancelledError:
            print("🧹 Задача очистки файлов отменена")
            break
        except Exception as e:
            print(f"❌ Ошибка при очистке файлов: {e}")
            # Продолжаем работу даже при ошибке
            await asyncio.sleep(60)  # Ждем минуту перед следующей попыткой

async def send_keep_alive_request() -> None:
    """Отправляет простой HTTP запрос на собственный URL для keep-alive - НЕЗАВИСИМАЯ ВЕРСИЯ"""
    # Хардкодим URL сервиса - никаких зависимостей от переменных окружения
    SERVICE_URL = "https://ai-bot-apmtihe4ga-as.a.run.app"
    
    try:
        # Убираем trailing slash если есть
        base_url = SERVICE_URL.rstrip('/')
        
        # Пробуем разные endpoints для keep-alive
        endpoints_to_try = [
            f"{base_url}/keepalive",  # Специальный keep-alive endpoint
            f"{base_url}/",           # Health check endpoint
            f"{base_url}/health"      # Альтернативный health endpoint
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:  # Уменьшили timeout
            for endpoint in endpoints_to_try:
                try:
                    response = await client.get(endpoint)
                    if response.status_code == 200:
                        print(f"✅ Keep-alive HTTP запрос успешен: {endpoint}")
                        return
                    else:
                        print(f"⚠️ Keep-alive HTTP запрос неуспешен: {endpoint} (HTTP {response.status_code})")
                except Exception as e:
                    print(f"⚠️ Ошибка keep-alive HTTP запроса {endpoint}: {e}")
                    continue
            
            # Если все endpoints не сработали, выводим предупреждение
            print("⚠️ Все keep-alive endpoints недоступны, но это не критично")
            
    except Exception as e:
        print(f"❌ Ошибка в send_keep_alive_request: {e}")
        # НЕ поднимаем исключение - keep-alive не должен влиять на работу бота

async def keep_alive_task() -> None:
    """Keep-alive задача для предотвращения засыпания Cloud Run - НЕЗАВИСИМАЯ ВЕРСИЯ"""
    print("💓 Keep-alive задача запущена (независимая версия)")
    
    while True:
        try:
            await asyncio.sleep(600)  # 10 minutes = 600 seconds
            
            import datetime
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"💓 Keep-alive ping: {current_time}")
            
            # Всегда пытаемся отправить HTTP запрос - никаких проверок переменных окружения
            try:
                await send_keep_alive_request()
                print("✅ Keep-alive HTTP запрос отправлен")
            except Exception as e:
                print(f"❌ Ошибка отправки keep-alive HTTP запроса: {e}")
                # Продолжаем работу даже при ошибке HTTP запроса
                
        except asyncio.CancelledError:
            print("💓 Keep-alive задача отменена")
            break
        except Exception as e:
            print(f"❌ Ошибка в keep-alive задаче: {e}")
            # Продолжаем работу даже при ошибке - keep-alive НЕ должен влиять на бота
            await asyncio.sleep(60)  # Ждем минуту перед следующей попыткой

async def start_keep_alive_task():
    """Запускает keep-alive задачу, если она еще не запущена - НЕЗАВИСИМАЯ ВЕРСИЯ"""
    global keep_alive_task_obj
    
    try:
        if keep_alive_task_obj is None or keep_alive_task_obj.done():
            keep_alive_task_obj = asyncio.create_task(keep_alive_task())
            print("✅ Keep-alive задача запущена (независимая версия)")
    except Exception as e:
        print(f"❌ Ошибка запуска keep-alive задачи: {e}")
        # НЕ поднимаем исключение - keep-alive не должен блокировать запуск бота

def get_cached_locale_manager():
    """Получает кэшированный LocaleManager для оптимизации"""
    global locale_manager_cache
    
    if locale_manager_cache is None:
        try:
            from config.locales.locale_manager import get_global_locale_manager
            locale_manager_cache = get_global_locale_manager()
        except Exception as e:
            print(f"❌ Ошибка получения LocaleManager: {e}")
            return None
    
    return locale_manager_cache

def create_application() -> Application:
    """Create and configure the Telegram application"""
    # Check if all required modules are available
    if not all([BotConfig, PromptManager, AIService, ReceiptAnalysisServiceCompat, 
                MessageHandlers, CallbackHandlers, IngredientStorage]):
        raise ImportError("Required modules are not available")
    
    # Initialize configuration
    config = BotConfig()
    prompt_manager = PromptManager()
    
    # Initialize AI Service Factory for dual model support
    ai_factory = AIServiceFactory(config, prompt_manager)
    
    # Get default AI service (Pro model)
    ai_service = ai_factory.get_default_service()
    analysis_service = ReceiptAnalysisServiceCompat(ai_service, ai_factory)
    
    print(f"🤖 AI Service инициализирован с моделью: {ai_service.get_current_model_info()['name']}")
    print(f"🏭 AIServiceFactory готова для переключения между моделями: {list(ai_factory._services.keys())}")
    
    # LocaleManager уже инициализирован глобально с Firestore instance
    
    # Initialize handlers AFTER LocaleManager is initialized
    message_handlers = MessageHandlers(config, analysis_service)
    callback_handlers = CallbackHandlers(config, analysis_service)
    
    # Initialize ingredient storage with 1 hour cleanup
    ingredient_storage = IngredientStorage(max_age_hours=1)
    
    # Create application
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    
    
    # Initialize empty Google Sheets ingredients - will be loaded on demand
    application.bot_data["google_sheets_ingredients"] = {}
    print("✅ Google Sheets ингредиенты будут загружены по требованию")
    
    # Preload GoogleSheetsManager to initialize Firestore connection
    from services.google_sheets_manager import get_google_sheets_manager
    sheets_manager = get_google_sheets_manager(db)
    print("✅ GoogleSheetsManager предзагружен с Firestore")
    
    # Preload IngredientsManager to initialize Firestore connection
    from services.ingredients_manager import get_ingredients_manager
    ingredients_manager = get_ingredients_manager(db)
    print("✅ IngredientsManager предзагружен с Firestore")
    
    # Preload UserService to initialize user role management
    from services.user_service import get_user_service
    user_service = get_user_service(db)
    print("✅ UserService предзагружен с Firestore")
    
    # Preload GoogleSheetsService to initialize Google Sheets API
    from services.google_sheets_service import GoogleSheetsService
    google_sheets_service = GoogleSheetsService(
        credentials_path=config.GOOGLE_SHEETS_CREDENTIALS if os.path.exists(config.GOOGLE_SHEETS_CREDENTIALS) else None,
        spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
    )
    print("✅ GoogleSheetsService предзагружен")
    
    # Debug Google Sheets configuration
    print(f"🔍 Google Sheets configuration:")
    print(f"  - Credentials path: {config.GOOGLE_SHEETS_CREDENTIALS}")
    print(f"  - Spreadsheet ID: {config.GOOGLE_SHEETS_SPREADSHEET_ID}")
    print(f"  - Service available: {google_sheets_service.is_available()}")
    print(f"  - GOOGLE_APPLICATION_CREDENTIALS_JSON set: {bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))}")
    print(f"  - GOOGLE_SHEETS_CREDENTIALS_JSON set: {bool(os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON'))}")
    
    # Test Google Sheets access
    if google_sheets_service.is_available():
        try:
            # Try to access the spreadsheet to verify credentials
            spreadsheet = google_sheets_service.service.spreadsheets().get(spreadsheetId=config.GOOGLE_SHEETS_SPREADSHEET_ID).execute()
            print(f"✅ Google Sheets access verified - spreadsheet title: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
        except Exception as e:
            print(f"❌ Google Sheets access failed: {e}")
            print(f"💡 This might be due to:")
            print(f"   - Invalid credentials")
            print(f"   - Insufficient permissions")
            print(f"   - Spreadsheet not accessible")
    else:
        print("❌ Google Sheets service not available")
    
    # Подробная отладка credentials
    google_sheets_credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
    if google_sheets_credentials_json:
        try:
            import json
            credentials_info = json.loads(google_sheets_credentials_json)
            print(f"  - NEW Credentials project_id: {credentials_info.get('project_id', 'Не найден')}")
            print(f"  - NEW Credentials client_email: {credentials_info.get('client_email', 'Не найден')}")
            print(f"  - NEW Credentials type: {credentials_info.get('type', 'Не найден')}")
        except Exception as e:
            print(f"  - Ошибка парсинга NEW credentials JSON: {e}")
    else:
        print("  - GOOGLE_SHEETS_CREDENTIALS_JSON не установлена")
        
        # Fallback to old credentials
        google_credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if google_credentials_json:
            try:
                import json
                credentials_info = json.loads(google_credentials_json)
                print(f"  - OLD Credentials project_id: {credentials_info.get('project_id', 'Не найден')}")
                print(f"  - OLD Credentials client_email: {credentials_info.get('client_email', 'Не найден')}")
                print(f"  - OLD Credentials type: {credentials_info.get('type', 'Не найден')}")
            except Exception as e:
                print(f"  - Ошибка парсинга OLD credentials JSON: {e}")
        else:
            print("  - GOOGLE_APPLICATION_CREDENTIALS_JSON также не установлена")
    
    # Проверяем файл credentials
    if os.path.exists(config.GOOGLE_SHEETS_CREDENTIALS):
        print(f"  - Файл credentials существует: ✅")
        try:
            with open(config.GOOGLE_SHEETS_CREDENTIALS, 'r') as f:
                file_content = f.read()
                if file_content.strip():
                    print(f"  - Размер файла: {len(file_content)} символов")
                else:
                    print(f"  - Файл пустой: ❌")
        except Exception as e:
            print(f"  - Ошибка чтения файла: {e}")
    else:
        print(f"  - Файл credentials не существует: ❌")

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", message_handlers.start),
            CommandHandler("reset_language", message_handlers.reset_language),
            CommandHandler("dashboard", message_handlers.dashboard),
            CommandHandler("admin", message_handlers.admin_commands),
            CommandHandler("add_whitelist", message_handlers.add_to_whitelist),
            CommandHandler("remove_whitelist", message_handlers.remove_from_whitelist),
            CommandHandler("list_whitelist", message_handlers.list_whitelist),
            MessageHandler(filters.PHOTO, message_handlers.handle_photo)
        ],
        states={
            config.AWAITING_CORRECTION: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_DASHBOARD: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_LINE_NUMBER: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_line_number_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_FIELD_EDIT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice), 
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_DELETE_LINE_NUMBER: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_delete_line_number_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_TOTAL_EDIT: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_total_edit_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INGREDIENT_MATCHING: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_MANUAL_MATCH: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_ingredient_matching_input),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_SHEET_URL: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handlers._handle_sheet_url_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_SHEET_NAME: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handlers._handle_sheet_name_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_CONFIRM_MAPPING: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.EDIT_MAPPING: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_column_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_COLUMN_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_column_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_SHEET_NAME_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_sheet_name_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_START_ROW_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_start_row_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INGREDIENTS_FILE: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.Document.ALL, message_handlers.handle_ingredients_file_upload),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INGREDIENTS_TEXT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_ingredients_text_upload),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_ADMIN_USERNAME: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_ADMIN_CONFIRM_DELETE: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", message_handlers.start),
            CommandHandler("dashboard", message_handlers.dashboard)
        ],
        per_message=False
    )

    # Add handlersп
    application.add_handler(conv_handler)
    
    # Add separate command handlers that work in any state
    application.add_handler(CommandHandler("start", message_handlers.start))
    application.add_handler(CommandHandler("dashboard", message_handlers.dashboard))
    application.add_handler(CommandHandler("reset_language", message_handlers.reset_language))
    application.add_handler(CommandHandler("switch_model", message_handlers.switch_model))
    application.add_handler(CommandHandler("model_info", message_handlers.model_info))
    
    return application

async def initialize_bot():
    """Initialize the bot application and start background tasks"""
    global application, ingredient_storage, TOKEN, TELEGRAM_API
    
    # Проверяем, не инициализирован ли уже бот
    if application is not None:
        print("⚠️ Бот уже инициализирован, пропускаем повторную инициализацию")
        return
    
    print("🚀 Инициализация бота...")
    
    # Debug: Print all environment variables
    print("🔍 Debug: Environment variables:")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ["TOKEN", "PROJECT", "WEBHOOK", "GOOGLE", "CREDENTIALS"]):
            print(f"  {key}: {'*' * len(value) if value else 'NOT SET'}")
    
    # Check if BOT_TOKEN is available
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN не найден в переменных окружения")
        print("🔍 Available env vars with 'BOT':", [k for k in os.environ.keys() if 'BOT' in k])
        return
    
    TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
    print("✅ BOT_TOKEN найден")
    
    # Create application
    print("🔧 Создаем Telegram application...")
    application = create_application()
    print(f"✅ Application создан: {application}")
    
    # Initialize ingredient storage with 1 hour cleanup
    ingredient_storage = IngredientStorage(max_age_hours=1)
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_files_periodically(ingredient_storage))
    print("✅ Фоновая задача очистки запущена")
    
    # Initialize roles and permissions
    if db:
        try:
            from utils.role_initializer import initialize_roles_and_permissions
            await initialize_roles_and_permissions(db)
            print("✅ Roles and permissions initialized")
        except Exception as e:
            print(f"⚠️ Role initialization failed: {e}")
            # НЕ прерываем инициализацию - роли не критичны для базовой работы
    
    # Start keep-alive task - НЕ блокируем инициализацию бота
    try:
        await start_keep_alive_task()
    except Exception as e:
        print(f"⚠️ Keep-alive задача не запустилась при инициализации бота: {e}")
        # НЕ прерываем инициализацию - keep-alive не критичен
    
    # Initialize the application
    print("🔧 Инициализируем Telegram application...")
    await application.initialize()
    print("✅ Telegram application инициализирован")
    
    # Проверяем, что LocaleManager работает
    try:
        from config.locales.locale_manager import get_global_locale_manager
        lm = get_global_locale_manager()
        print(f"✅ LocaleManager проверен: {lm}")
        if hasattr(lm, 'language_service') and lm.language_service and lm.language_service.db:
            print("✅ LocaleManager подключен к Firestore")
        else:
            print("⚠️ LocaleManager НЕ подключен к Firestore")
    except Exception as e:
        print(f"❌ Ошибка проверки LocaleManager: {e}")
    
    print("🚀 Бот инициализирован для webhook режима")

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    print("🚀 Запуск приложения...")
    
    # Запускаем keep-alive задачу в фоне - НЕ блокируем запуск бота
    try:
        await start_keep_alive_task()
    except Exception as e:
        print(f"⚠️ Keep-alive задача не запустилась: {e}")
        # НЕ прерываем запуск - keep-alive не критичен
    
    try:
        await initialize_bot()
    except Exception as e:
        print(f"❌ Ошибка при инициализации бота: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, если бот не может инициализироваться

@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run - OPTIMIZED"""
    return {
        "status": "ok", 
        "message": "AI Bot is running",
        "application_initialized": application is not None,
        "firestore_connected": db is not None,
        "keep_alive_running": keep_alive_task_obj is not None and not keep_alive_task_obj.done()
    }

@app.post("/set_webhook")
async def set_webhook(request: Request):
    """Manual webhook setup endpoint"""
    try:
        data = await request.json()
        webhook_url = data.get("webhook_url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        if not application:
            raise HTTPException(status_code=500, detail="Bot not initialized")
        
        result = await application.bot.set_webhook(
            url=f"{webhook_url}/webhook",
            drop_pending_updates=True
        )
        
        return {
            "status": "success", 
            "webhook_url": f"{webhook_url}/webhook",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_webhook")
async def get_webhook():
    """Get current webhook info"""
    try:
        if not application:
            raise HTTPException(status_code=500, detail="Bot not initialized")
        
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "webhook_info": webhook_info.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug")
async def debug_info():
    """Debug information endpoint"""
    from config.locales.locale_manager import get_global_locale_manager
    
    locale_manager_status = "Not initialized"
    try:
        lm = get_global_locale_manager()
        locale_manager_status = "Initialized"
        if hasattr(lm, 'language_service') and lm.language_service:
            if lm.language_service.db:
                locale_manager_status += " with Firestore"
            else:
                locale_manager_status += " without Firestore"
    except Exception as e:
        locale_manager_status = f"Error: {str(e)}"
    
    return {
        "application_initialized": application is not None,
        "firestore_connected": db is not None,
        "bot_token_set": TOKEN is not None,
        "locale_manager_status": locale_manager_status,
        "keep_alive_active": True,  # Keep-alive всегда активен, если сервер работает
        "environment_vars": {
            "BOT_TOKEN": "***" if os.getenv("BOT_TOKEN") else "NOT SET",
            "PROJECT_ID": "***" if os.getenv("PROJECT_ID") else "NOT SET",
            "WEBHOOK_URL": "***" if os.getenv("WEBHOOK_URL") else "NOT SET",
            "GOOGLE_APPLICATION_CREDENTIALS_JSON": "***" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") else "NOT SET"
        },
        "google_sheets_config": {
            "credentials_path": "google_sheets_credentials.json",
            "spreadsheet_id": "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI",
            "service_available": google_sheets_service.is_available() if 'google_sheets_service' in locals() else False
        }
    }

@app.get("/keepalive")
async def keepalive_check():
    """Keep-alive check endpoint - OPTIMIZED"""
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "alive",
        "timestamp": current_time,
        "application_initialized": application is not None,
        "keep_alive_running": keep_alive_task_obj is not None and not keep_alive_task_obj.done(),
        "message": "Keep-alive check successful"
    }


@app.post("/webhook")
async def webhook(request: Request):
    """Webhook endpoint for Telegram updates - ASYNC VERSION"""
    try:
        # Get the update from Telegram
        update_data = await request.json()
        
        if not update_data:
            return {"ok": True}
        
        if not application:
            return {"ok": True, "error": "Bot not initialized"}
        
        # ASYNC PROCESSING: Process all updates asynchronously in background
        # This allows multiple updates to be processed in parallel
        try:
            update = Update.de_json(update_data, application.bot)
            
            if not update:
                return {"ok": True}
            
            # КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Запускаем обработку асинхронно в фоне
            # Это позволяет webhook сразу вернуть ответ, а обработка работает параллельно
            asyncio.create_task(application.process_update(update))
            
            # Сразу возвращаем ответ - webhook не блокируется!
            return {"ok": True}
            
        except Exception as e:
            print(f"❌ Ошибка при обработке update: {e}")
            return {"ok": True, "error": f"Processing error: {str(e)}"}
        
    except Exception as e:
        print(f"❌ Ошибка при обработке webhook: {e}")
        return {"ok": True, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)