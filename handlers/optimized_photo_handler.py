"""
Optimized photo handling for Telegram bot with async processing
"""
import asyncio
import time
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.receipt import ReceiptData
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import get_global_locale_manager
from utils.access_control import access_check
from utils.performance_utils import measure_performance, run_async_task


class OptimizedPhotoHandler(BaseMessageHandler):
    """Optimized photo handler with async processing and timeout prevention"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.processing_photos: Dict[int, Dict[str, Any]] = {}
    
    @access_check
    @measure_performance("photo_handler.handle_photo")
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle photo upload with immediate response"""
        user_id = update.effective_user.id
        
        # Show immediate response
        message = await update.message.reply_text("📸 Получаю фото...")
        
        # Process photo asynchronously
        asyncio.create_task(self._process_photo_async(update, context, message))
        
        return self.config.AWAITING_CORRECTION
    
    async def _process_photo_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, status_message):
        """Process photo asynchronously without blocking"""
        user_id = update.effective_user.id
        
        try:
            # Update status
            await status_message.edit_text("📥 Загружаю фото...")
            
            # Get photo file
            photo_file = await self._get_photo_file_async(update)
            if not photo_file:
                await status_message.edit_text("❌ Ошибка загрузки фото")
                return
            
            # Update status
            await status_message.edit_text("💾 Сохраняю фото...")
            
            # Download photo with timeout
            photo_path = await self._download_photo_async(photo_file)
            if not photo_path:
                await status_message.edit_text("❌ Ошибка сохранения фото")
                return
            
            # Update status
            await status_message.edit_text("🔍 Анализирую фото...")
            
            # Process photo
            result = await self._analyze_photo_async(photo_path, context)
            
            if result:
                await status_message.edit_text("✅ Фото обработано успешно!")
                # Show results
                await self._show_analysis_results(update, context, result)
            else:
                await status_message.edit_text("❌ Ошибка анализа фото")
                
        except Exception as e:
            print(f"❌ Photo processing error: {e}")
            await status_message.edit_text("❌ Произошла ошибка при обработке фото")
    
    async def _get_photo_file_async(self, update: Update) -> Optional[Any]:
        """Get photo file with timeout handling"""
        try:
            photo = update.message.photo[-1]  # Get highest resolution
            photo_file = await asyncio.wait_for(
                photo.get_file(),
                timeout=30  # 30 second timeout
            )
            return photo_file
        except asyncio.TimeoutError:
            print("❌ Photo file download timeout")
            return None
        except Exception as e:
            print(f"❌ Error getting photo file: {e}")
            return None
    
    async def _download_photo_async(self, photo_file) -> Optional[str]:
        """Download photo with timeout handling"""
        try:
            photo_path = self.config.PHOTO_FILE_NAME
            await asyncio.wait_for(
                photo_file.download_to_drive(photo_path),
                timeout=60  # 60 second timeout
            )
            return photo_path
        except asyncio.TimeoutError:
            print("❌ Photo download timeout")
            return None
        except Exception as e:
            print(f"❌ Error downloading photo: {e}")
            return None
    
    async def _analyze_photo_async(self, photo_path: str, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Analyze photo asynchronously"""
        try:
            # This would call your AI analysis service
            # For now, return a mock result
            await asyncio.sleep(2)  # Simulate processing time
            
            return {
                "status": "success",
                "items": ["Молоко", "Хлеб", "Яйца"],
                "total": 150.50
            }
        except Exception as e:
            print(f"❌ Photo analysis error: {e}")
            return None
    
    async def _show_analysis_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: Dict[str, Any]):
        """Show analysis results to user"""
        try:
            # Create results message
            message_text = "🛒 **Результаты анализа:**\n\n"
            for item in result.get("items", []):
                message_text += f"• {item}\n"
            message_text += f"\n💰 **Итого:** {result.get('total', 0)} руб."
            
            # Create keyboard
            keyboard = [
                [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_receipt")],
                [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_receipt")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_receipt")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send results
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"❌ Error showing results: {e}")
    
    @access_check
    async def handle_multiple_photos(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle multiple photo uploads with parallel processing"""
        user_id = update.effective_user.id
        photos = update.message.photo
        
        if not photos:
            await update.message.reply_text("❌ Фото не найдены")
            return self.config.AWAITING_CORRECTION
        
        # Show status
        status_message = await update.message.reply_text(f"📸 Обрабатываю {len(photos)} фото...")
        
        # Process photos in parallel
        tasks = []
        for i, photo in enumerate(photos):
            task = self._process_single_photo_async(photo, i, context)
            tasks.append(task)
        
        # Wait for all photos to be processed
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
            
            await status_message.edit_text(
                f"✅ Обработано {successful} из {len(photos)} фото"
            )
            
        except Exception as e:
            print(f"❌ Multiple photo processing error: {e}")
            await status_message.edit_text("❌ Ошибка обработки фото")
        
        return self.config.AWAITING_CORRECTION
    
    async def _process_single_photo_async(self, photo, index: int, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """Process a single photo asynchronously"""
        try:
            # Get photo file
            photo_file = await asyncio.wait_for(photo.get_file(), timeout=30)
            
            # Download photo
            photo_path = f"temp_photo_{index}.jpg"
            await asyncio.wait_for(
                photo_file.download_to_drive(photo_path),
                timeout=60
            )
            
            # Analyze photo
            result = await self._analyze_photo_async(photo_path, context)
            
            return result or {"status": "error", "message": "Analysis failed"}
            
        except asyncio.TimeoutError:
            return {"status": "error", "message": "Timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
