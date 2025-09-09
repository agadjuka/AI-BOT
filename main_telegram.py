"""
Версия с Telegram Bot API для тестирования
"""
import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# FastAPI app
app = FastAPI(title="AI Bot Telegram", description="Telegram Bot version for testing")

# Global variables
application = None

async def start_command(update, context):
    """Handle /start command"""
    await update.message.reply_text("Hello! Bot is working!")

async def message_handler(update, context):
    """Handle text messages"""
    await update.message.reply_text(f"You said: {update.message.text}")

async def initialize_bot():
    """Initialize the bot application"""
    global application
    
    print("🚀 Инициализация Telegram бота...")
    
    # Check if BOT_TOKEN is available
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден в переменных окружения")
        return
    
    print("✅ BOT_TOKEN найден")
    
    # Create application
    application = Application.builder().token(token).concurrent_updates(True).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Initialize the application
    await application.initialize()
    
    print("🚀 Telegram бот инициализирован")

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    try:
        await initialize_bot()
    except Exception as e:
        print(f"❌ Ошибка при инициализации бота: {e}")

@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "ok", "message": "AI Bot Telegram is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook(request: Request):
    """Webhook endpoint for Telegram updates"""
    try:
        print("📨 Получен webhook запрос")
        
        if not application:
            print("❌ Бот не инициализирован")
            return {"ok": True, "error": "Bot not initialized"}
        
        # Get the update from Telegram
        update_data = await request.json()
        print(f"📊 Update data: {update_data}")
        
        if not update_data:
            print("❌ Пустые данные от Telegram")
            return {"ok": True}
        
        update = Update.de_json(update_data, application.bot)
        print(f"📊 Parsed update: {update}")
        
        if not update:
            print("❌ Не удалось распарсить update")
            return {"ok": True}
        
        # Process the update
        await application.process_update(update)
        
        print("✅ Update обработан успешно")
        return {"ok": True}
        
    except Exception as e:
        print(f"❌ Ошибка при обработке webhook: {e}")
        return {"ok": True, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Telegram bot server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
