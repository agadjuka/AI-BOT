"""
Example of using the updated PhotoHandler with parallel processing support
"""
import asyncio
from telegram import Update, Message
from telegram.ext import ContextTypes

from handlers.photo_handler import PhotoHandler
from services.ai_service import AIService
from config.settings import BotConfig
from config.prompts import PromptManager


async def example_single_photo_processing():
    """Example of processing a single photo"""
    # Initialize services
    config = BotConfig()
    prompt_manager = PromptManager()
    ai_service = AIService(config, prompt_manager)
    photo_handler = PhotoHandler(config, ai_service)
    
    # Mock update and context
    update = Update(update_id=1)
    context = ContextTypes.DEFAULT_TYPE()
    
    # Process single photo
    result = await photo_handler.handle_single_photo(update, context)
    print(f"Single photo processing result: {result}")


async def example_multiple_photos_processing():
    """Example of processing multiple photos in parallel"""
    # Initialize services
    config = BotConfig()
    prompt_manager = PromptManager()
    ai_service = AIService(config, prompt_manager)
    photo_handler = PhotoHandler(config, ai_service)
    
    # Mock update and context
    update = Update(update_id=1)
    context = ContextTypes.DEFAULT_TYPE()
    
    # Mock photo messages
    photo_messages = [
        Message(message_id=1, date=None, chat=None, photo=[]),
        Message(message_id=2, date=None, chat=None, photo=[]),
        Message(message_id=3, date=None, chat=None, photo=[])
    ]
    
    # Process multiple photos
    result = await photo_handler.handle_multiple_photos(update, context, photo_messages)
    print(f"Multiple photos processing result: {result}")


async def example_media_group_processing():
    """Example of processing media group (multiple photos sent at once)"""
    # Initialize services
    config = BotConfig()
    prompt_manager = PromptManager()
    ai_service = AIService(config, prompt_manager)
    photo_handler = PhotoHandler(config, ai_service)
    
    # Mock update and context
    update = Update(update_id=1)
    context = ContextTypes.DEFAULT_TYPE()
    
    # Mock media group
    media_group = [
        Message(message_id=1, date=None, chat=None, photo=[]),
        Message(message_id=2, date=None, chat=None, photo=[]),
        Message(message_id=3, date=None, chat=None, photo=[])
    ]
    
    # Process media group
    result = await photo_handler.handle_media_group(update, context, media_group)
    print(f"Media group processing result: {result}")


async def main():
    """Main example function"""
    print("PhotoHandler Parallel Processing Examples")
    print("=" * 50)
    
    # Example 1: Single photo processing
    print("\n1. Single Photo Processing:")
    await example_single_photo_processing()
    
    # Example 2: Multiple photos processing
    print("\n2. Multiple Photos Processing:")
    await example_multiple_photos_processing()
    
    # Example 3: Media group processing
    print("\n3. Media Group Processing:")
    await example_media_group_processing()
    
    print("\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main())
