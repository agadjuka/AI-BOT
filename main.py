"""
Main entry point for the AI Bot application with webhook support for Cloud Run
"""
import os
import json
import logging
import asyncio
import time
import threading
from flask import Flask, request, jsonify
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

from config.settings import BotConfig
from config.prompts import PromptManager
from services.ai_service import AIService, ReceiptAnalysisService
from handlers.message_handlers import MessageHandlers
from handlers.callback_handlers import CallbackHandlers
from utils.ingredient_storage import IngredientStorage
from utils.message_sender import MessageSender
from google_sheets_handler import get_google_sheets_ingredients


def safe_start_bot(application: Application, ingredient_storage: IngredientStorage, max_retries: int = 3) -> None:
    """Безопасный запуск бота с обработкой конфликтов"""
    for attempt in range(max_retries):
        try:
            print(f"Попытка запуска бота #{attempt + 1}...")
            
            # Сброс webhook перед каждым запуском
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
                print("✅ Webhook сброшен успешно")
            except Exception as e:
                print(f"⚠️ Предупреждение при сбросе webhook: {e}")
            
            # Небольшая задержка перед запуском
            time.sleep(2)
            
            # Запуск бота
            application.run_polling()
            break
            
        except Conflict as e:
            print(f"❌ Конфликт обнаружен (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Увеличиваем время ожидания с каждой попыткой
                print(f"⏳ Ожидание {wait_time} секунд перед следующей попыткой...")
                time.sleep(wait_time)
            else:
                print("❌ Максимальное количество попыток исчерпано. Проверьте, что не запущено других экземпляров бота.")
                raise
                
        except NetworkError as e:
            print(f"🌐 Ошибка сети (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = 3
                print(f"⏳ Ожидание {wait_time} секунд перед повторной попыткой...")
                time.sleep(wait_time)
            else:
                raise
                
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            raise


def cleanup_old_files_periodically(ingredient_storage: IngredientStorage) -> None:
    """Background task to clean up old files every 30 minutes"""
    while True:
        try:
            time.sleep(1800)  # 30 minutes = 1800 seconds
            ingredient_storage.cleanup_old_files()
            print("🧹 Выполнена очистка старых файлов сопоставления")
        except Exception as e:
            print(f"Ошибка при очистке файлов: {e}")

def create_application() -> Application:
    """Create and configure the Telegram application"""
    # Initialize configuration
    config = BotConfig()
    prompt_manager = PromptManager()
    
    # Initialize services
    ai_service = AIService(config, prompt_manager)
    analysis_service = ReceiptAnalysisService(ai_service)
    
    # Initialize handlers
    message_handlers = MessageHandlers(config, analysis_service)
    callback_handlers = CallbackHandlers(config, analysis_service)
    
    # Initialize ingredient storage with 1 hour cleanup
    ingredient_storage = IngredientStorage(max_age_hours=1)
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).concurrent_updates(True).build()
    
    # Initialize empty poster ingredients - will be loaded on demand
    application.bot_data["poster_ingredients"] = {}
    
    # Initialize empty Google Sheets ingredients - will be loaded on demand
    application.bot_data["google_sheets_ingredients"] = {}
    print("✅ Google Sheets ингредиенты будут загружены по требованию")

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, message_handlers.handle_photo)],
        states={
            config.AWAITING_CORRECTION: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),  # Add text handler for search
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_LINE_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_line_number_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_FIELD_EDIT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice), 
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_DELETE_LINE_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_delete_line_number_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_TOTAL_EDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_total_edit_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_INGREDIENT_MATCHING: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_MANUAL_MATCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_ingredient_matching_input),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
        },
        fallbacks=[CommandHandler("cancel", message_handlers.start)],  # Use start as cancel fallback
        per_message=False
    )

    # Add handlers
    application.add_handler(CommandHandler("start", message_handlers.start))
    application.add_handler(conv_handler)
    
    return application

# Global variables for Flask app
app = Flask(__name__)
application = None
ingredient_storage = None

def initialize_bot():
    """Initialize the bot application and start background tasks"""
    global application, ingredient_storage
    
    # Create application
    application = create_application()
    
    # Initialize ingredient storage with 1 hour cleanup
    ingredient_storage = IngredientStorage(max_age_hours=1)
    
    # Start background cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_files_periodically, args=(ingredient_storage,), daemon=True)
    cleanup_thread.start()
    print("✅ Фоновый поток очистки запущен")
    
    # Initialize the application
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.initialize())
    loop.close()
    print("🚀 Бот инициализирован для webhook режима")

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "ok", "message": "AI Bot is running"})

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for Telegram updates"""
    try:
        # Получаем сырые данные для логирования
        data = request.get_data(as_text=True)
        print("Raw payload:", data)  # ЛОГИРУЕМ СЫРОЕ ТЕЛО
        
        # Парсим JSON и создаем Update объект
        update_data = json.loads(data)
        update = Update.de_json(update_data, application.bot)
        
        print(f"📨 Получено обновление: {update.update_id if update else 'None'}")
        
        # Process the update asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        print("✅ Обновление обработано успешно")
        return "ok", 200
    except Exception as e:
        print(f"❌ Ошибка при обработке webhook: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return "error", 500

def main() -> None:
    """Main function to start the Flask app for Cloud Run"""
    global application, ingredient_storage
    
    print("🚀 Запуск AI Bot в webhook режиме для Cloud Run...")
    print("🧹 Автоочистка файлов сопоставления: каждые 30 минут, файлы старше 1 часа")
    
    # Initialize the bot
    initialize_bot()
    
    # Get port from environment (Cloud Run sets this)
    port = int(os.environ.get("PORT", 8080))
    
    print(f"🌐 Запуск веб-сервера на порту {port}")
    print("📡 Webhook endpoint: /webhook")
    print("❤️ Health check endpoint: /")
    
    # Start Flask app
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
