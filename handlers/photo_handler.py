"""
Photo handling for Telegram bot with parallel processing support
"""
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from models.receipt import ReceiptData
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import get_global_locale_manager
from utils.access_control import access_check


class PhotoHandler(BaseMessageHandler):
    """Handler for photo upload and processing with parallel processing support"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.locale_manager = get_global_locale_manager()
        self.max_concurrent_photos = 3  # Maximum number of photos to process simultaneously
        self.processing_photos: Dict[int, Dict[str, Any]] = {}  # Track processing photos by user_id
    
    @access_check
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle single photo upload (backward compatibility)"""
        return await self.handle_single_photo(update, context)
    
    @access_check
    async def handle_single_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle single photo upload - OPTIMIZED VERSION"""
        # Set anchor message (first receipt message)
        self.ui_manager.set_anchor(context, update.message.message_id)
        
        # ALWAYS clear ALL data when uploading new photo to ensure completely fresh start
        self._clear_receipt_data(context)
        print(f"DEBUG: Cleared all data for new receipt upload")
        
        # Send processing message without auto-delete
        processing_text = self.locale_manager.get_text("status.processing_receipt", context)
        if hasattr(update, 'callback_query') and update.callback_query:
            processing_message = await update.callback_query.message.reply_text(processing_text)
        elif hasattr(update, 'message') and update.message:
            processing_message = await update.message.reply_text(processing_text)
        else:
            raise ValueError("Invalid update object")
        
        # Store processing message ID for later deletion
        context.user_data['processing_message_id'] = processing_message.message_id
        
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(self.config.PHOTO_FILE_NAME)

        # ОПТИМИЗАЦИЯ: Обрабатываем фото синхронно для быстрого ответа
        # Убираем асинхронную обработку, которая вызывала таймауты
        try:
            await self._process_photo_optimized(update, context)
        except Exception as e:
            print(f"❌ Ошибка при обработке фото: {e}")
            await self._delete_processing_message(update, context)
            await update.message.reply_text(self.locale_manager.get_text("errors.critical_photo_error", context))
        
        return self.config.AWAITING_CORRECTION
    
    async def _ensure_turbo_mode_loaded(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Загружает turbo_mode из Firestore если не загружен"""
        try:
            # Проверяем, загружен ли уже turbo_mode
            if 'turbo_mode' in context.user_data:
                return
            
            # Получаем user_id
            user_id = update.effective_user.id if update.effective_user else None
            if not user_id:
                print("❌ Не удалось получить user_id для загрузки turbo_mode")
                context.user_data['turbo_mode'] = False
                return
            
            # Импортируем Firestore
            from google.cloud import firestore
            import main
            
            db = main.db
            if not db:
                print("❌ Firestore недоступен для загрузки turbo_mode")
                context.user_data['turbo_mode'] = False
                return
            
            # Загружаем из Firestore
            user_ref = db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                turbo_mode = user_data.get('turbo_mode', False)
                context.user_data['turbo_mode'] = turbo_mode
                print(f"✅ Turbo mode загружен из Firestore: user {user_id}, turbo={turbo_mode}")
            else:
                print(f"ℹ️ Пользователь {user_id} не найден в Firestore, используем turbo=False")
                context.user_data['turbo_mode'] = False
                
        except Exception as e:
            print(f"❌ Ошибка загрузки turbo_mode из Firestore: {e}")
            context.user_data['turbo_mode'] = False
    
    async def _process_photo_optimized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ОПТИМИЗИРОВАННАЯ обработка фото - быстрая и эффективная"""
        try:
            print(f"🔍 {self.locale_manager.get_text('status.starting_analysis', context)}")
            
            # Загружаем TURBO режим из Firestore если не загружен
            await self._ensure_turbo_mode_loaded(update, context)
            
            # Проверяем TURBO режим и настройки OpenCV
            turbo_enabled = context.user_data.get('turbo_mode', False)
            opencv_disabled = getattr(self.config, 'DISABLE_OPENCV_ANALYSIS', False)
            
            if turbo_enabled or opencv_disabled:
                if turbo_enabled:
                    print("🚀 TURBO режим включен - отправляем фото напрямую в Gemini Flash без OpenCV")
                else:
                    print("🔍 OpenCV анализ отключен в настройках - используем упрощенный выбор")
                
                # В TURBO режиме или при отключенном OpenCV используем упрощенный выбор
                chosen_model = self._choose_model_simple()
                opencv_enabled = False
            else:
                print("🔍 TURBO режим выключен - используем быстрый OpenCV анализ")
                # В обычном режиме используем быстрый OpenCV анализ для выбора модели
                chosen_model = await self._choose_model_with_opencv()
                opencv_enabled = True
                print(f"🎯 Выбрана модель: {chosen_model}, OpenCV анализ: {opencv_enabled}")
            
            # Проверяем режим анализа
            if self.config.GEMINI_ANALYSIS_MODE == "debug":
                # Режим отладки - только показываем результат выбора модели
                debug_message = f"🔍 **Режим отладки**: для этого чека выбрана модель **{chosen_model.upper()}**"
                if turbo_enabled:
                    debug_message += "\n🚀 **TURBO режим активен** - OpenCV отключен"
                elif opencv_disabled:
                    debug_message += "\n🔍 **OpenCV отключен в настройках** - используем упрощенный выбор"
                else:
                    debug_message += f"\n🔍 **TURBO режим выключен** - OpenCV анализ: {'включен' if opencv_enabled else 'отключен'}"
                
                # Удаляем сообщение о обработке
                await self._delete_processing_message(update, context)
                
                # Отправляем сообщение с результатом
                await update.message.reply_text(debug_message, parse_mode='Markdown')
                print(f"🔍 Режим отладки: отправлено сообщение с результатом выбора модели")
                return
            
            # Режим production - продолжаем обычную обработку
            print(f"🔍 Режим production: используем модель {chosen_model} для анализа")
            if turbo_enabled:
                print("🚀 TURBO режим: пропускаем OpenCV обработку")
            elif opencv_disabled:
                print("🔍 OpenCV отключен в настройках: используем упрощенный выбор")
            else:
                print(f"🔍 Обычный режим: OpenCV анализ {'включен' if opencv_enabled else 'отключен'}")
            
            # Передаем выбранную модель в сервис анализа
            print(f"🎯 Отправляем запрос в модель: {chosen_model.upper()}")
            analysis_data = await self.analysis_service.analyze_receipt_async(self.config.PHOTO_FILE_NAME, model_type=chosen_model)
            print(f"✅ {self.locale_manager.get_text('status.analysis_completed', context)}")
            
            # Convert to ReceiptData model
            receipt_data = ReceiptData.from_dict(analysis_data)
            print(f"✅ {self.locale_manager.get_text('status.converted_to_receipt_data', context)}")
            
            # Validate and correct data
            is_valid, message = self.validator.validate_receipt_data(receipt_data)
            if not is_valid:
                print(f"Validation warning: {message}")
            
            context.user_data['receipt_data'] = receipt_data
            print(f"✅ {self.locale_manager.get_text('status.data_saved', context)}")
            # Save original data for change tracking
            context.user_data['original_data'] = ReceiptData.from_dict(receipt_data.to_dict())  # Deep copy
            
            # AUTOMATICALLY create ingredient matching table for this receipt
            await self._create_ingredient_matching_for_receipt(update, context, receipt_data)
            
            # Delete processing message after successful analysis
            await self._delete_processing_message(update, context)
            
            # Always show final report with edit button
            await self.show_final_report_with_edit_button(update, context)
            
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            print(f"{self.locale_manager.get_text('errors.json_parsing_error', context)}: {e}")
            # Delete processing message on error
            await self._delete_processing_message(update, context)
            await update.message.reply_text(self.locale_manager.get_text("errors.parsing_error", context))
        
        except Exception as e:
            print(f"{self.locale_manager.get_text('errors.critical_photo_error', context)}: {e}")
            import traceback
            traceback.print_exc()
            # Delete processing message on error
            await self._delete_processing_message(update, context)
            await update.message.reply_text(self.locale_manager.get_text("errors.critical_photo_error", context))
    
    def _choose_model_simple(self) -> str:
        """
        Упрощенный выбор модели без сложного анализа OpenCV
        Использует простые эвристики для быстрого выбора
        """
        try:
            # Получаем размер файла
            import os
            file_size = os.path.getsize(self.config.PHOTO_FILE_NAME)
            
            # Простая эвристика: большие файлы = сложные чеки = Pro модель
            if file_size > 500000:  # > 500KB
                print("🔍 Большой файл (>500KB) - выбираем Pro модель")
                return 'pro'
            
            # Проверяем настройки по умолчанию
            default_model = getattr(self.config, 'DEFAULT_MODEL', 'pro')
            print(f"🔍 Используем модель по умолчанию: {default_model}")
            return default_model
            
        except Exception as e:
            print(f"⚠️ Ошибка при выборе модели: {e}, используем Pro")
            return 'pro'
    
    async def _choose_model_with_opencv(self) -> str:
        """
        БЫСТРЫЙ выбор модели с использованием упрощенного OpenCV анализа
        Анализирует изображение для определения типа текста (печатный/рукописный)
        """
        try:
            print("🔍 Выполняем БЫСТРЫЙ OpenCV анализ для выбора модели...")
            
            # Читаем изображение для анализа
            with open(self.config.PHOTO_FILE_NAME, 'rb') as f:
                image_bytes = f.read()
            
            # Используем УПРОЩЕННУЮ функцию анализа для максимальной скорости
            chosen_model = await self._fast_opencv_analysis(image_bytes)
            print(f"🔍 Быстрый OpenCV анализ завершен, выбрана модель: {chosen_model}")
            
            return chosen_model
            
        except Exception as e:
            print(f"⚠️ Ошибка при быстром OpenCV анализе: {e}, используем упрощенный выбор")
            return self._choose_model_simple()
    
    async def _fast_opencv_analysis(self, image_bytes: bytes) -> str:
        """
        БЫСТРЫЙ OpenCV анализ - только основные проверки для выбора модели
        """
        try:
            # Проверяем доступность OpenCV
            from utils.opencv_lazy_loader import check_opencv_availability
            if not check_opencv_availability():
                print("❌ OpenCV недоступен, используем упрощенный выбор")
                return self._choose_model_simple()
            
            # Используем контекстный менеджер для автоматической загрузки/выгрузки OpenCV
            from utils.opencv_lazy_loader import OpenCVContext
            import numpy as np
            
            with OpenCVContext() as cv2:
                # Декодирование изображения
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    print("❌ Не удалось декодировать изображение")
                    return self._choose_model_simple()
                
                # БЫСТРЫЙ анализ: только основные признаки
                height, width = image.shape[:2]
                
                # 1. Проверяем размер изображения
                if width < 200 or height < 200:
                    print("🔍 Маленькое изображение - выбираем Flash")
                    return 'flash'
                
                # 2. Проверяем соотношение сторон
                aspect_ratio = width / height
                if aspect_ratio < 0.5 or aspect_ratio > 3.0:
                    print("🔍 Необычное соотношение сторон - выбираем Flash")
                    return 'flash'
                
                # 3. БЫСТРАЯ проверка на рукописный текст (упрощенная)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Простая проверка контраста
                mean_brightness = np.mean(gray)
                std_brightness = np.std(gray)
                
                # Если изображение слишком темное или неконтрастное - Flash
                if mean_brightness < 50 or std_brightness < 20:
                    print("🔍 Темное/неконтрастное изображение - выбираем Flash")
                    return 'flash'
                
                # 4. Простая проверка на размытость
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                if laplacian_var < 100:  # Размытое изображение
                    print("🔍 Размытое изображение - выбираем Flash")
                    return 'flash'
                
                # 5. Если все проверки пройдены - выбираем Pro для сложных случаев
                print("🔍 Сложное изображение - выбираем Pro")
                return 'pro'
                
        except Exception as e:
            print(f"❌ Ошибка в быстром OpenCV анализе: {e}")
            return self._choose_model_simple()
    
    async def _process_photo_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Асинхронная обработка фото в фоне - НЕ блокирует webhook"""
        try:
            print(f"🔍 {self.locale_manager.get_text('status.starting_analysis', context)}")
            
            # НОВАЯ ЛОГИКА: Анализ выбора модели
            print("🔍 Анализируем изображение для выбора модели...")
            
            # Читаем изображение для анализа
            with open(self.config.PHOTO_FILE_NAME, 'rb') as f:
                image_bytes = f.read()
            
            # Импортируем оптимизированную функцию анализа с ленивой загрузкой OpenCV
            from utils.receipt_analyzer_optimized import analyze_receipt_and_choose_model
            
            # Анализируем и выбираем модель (OpenCV загружается только здесь)
            chosen_model = await analyze_receipt_and_choose_model(image_bytes)
            print(f"🎯 Выбрана модель: {chosen_model}")
            
            # Выгружаем OpenCV после анализа для освобождения памяти
            try:
                from utils.receipt_analyzer import unload_opencv
                unload_opencv()
            except Exception as e:
                print(f"⚠️ Ошибка при выгрузке OpenCV: {e}")
            
            # Проверяем режим анализа
            if self.config.GEMINI_ANALYSIS_MODE == "debug":
                # Режим отладки - только показываем результат выбора модели
                debug_message = f"🔍 **Режим отладки**: для этого чека выбрана модель **{chosen_model.upper()}**"
                
                # Удаляем сообщение о обработке
                await self._delete_processing_message(update, context)
                
                # Отправляем сообщение с результатом
                await update.message.reply_text(debug_message, parse_mode='Markdown')
                print(f"🔍 Режим отладки: отправлено сообщение с результатом выбора модели")
                return
            
            # Режим production - продолжаем обычную обработку
            print(f"🔍 Режим production: используем модель {chosen_model} для анализа")
            
            # Передаем выбранную модель в сервис анализа
            print(f"🎯 Отправляем запрос в модель: {chosen_model.upper()}")
            analysis_data = await self.analysis_service.analyze_receipt_async(self.config.PHOTO_FILE_NAME, model_type=chosen_model)
            print(f"✅ {self.locale_manager.get_text('status.analysis_completed', context)}")
            
            # Convert to ReceiptData model
            receipt_data = ReceiptData.from_dict(analysis_data)
            print(f"✅ {self.locale_manager.get_text('status.converted_to_receipt_data', context)}")
            
            # Validate and correct data
            is_valid, message = self.validator.validate_receipt_data(receipt_data)
            if not is_valid:
                print(f"Validation warning: {message}")
            
            context.user_data['receipt_data'] = receipt_data
            print(f"✅ {self.locale_manager.get_text('status.data_saved', context)}")
            # Save original data for change tracking
            context.user_data['original_data'] = ReceiptData.from_dict(receipt_data.to_dict())  # Deep copy
            
            # AUTOMATICALLY create ingredient matching table for this receipt
            await self._create_ingredient_matching_for_receipt(update, context, receipt_data)
            
            # Delete processing message after successful analysis
            await self._delete_processing_message(update, context)
            
            # Always show final report with edit button
            await self.show_final_report_with_edit_button(update, context)
            
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
            print(f"{self.locale_manager.get_text('errors.json_parsing_error', context)}: {e}")
            # Delete processing message on error
            await self._delete_processing_message(update, context)
            await update.message.reply_text(self.locale_manager.get_text("errors.parsing_error", context))
        
        except Exception as e:
            print(f"{self.locale_manager.get_text('errors.critical_photo_error', context)}: {e}")
            import traceback
            traceback.print_exc()
            # Delete processing message on error
            await self._delete_processing_message(update, context)
            await update.message.reply_text(self.locale_manager.get_text("errors.critical_photo_error", context))
    
    async def handle_multiple_photos(self, update: Update, context: ContextTypes.DEFAULT_TYPE, photo_messages: List[Message]) -> int:
        """Handle multiple photos with parallel processing"""
        user_id = update.effective_user.id
        
        # Check if user already has photos processing
        if user_id in self.processing_photos:
            await update.message.reply_text(
                self.locale_manager.get_text("errors.photos_already_processing", context)
            )
            return self.config.AWAITING_CORRECTION
        
        # Limit number of photos
        if len(photo_messages) > self.max_concurrent_photos:
            await update.message.reply_text(
                self.locale_manager.get_text("errors.too_many_photos", context, 
                                           max_photos=self.max_concurrent_photos)
            )
            return self.config.AWAITING_CORRECTION
        
        # Set anchor message
        self.ui_manager.set_anchor(context, update.message.message_id)
        
        # Clear existing data
        self._clear_receipt_data(context)
        
        # Initialize processing tracking
        self.processing_photos[user_id] = {
            'total_photos': len(photo_messages),
            'processed_photos': 0,
            'successful_photos': 0,
            'failed_photos': 0,
            'results': [],
            'progress_message': None
        }
        
        try:
            # Send initial progress message
            progress_text = self.locale_manager.get_text("status.processing_multiple_photos", context, 
                                                       total=len(photo_messages), processed=0)
            progress_message = await self.ui_manager.send_temp(update, context, progress_text, duration=60)
            self.processing_photos[user_id]['progress_message'] = progress_message
            
            # Process photos in parallel
            await self._process_photos_parallel(update, context, photo_messages)
            
            # Show final results
            await self._show_multiple_photos_results(update, context)
            
        except Exception as e:
            print(f"Error in handle_multiple_photos: {e}")
            await update.message.reply_text(
                self.locale_manager.get_text("errors.multiple_photos_error", context, error=str(e))
            )
        finally:
            # Clean up processing tracking
            self.processing_photos.pop(user_id, None)
        
        return self.config.AWAITING_CORRECTION
    
    async def _process_photos_parallel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     photo_messages: List[Message]) -> None:
        """Process multiple photos in parallel with progress tracking"""
        user_id = update.effective_user.id
        processing_info = self.processing_photos[user_id]
        
        # Create tasks for parallel processing
        tasks = []
        for i, photo_message in enumerate(photo_messages):
            task = self._process_single_photo_async(update, context, photo_message, i)
            tasks.append(task)
        
        # Process with semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.max_concurrent_photos)
        
        async def process_with_semaphore(task):
            async with semaphore:
                return await task
        
        # Execute all tasks
        results = await asyncio.gather(*[process_with_semaphore(task) for task in tasks], 
                                     return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            processing_info['processed_photos'] += 1
            
            if isinstance(result, Exception):
                processing_info['failed_photos'] += 1
                processing_info['results'].append({
                    'photo_index': i,
                    'success': False,
                    'error': str(result),
                    'receipt_data': None
                })
            else:
                processing_info['successful_photos'] += 1
                processing_info['results'].append({
                    'photo_index': i,
                    'success': True,
                    'error': None,
                    'receipt_data': result
                })
            
            # Update progress
            await self._update_progress_message(update, context, processing_info)
    
    async def _process_single_photo_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                        photo_message: Message, photo_index: int) -> Optional[ReceiptData]:
        """Process a single photo asynchronously"""
        try:
            # Download photo
            photo_file = await photo_message.photo[-1].get_file()
            photo_filename = f"{self.config.PHOTO_FILE_NAME}_{photo_index}"
            await photo_file.download_to_drive(photo_filename)
            
            # Analyze photo
            analysis_data = await self.analysis_service.analyze_receipt_async(photo_filename)
            
            # Convert to ReceiptData
            receipt_data = ReceiptData.from_dict(analysis_data)
            
            # Validate data
            is_valid, message = self.validator.validate_receipt_data(receipt_data)
            if not is_valid:
                print(f"Validation warning for photo {photo_index}: {message}")
            
            return receipt_data
            
        except Exception as e:
            print(f"Error processing photo {photo_index}: {e}")
            raise e
    
    async def _update_progress_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     processing_info: Dict[str, Any]) -> None:
        """Update progress message for multiple photos processing"""
        try:
            progress_text = self.locale_manager.get_text(
                "status.processing_multiple_photos_progress", context,
                total=processing_info['total_photos'],
                processed=processing_info['processed_photos'],
                successful=processing_info['successful_photos'],
                failed=processing_info['failed_photos']
            )
            
            # Update progress message
            if processing_info['progress_message']:
                await processing_info['progress_message'].edit_text(progress_text)
                
        except Exception as e:
            print(f"Error updating progress message: {e}")
    
    async def _show_multiple_photos_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show results of multiple photos processing"""
        user_id = update.effective_user.id
        processing_info = self.processing_photos.get(user_id, {})
        
        if not processing_info:
            return
        
        results = processing_info['results']
        successful_count = processing_info['successful_photos']
        failed_count = processing_info['failed_photos']
        
        # Create results summary
        summary_text = self.locale_manager.get_text(
            "status.multiple_photos_completed", context,
            total=len(results),
            successful=successful_count,
            failed=failed_count
        )
        
        # If we have successful results, show the first one as main result
        successful_results = [r for r in results if r['success']]
        if successful_results:
            # Use the first successful result as the main receipt data
            main_receipt = successful_results[0]['receipt_data']
            context.user_data['receipt_data'] = main_receipt
            context.user_data['original_data'] = ReceiptData.from_dict(main_receipt.to_dict())
            
            # Create ingredient matching for main receipt
            await self._create_ingredient_matching_for_receipt(update, context, main_receipt)
            
            # Show final report
            await self.show_final_report_with_edit_button(update, context)
        else:
            # No successful results
            await update.message.reply_text(
                self.locale_manager.get_text("errors.no_successful_photos", context)
            )
    
    async def handle_media_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE, media_group: List[Message]) -> int:
        """Handle media group (multiple photos sent at once)"""
        # Filter only photo messages
        photo_messages = [msg for msg in media_group if msg.photo]
        
        if not photo_messages:
            await update.message.reply_text(
                self.locale_manager.get_text("errors.no_photos_in_group", context)
            )
            return self.config.AWAITING_CORRECTION
        
        return await self.handle_multiple_photos(update, context, photo_messages)
    
    async def _create_ingredient_matching_for_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, receipt_data: ReceiptData) -> None:
        """Automatically create ingredient matching table for the receipt"""
        try:
            # Get user's personal ingredients from Firestore
            from services.ingredients_manager import get_ingredients_manager
            ingredients_manager = get_ingredients_manager()
            user_ingredients = await ingredients_manager.get_user_ingredients(update.effective_user.id)
            
            if not user_ingredients:
                print("DEBUG: No personal ingredients found for user, skipping automatic matching")
                return
            
            # Convert user ingredients to the format expected by matching service
            # Format: {ingredient_name: ingredient_id} where ID is just the index
            user_ingredients_for_matching = {}
            for i, ingredient_name in enumerate(user_ingredients):
                user_ingredients_for_matching[ingredient_name] = f"user_ingredient_{i}"
            
            print(f"DEBUG: Using {len(user_ingredients_for_matching)} personal ingredients for matching")
            
            # Perform ingredient matching
            matching_result = self.ingredient_matching_service.match_ingredients(receipt_data, user_ingredients_for_matching)
            
            # Save matching result to context
            context.user_data['ingredient_matching_result'] = matching_result
            context.user_data['changed_ingredient_indices'] = set()
            context.user_data['current_match_index'] = 0
            
            # Save to persistent storage
            user_id = update.effective_user.id
            receipt_hash = receipt_data.get_receipt_hash()
            success = self.ingredient_storage.save_matching_result(user_id, matching_result, set(), receipt_hash)
            print(f"DEBUG: Auto-created matching for receipt {receipt_hash}, success: {success}")
            
        except Exception as e:
            print(f"DEBUG: Error creating automatic ingredient matching: {e}")
    
    async def _delete_processing_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Delete processing message if it exists"""
        processing_message_id = context.user_data.get('processing_message_id')
        if processing_message_id:
            try:
                chat_id = update.effective_chat.id
                await context.bot.delete_message(chat_id=chat_id, message_id=processing_message_id)
                print(f"DEBUG: Deleted processing message {processing_message_id}")
            except Exception as e:
                print(f"DEBUG: Failed to delete processing message {processing_message_id}: {e}")
            finally:
                # Remove from context
                context.user_data.pop('processing_message_id', None)

    def _clear_receipt_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all receipt-related data from context"""
        keys_to_clear = [
            'receipt_data', 'original_data', 'line_to_edit', 'field_to_edit',
            'cached_final_report', 'table_message_id', 'edit_menu_message_id',
            'instruction_message_id', 'line_number_instruction_message_id',
            'delete_line_number_instruction_message_id', 'total_edit_instruction_message_id',
            'total_edit_menu_message_id', 'ingredient_matching_result', 'current_match_index',
            'processing_message_id', 'changed_ingredient_indices', 'search_results',
            'position_search_results', 'awaiting_search', 'awaiting_position_search',
            'in_position_selection_mode', 'selected_line_number', 'position_match_search_results',
            'awaiting_ingredient_name_for_position'
        ]
        for key in keys_to_clear:
            context.user_data.pop(key, None)
    
    async def show_final_report_with_edit_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show final report with edit buttons - this is the root menu"""
        print(f"DEBUG: show_final_report_with_edit_button called")
        print(f"DEBUG: Anchor message ID: {context.user_data.get('anchor_message_id')}")
        
        # Clean up all messages except anchor before showing final report
        await self.ui_manager.cleanup_all_except_anchor(update, context)
        
        final_data: ReceiptData = context.user_data.get('receipt_data')
        
        if not final_data:
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("errors.data_not_found", context), duration=5
            )
            return

        try:
            # Automatically update statuses of all elements
            final_data = self.processor.auto_update_all_statuses(final_data)
            context.user_data['receipt_data'] = final_data
            
            # Check if there are errors
            has_errors = not self.processor.check_all_items_confirmed(final_data)
            
            # Create aligned table programmatically based on user's display mode
            from services.user_service import get_user_service
            user_service = get_user_service()
            user_id = update.effective_user.id
            display_mode = await user_service.get_user_display_mode(user_id)
            
            if display_mode == "desktop":
                aligned_table = self.formatter.format_aligned_table_desktop(final_data, context)
            else:
                aligned_table = self.formatter.format_aligned_table_mobile(final_data, context)
            
            # Calculate total sum
            calculated_total = self.formatter.calculate_total_sum(final_data)
            receipt_total = self.text_parser.parse_number_from_text(final_data.grand_total_text)
            
            # Form final report
            final_report = ""
            
            # Add red marker if there are errors
            if has_errors:
                final_report += self.locale_manager.get_text("analysis.errors_found", context)
            
            final_report += f"```\n{aligned_table}\n```\n\n"
            
            if abs(calculated_total - receipt_total) < 0.01:
                final_report += self.locale_manager.get_text("analysis.total_matches", context)
            else:
                difference = abs(calculated_total - receipt_total)
                final_report += self.locale_manager.get_text("analysis.total_mismatch", context).format(difference=self.number_formatter.format_number_with_spaces(difference))
            
            # Save report in cache for quick access
            context.user_data['cached_final_report'] = final_report
            
            # Create buttons
            keyboard = []
            
            # If there are errors, add buttons for fixing problematic lines
            if has_errors:
                fix_buttons = []
                for item in final_data.items:
                    status = item.status
                    
                    # Check calculation mismatch
                    quantity = item.quantity
                    price = item.price
                    total = item.total
                    has_calculation_error = False
                    
                    if quantity is not None and price is not None and total is not None and quantity > 0 and price > 0 and total > 0:
                        expected_total = quantity * price
                        has_calculation_error = abs(expected_total - total) > 0.01
                    
                    # Check if name is unreadable
                    item_name = item.name
                    is_unreadable = item_name == "???" or item_name == "**unrecognized**"
                    
                    # If there are calculation errors, unreadable data or status not confirmed
                    if status != 'confirmed' or has_calculation_error or is_unreadable:
                        fix_buttons.append(InlineKeyboardButton(
                            self.locale_manager.get_text("buttons.fix_line", context).format(line_number=item.line_number),
                            callback_data=f"edit_{item.line_number}"
                        ))
                
                # Distribute fix buttons across 1-3 columns based on quantity
                if fix_buttons:
                    if len(fix_buttons) <= 3:
                        # 1 column for 1-3 buttons
                        for button in fix_buttons:
                            keyboard.append([button])
                    elif len(fix_buttons) <= 6:
                        # 2 columns for 4-6 buttons
                        for i in range(0, len(fix_buttons), 2):
                            row = fix_buttons[i:i+2]
                            if len(row) == 1:
                                row.append(InlineKeyboardButton("", callback_data="noop"))  # Empty button for alignment
                            keyboard.append(row)
                    else:
                        # 3 columns for 7+ buttons
                        for i in range(0, len(fix_buttons), 3):
                            row = fix_buttons[i:i+3]
                            while len(row) < 3:
                                row.append(InlineKeyboardButton("", callback_data="noop"))  # Empty buttons for alignment
                            keyboard.append(row)
            
            # Add line management buttons
            keyboard.append([
                InlineKeyboardButton(self.locale_manager.get_text("buttons.add_row", context), callback_data="add_row"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.delete_row", context), callback_data="delete_row")
            ])
            
            # Add edit line by number button under add/delete buttons
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_line_number", context), callback_data="edit_line_number")])
            
            # Add total edit and reanalysis buttons in one row
            keyboard.append([
                InlineKeyboardButton(self.locale_manager.get_text("buttons.edit_total", context), callback_data="edit_total"),
                InlineKeyboardButton(self.locale_manager.get_text("buttons.reanalyze", context), callback_data="reanalyze")
            ])
            
            # Add Google Sheets upload button
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("buttons.upload_to_google_sheets", context), callback_data="upload_to_google_sheets")])
            
            
            # Add back button (required in every menu)
            keyboard.append([InlineKeyboardButton(self.locale_manager.get_text("buttons.back_to_receipt", context), callback_data="back_to_receipt")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send report with buttons using UI manager (this becomes the single working menu)
            print(f"DEBUG: Sending final report with buttons")
            message = await self.ui_manager.send_menu(update, context, final_report, reply_markup)
            # Save table message ID for subsequent editing
            context.user_data['table_message_id'] = message.message_id
            print(f"DEBUG: Final report sent, message ID: {message.message_id}")
        
        except Exception as e:
            print(f"{self.locale_manager.get_text('errors.report_formation_error', context)}: {e}")
            await self.ui_manager.send_temp(
                update, context, self.locale_manager.get_text("errors.field_edit_error", context).format(error=e), duration=5
            )
