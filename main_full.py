"""
Полная версия с всеми зависимостями для тестирования
"""
import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# FastAPI app
app = FastAPI(title="AI Bot Full", description="Full version with all dependencies for testing")

# Global variables
application = None

async def start_command(update, context):
    """Handle /start command"""
    await update.message.reply_text("Hello! Full AI Bot is working!")

async def message_handler(update, context):
    """Handle text messages"""
    await update.message.reply_text(f"You said: {update.message.text}")

async def initialize_bot():
    """Initialize the bot application"""
    global application
    
    print("🚀 Инициализация полного AI бота...")
    
    # Check if BOT_TOKEN is available
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не найден в переменных окружения")
        return
    
    print("✅ BOT_TOKEN найден")
    
    # Test all imports step by step
    try:
        import numpy as np
        print(f"✅ numpy версия: {np.__version__}")
    except ImportError as e:
        print(f"❌ Ошибка импорта numpy: {e}")
        return
    
    try:
        import pandas as pd
        print(f"✅ pandas версия: {pd.__version__}")
    except ImportError as e:
        print(f"❌ Ошибка импорта pandas: {e}")
        return
    
    try:
        import vertexai
        print("✅ Google AI (vertexai) импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта vertexai: {e}")
        return
    
    try:
        from google.cloud import aiplatform
        print("✅ Google AI (aiplatform) импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта aiplatform: {e}")
        return
    
    try:
        import openpyxl
        print("✅ openpyxl импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта openpyxl: {e}")
        return
    
    # Create application
    application = Application.builder().token(token).concurrent_updates(True).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Initialize the application
    await application.initialize()
    
    print("🚀 Полный AI бот инициализирован")

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
    return {"status": "ok", "message": "AI Bot Full is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/test-imports")
async def test_imports():
    """Test all imports endpoint"""
    results = {}
    
    try:
        import numpy as np
        results["numpy"] = f"✅ {np.__version__}"
    except Exception as e:
        results["numpy"] = f"❌ {e}"
    
    try:
        import pandas as pd
        results["pandas"] = f"✅ {pd.__version__}"
    except Exception as e:
        results["pandas"] = f"❌ {e}"
    
    try:
        import vertexai
        results["vertexai"] = "✅"
    except Exception as e:
        results["vertexai"] = f"❌ {e}"
    
    try:
        from google.cloud import aiplatform
        results["aiplatform"] = "✅"
    except Exception as e:
        results["aiplatform"] = f"❌ {e}"
    
    try:
        import openpyxl
        results["openpyxl"] = "✅"
    except Exception as e:
        results["openpyxl"] = f"❌ {e}"
    
    return {
        "status": "ok" if all("✅" in str(v) for v in results.values()) else "error",
        "imports": results
    }

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
    print(f"Starting full AI bot server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
