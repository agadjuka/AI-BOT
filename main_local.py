"""
Main entry point for the AI Bot application - LOCAL DEVELOPMENT VERSION
Uses polling instead of webhook for local development
"""
import logging
import asyncio
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
import os

# Инициализация клиента Firestore с обработкой ошибок
try:
    db = firestore.Client(database='billscaner')
    print("✅ Firestore клиент инициализирован успешно (база: billscaner)")
except Exception as e:
    print(f"❌ Ошибка инициализации Firestore: {e}")
    print("💡 Убедитесь, что переменная GOOGLE_APPLICATION_CREDENTIALS установлена")
    print(f"💡 Текущее значение: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'НЕ УСТАНОВЛЕНО')}")
    db = None

from config.settings import BotConfig
from config.prompts import PromptManager
from services.ai_service import AIService, ReceiptAnalysisServiceCompat
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
            import time
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
    import time
    while True:
        try:
            time.sleep(1800)  # 30 minutes = 1800 seconds
            ingredient_storage.cleanup_old_files()
            print("🧹 Выполнена очистка старых файлов сопоставления")
        except Exception as e:
            print(f"❌ Ошибка при очистке файлов: {e}")
            # Продолжаем работу даже при ошибке
            time.sleep(60)  # Ждем минуту перед следующей попыткой

def main() -> None:
    """Main function to start the bot"""
    # Initialize configuration
    config = BotConfig()
    prompt_manager = PromptManager()
    
    # Initialize services
    ai_service = AIService(config, prompt_manager)
    analysis_service = ReceiptAnalysisServiceCompat(ai_service)
    
    # КРИТИЧЕСКИ ВАЖНО: Инициализируем LocaleManager ПЕРЕД созданием handlers
    initialize_locale_manager(db)
    
    # Initialize handlers
    message_handlers = MessageHandlers(config, analysis_service)
    callback_handlers = CallbackHandlers(config, analysis_service)
    
    # Initialize message sender for centralized message sending
    # Example usage:
    # message_sender = MessageSender(config)
    # await message_sender.send_success_message(update, context, "Операция выполнена успешно!")
    # await message_sender.send_error_message(update, context, "Произошла ошибка при обработке")
    # await message_sender.send_temp_message(update, context, "Временное сообщение", duration=5)
    
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
        entry_points=[
            CommandHandler("start", message_handlers.start),
            CommandHandler("reset_language", message_handlers.reset_language),
            CommandHandler("dashboard", message_handlers.dashboard),
            MessageHandler(filters.PHOTO, message_handlers.handle_photo)
        ],
        states={
            config.AWAITING_CORRECTION: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),  # Add text handler for search
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_DASHBOARD: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_INPUT: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_LINE_NUMBER: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_line_number_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_FIELD_EDIT: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice), 
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_user_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_DELETE_LINE_NUMBER: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_delete_line_number_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_TOTAL_EDIT: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_total_edit_input),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_INGREDIENT_MATCHING: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_MANUAL_MATCH: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_ingredient_matching_input),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)  # Add photo handler
            ],
            config.AWAITING_SHEET_URL: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handlers._handle_sheet_url_input),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
            config.AWAITING_SHEET_NAME: [
                CommandHandler("dashboard", message_handlers.dashboard),
                MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handlers._handle_sheet_name_input),
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
                MessageHandler(filters.PHOTO, message_handlers.handle_photo)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", message_handlers.start),
            CommandHandler("dashboard", message_handlers.dashboard)
        ],  # Use start as cancel fallback and dashboard as universal access
        per_message=False
    )

    # Add handlers
    application.add_handler(conv_handler)

    # 4. Запускаем бота с улучшенной обработкой ошибок и автоочисткой
    print("🚀 Бот запускается...")
    print("🧹 Автоочистка файлов сопоставления: каждые 30 минут, файлы старше 1 часа")
    
    # Запускаем фоновую задачу для очистки
    import threading
    cleanup_thread = threading.Thread(target=cleanup_old_files_periodically, args=(ingredient_storage,), daemon=True)
    cleanup_thread.start()
    print("✅ Фоновая задача очистки запущена")
    
    try:
        safe_start_bot(application, ingredient_storage)
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("💡 Попробуйте:")
        print("   1. Убедиться, что не запущено других экземпляров бота")
        print("   2. Проверить интернет-соединение")
        print("   3. Перезапустить через несколько минут")


if __name__ == "__main__":
    main()
