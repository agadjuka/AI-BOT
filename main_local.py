"""
Main entry point for the AI Bot application - LOCAL DEVELOPMENT VERSION
Uses polling instead of webhook for local development
"""
import logging
import asyncio
import os
from dotenv import load_dotenv
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

# Загружаем переменные окружения из .env файла
load_dotenv()

# Инициализация клиента Firestore
# Этот код будет работать автоматически в Cloud Run
# и при локальной настройке с переменной окружения.
from google.cloud import firestore

# Инициализация клиента Firestore с обработкой ошибок
try:
    # Получаем имя базы данных из переменных окружения
    database_name = os.getenv("FIRESTORE_DATABASE", "default")
    db = firestore.Client(database=database_name)
    print(f"✅ Firestore клиент инициализирован успешно (база: {database_name})")
except Exception as e:
    print(f"❌ Ошибка инициализации Firestore: {e}")
    print("💡 Убедитесь, что переменная GOOGLE_APPLICATION_CREDENTIALS установлена")
    print(f"💡 Текущее значение: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'НЕ УСТАНОВЛЕНО')}")
    db = None

# OpenCV removed for template - not needed for basic bot functionality
opencv_available = False

from config.settings import BotConfig
from config.prompts import PromptManager
from services.ai_service import AIService, ReceiptAnalysisServiceCompat, AIServiceFactory
from handlers.message_handlers import MessageHandlers
from handlers.callback_handlers import CallbackHandlers
from utils.message_sender import MessageSender
# Google Sheets handler removed for template


def safe_start_bot(application: Application, max_retries: int = 3) -> None:
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


# Cleanup function removed for template - not needed for basic bot functionality

def main() -> None:
    """Main function to start the bot"""
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
    
    # Ingredient storage removed for template - not needed for basic bot functionality
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).concurrent_updates(True).build()
    
    # Services removed for template - only basic bot functionality remains
    print("✅ Template mode: Advanced services disabled")

    # Create simple conversation handler for template
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", message_handlers.start),
            CommandHandler("help", message_handlers.help_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text)
        ],
        states={
            # Basic states only for template
        },
        fallbacks=[
            CommandHandler("cancel", message_handlers.start),
            CommandHandler("help", message_handlers.help_command)
        ],
        per_message=False
    )

    # Add handlers
    application.add_handler(conv_handler)
    
    # Add basic command handlers for template
    application.add_handler(CommandHandler("start", message_handlers.start))
    application.add_handler(CommandHandler("help", message_handlers.help_command))
    
    # Role initialization removed for template

    # 4. Запускаем бота
    print("🚀 Бот запускается...")
    
    try:
        safe_start_bot(application)
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
