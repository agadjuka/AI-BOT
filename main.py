"""
Main entry point for the AI Bot application
"""
import logging
import asyncio
import time
import threading
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

from config.settings import BotConfig, PromptConfig
from services.ai_service import AIService, ReceiptAnalysisService
from handlers.message_handlers import MessageHandlers
from handlers.callback_handlers import CallbackHandlers
from utils.ingredient_storage import IngredientStorage
# 👇 --- ДОБАВЛЕН ИМПОРТ --- 👇
from poster_handler import get_all_poster_ingredients


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

def main() -> None:
    """Main function to start the bot"""
    # 1. Загружаем справочник ингредиентов из Poster
    poster_ingredients_handbook = get_all_poster_ingredients()
    
    # Initialize configuration
    config = BotConfig()
    prompt_config = PromptConfig()
    
    # Initialize services
    ai_service = AIService(config, prompt_config)
    analysis_service = ReceiptAnalysisService(ai_service)
    
    # Initialize handlers
    message_handlers = MessageHandlers(config, analysis_service)
    callback_handlers = CallbackHandlers(config, analysis_service)
    
    # Initialize ingredient storage with 1 hour cleanup
    ingredient_storage = IngredientStorage(max_age_hours=1)
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).concurrent_updates(True).build()
    
    # 3. Сохраняем загруженный справочник в общую память бота
    # Это специальное 'хранилище' данных, доступное во всех частях нашего бота.
    application.bot_data["poster_ingredients"] = poster_ingredients_handbook

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, message_handlers.handle_photo)],
        states={
            config.AWAITING_CORRECTION: [
                CallbackQueryHandler(callback_handlers.handle_correction_choice),
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

    # 4. Запускаем бота с улучшенной обработкой ошибок и автоочисткой
    print("🚀 Бот запускается...")
    print("🧹 Автоочистка файлов сопоставления: каждые 30 минут, файлы старше 1 часа")
    
    # Запускаем фоновый поток для очистки
    cleanup_thread = threading.Thread(target=cleanup_old_files_periodically, args=(ingredient_storage,), daemon=True)
    cleanup_thread.start()
    print("✅ Фоновый поток очистки запущен")
    
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
