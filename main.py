"""
Main entry point for the AI Bot application with webhook support for Cloud Run
Using FastAPI for better performance and modern async support
"""
import os
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
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

# Импорты с обработкой ошибок
try:
    from config.settings import BotConfig
    from config.prompts import PromptManager
    from services.ai_service import AIService, ReceiptAnalysisServiceCompat
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

# Global variables for keep-alive task
keep_alive_task_obj: Optional[asyncio.Task] = None

def get_service_url():
    """Получает URL сервиса из переменных окружения Cloud Run"""
    # Сначала проверяем SERVICE_URL (если установлен вручную)
    service_url = os.getenv("SERVICE_URL")
    if service_url:
        return service_url
    
    # Если SERVICE_URL не установлен, используем известный URL Cloud Run
    return "https://ai-bot-apmtihe4ga-as.a.run.app"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager для FastAPI приложения"""
    # Код, который выполняется при старте
    print("🚀 Запуск приложения...")
    
    # Получаем URL сервиса
    service_url = get_service_url()
    if service_url:
        # Проверяем, взят ли URL по умолчанию
        if os.getenv("SERVICE_URL"):
            print(f"💓 Starting keep-alive ping to {service_url} (из переменной SERVICE_URL)")
        else:
            print(f"💓 Starting keep-alive ping to {service_url} (URL по умолчанию)")
        global keep_alive_task_obj
        keep_alive_task_obj = asyncio.create_task(keep_alive_ping(service_url))
    else:
        print("⚠️ Не удалось определить URL сервиса - keep-alive отключен")
    
    yield
    
    # Код, который выполняется при выключении
    if keep_alive_task_obj and not keep_alive_task_obj.done():
        keep_alive_task_obj.cancel()
        print("💓 Keep-alive task cancelled.")

# FastAPI app
app = FastAPI(title="AI Bot", description="Telegram Bot for receipt processing", lifespan=lifespan)

# Global variables
application: Optional[Application] = None
ingredient_storage: Optional[IngredientStorage] = None
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

async def keep_alive_ping(service_url: str) -> None:
    """Асинхронная функция для отправки keep-alive пингов на собственный URL"""
    print(f"💓 Keep-alive ping запущен для {service_url}")
    
    while True:
        try:
            await asyncio.sleep(300)  # 5 минут = 300 секунд
            
            # Отправляем HTTP-запрос на собственный URL
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{service_url}/health")
                if response.status_code == 200:
                    print("💓 Keep-alive ping sent successfully.")
                else:
                    print(f"⚠️ Keep-alive ping получил статус {response.status_code}")
                    
        except asyncio.CancelledError:
            print("💓 Keep-alive ping задача отменена")
            break
        except Exception as e:
            print(f"❌ Keep-alive ping failed: {e}")
            # Продолжаем работу даже при ошибке
            await asyncio.sleep(60)  # Ждем минуту перед следующей попыткой

async def start_keep_alive_task():
    """Запускает keep-alive задачу, если URL сервиса доступен"""
    global keep_alive_task_obj
    
    # Получаем URL сервиса
    service_url = get_service_url()
    if not service_url:
        print("⚠️ Не удалось определить URL сервиса - keep-alive отключен")
        return
    
    if keep_alive_task_obj is None or keep_alive_task_obj.done():
        keep_alive_task_obj = asyncio.create_task(keep_alive_ping(service_url))
        print(f"✅ Keep-alive задача запущена для {service_url}")

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
    
    # Check if TOKEN is available
    if not TOKEN:
        raise ValueError("BOT_TOKEN is not set")
    
    # Initialize configuration
    config = BotConfig()
    prompt_manager = PromptManager()
    
    # Initialize services
    ai_service = AIService(config, prompt_manager)
    analysis_service = ReceiptAnalysisServiceCompat(ai_service)
    
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
    
    # Preload GoogleSheetsService to initialize Google Sheets API
    from services.google_sheets_service import GoogleSheetsService
    google_sheets_service = GoogleSheetsService(
        credentials_path=config.GOOGLE_SHEETS_CREDENTIALS,
        spreadsheet_id=config.GOOGLE_SHEETS_SPREADSHEET_ID
    )
    print("✅ GoogleSheetsService предзагружен")
    
    # Debug Google Sheets configuration
    print(f"🔍 Google Sheets configuration:")
    print(f"  - Credentials path: {config.GOOGLE_SHEETS_CREDENTIALS}")
    print(f"  - Spreadsheet ID: {config.GOOGLE_SHEETS_SPREADSHEET_ID}")
    print(f"  - Service available: {google_sheets_service.is_available()}")
    print(f"  - GOOGLE_APPLICATION_CREDENTIALS_JSON set: {bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))}")

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", message_handlers.start),
            CommandHandler("reset_language", message_handlers.reset_language),
            CommandHandler("dashboard", message_handlers.dashboard),
            MessageHandler(filters.PHOTO, message_handlers.handle_photo)
        ],
        states={
            config.AWAITING_CORRECTION: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_DASHBOARD: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_LINE_NUMBER: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_line_number_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_FIELD_EDIT: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice), 
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_DELETE_LINE_NUMBER: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
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
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handlers._handle_sheet_url_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_SHEET_NAME: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handlers._handle_sheet_name_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_CONFIRM_MAPPING: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.EDIT_MAPPING: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_column_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_COLUMN_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_column_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_SHEET_NAME_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_sheet_name_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_START_ROW_INPUT: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_start_row_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INGREDIENTS_FILE: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.Document.ALL, message_handlers.handle_ingredients_file_upload),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INGREDIENTS_TEXT: [
                CallbackQueryHandler(callback_handlers.handle_callback_query),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_ingredients_text_upload),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", message_handlers.start),
            CommandHandler("dashboard", message_handlers.dashboard)
        ],
        per_message=False
    )

    # Add handlers
    application.add_handler(conv_handler)
    
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
        if "TOKEN" in key or "PROJECT" in key or "WEBHOOK" in key:
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

@app.get("/health")
async def health_ping():
    """Health ping endpoint для keep-alive запросов"""
    return {"status": "ok"}

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
            return {
                "error": "Bot not initialized",
                "application_initialized": False,
                "webhook_info": None
            }
        
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "webhook_info": webhook_info.to_dict(),
            "application_initialized": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "application_initialized": application is not None,
            "webhook_info": None
        }

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
    """Webhook endpoint for Telegram updates - OPTIMIZED VERSION"""
    try:
        # Get the update from Telegram
        update_data = await request.json()
        
        if not update_data:
            return {"ok": True}
        
        if not application:
            return {"ok": True, "error": "Bot not initialized"}
        
        # Process the update DIRECTLY instead of background processing
        # This eliminates the overhead of asyncio.create_task()
        try:
            update = Update.de_json(update_data, application.bot)
            
            if not update:
                return {"ok": True}
            
            # Process the update directly
            await application.process_update(update)
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