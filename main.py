"""
Main entry point for the AI Bot application
"""
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

from config.settings import BotConfig, PromptConfig
from services.ai_service import AIService, ReceiptAnalysisService
from handlers.message_handlers import MessageHandlers
from handlers.callback_handlers import CallbackHandlers
# 👇 --- ДОБАВЛЕН ИМПОРТ --- 👇
from poster_handler import get_all_poster_ingredients


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

    # 4. Запускаем бота
    print("Бот запускается...")
    application.run_polling()


if __name__ == "__main__":
    main()
