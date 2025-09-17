"""
AI service for receipt analysis using Google Gemini
"""
import json
import asyncio
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import httpx
from httpx import AsyncClient, Limits, Timeout
import threading
from concurrent.futures import ThreadPoolExecutor

from config.settings import BotConfig
from config.prompts import PromptManager


class AIService:
    """Service for AI operations using Google Gemini with parallel processing support"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager, model_type: str = None):
        self.config = config
        self.prompt_manager = prompt_manager
        self.model_type = model_type or config.DEFAULT_MODEL  # Тип модели (pro/flash)
        self._http_client: Optional[AsyncClient] = None
        self._model_name = None  # Store model name instead of model instance
        self._thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="gemini_worker")
        self._ai_service_pool = []  # Pool of AI service instances
        self._pool_lock = threading.Lock()
        self._max_pool_size = 5
        self._initialize_vertex_ai()
        self._initialize_http_client()
    
    def _initialize_vertex_ai(self):
        """Initialize AI services - vertexai for Flash, google.generativeai for Pro"""
        import os
        import json
        import tempfile
        
        # Debug information
        print(f"🔍 Debug: GOOGLE_APPLICATION_CREDENTIALS = {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        print(f"🔍 Debug: GOOGLE_APPLICATION_CREDENTIALS_JSON exists: {bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))}")
        
        # Set GOOGLE_APPLICATION_CREDENTIALS if not set
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            # First try to use GOOGLE_APPLICATION_CREDENTIALS_JSON (for Cloud Run)
            google_credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if google_credentials_json:
                try:
                    # Parse and validate JSON
                    credentials_info = json.loads(google_credentials_json)
                    print(f"🔍 Parsed GOOGLE_APPLICATION_CREDENTIALS_JSON successfully")
                    print(f"  - Project ID: {credentials_info.get('project_id', 'Не найден')}")
                    print(f"  - Client Email: {credentials_info.get('client_email', 'Не найден')}")
                    print(f"  - Type: {credentials_info.get('type', 'Не найден')}")
                    
                    # Create temporary file with credentials
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        f.write(google_credentials_json)
                        temp_credentials_file = f.name
                    
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_credentials_file
                    print(f"✅ Установлена переменная GOOGLE_APPLICATION_CREDENTIALS: {temp_credentials_file}")
                    
                except Exception as e:
                    print(f"❌ Ошибка парсинга GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
                    # Fallback to local file
                    credentials_file = "just-advice-470905-a3-ee25a8712359.json"
                    if os.path.exists(credentials_file):
                        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
                        print(f"✅ Fallback: установлена переменная GOOGLE_APPLICATION_CREDENTIALS: {credentials_file}")
                    else:
                        print(f"❌ Файл учетных данных не найден: {credentials_file}")
            else:
                # Fallback to local file
                credentials_file = "just-advice-470905-a3-ee25a8712359.json"
                if os.path.exists(credentials_file):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
                    print(f"✅ Установлена переменная GOOGLE_APPLICATION_CREDENTIALS: {credentials_file}")
                else:
                    print(f"❌ Файл учетных данных не найден: {credentials_file}")
        
        # Initialize based on model type
        try:
            if self.model_type.lower() == "flash":
                # Flash model uses vertexai with asia-southeast1 (exactly like rollback version)
                location = self.config.get_location_by_model_type("flash")
                try:
                    vertexai.init(project=self.config.PROJECT_ID, location=location)
                    print(f"✅ Vertex AI инициализирован для Flash модели (регион: {location})")
                except Exception as e:
                    print(f"❌ Ошибка инициализации Vertex AI с {location}: {e}")
                    # Try fallback to us-central1 if asia-southeast1 fails
                    try:
                        print("🔄 Пробуем fallback на us-central1...")
                        vertexai.init(project=self.config.PROJECT_ID, location="us-central1")
                        print("✅ Vertex AI инициализирован с fallback на us-central1")
                    except Exception as e2:
                        print(f"❌ Ошибка инициализации Vertex AI с fallback: {e2}")
                        raise
                
                # Store model name
                self._model_name = self.config.get_model_name("flash")
                print(f"✅ Flash модель {self._model_name} готова к созданию экземпляров")
                
            else:
                # Pro model uses google.generativeai with global
                genai.configure()
                print("✅ Google Generative AI инициализирован для Pro модели (регион: global)")
                
                # Store model name
                self._model_name = self.config.get_model_name(self.model_type)
                print(f"✅ Pro модель {self._model_name} готова к созданию экземпляров")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации AI сервиса: {e}")
            raise
    
    def _create_model_instance(self, model_type: str = None):
        """Create a new model instance for parallel processing"""
        if model_type:
            # Use the specified model type
            model_name = self._get_model_name_by_type(model_type)
            actual_model_type = model_type
        else:
            # Use the default model name
            model_name = self._model_name
            actual_model_type = self.model_type
        
        # Flash model uses vertexai (exactly like rollback version)
        if actual_model_type.lower() == "flash":
            return GenerativeModel(model_name)
        else:
            # Pro model uses google.generativeai
            return genai.GenerativeModel(model_name)
    
    def _get_model_name_by_type(self, model_type: str) -> str:
        """Get model name by type (pro or flash)"""
        from config.settings import BotConfig
        config = BotConfig()
        return config.get_model_name(model_type)
    
    def _create_isolated_ai_service(self):
        """Create a completely isolated AI service instance for maximum parallelization"""
        from config.settings import BotConfig
        from config.prompts import PromptManager
        
        # Create new instances to avoid any shared state
        config = BotConfig()
        prompt_manager = PromptManager()
        # Use the same model type as the current service
        return AIService(config, prompt_manager, self.model_type)
    
    def _get_ai_service_from_pool(self):
        """Get an AI service instance from the pool or create a new one"""
        with self._pool_lock:
            if self._ai_service_pool:
                return self._ai_service_pool.pop()
            else:
                return self._create_isolated_ai_service()
    
    def _return_ai_service_to_pool(self, ai_service):
        """Return an AI service instance to the pool"""
        with self._pool_lock:
            if len(self._ai_service_pool) < self._max_pool_size:
                self._ai_service_pool.append(ai_service)
            else:
                # Pool is full, cleanup the service
                asyncio.create_task(ai_service.close())
    
    def switch_model(self, model_type: str):
        """Переключить тип модели (pro/flash)"""
        if model_type.lower() in ["pro", "flash"]:
            self.model_type = model_type.lower()
            self._model_name = self.config.get_model_name(self.model_type)
            print(f"🔄 Переключено на модель: {self._model_name} ({self.model_type.upper()})")
        else:
            print(f"❌ Неизвестный тип модели: {model_type}. Доступные: pro, flash")
    
    def get_current_model_info(self) -> dict:
        """Получить информацию о текущей модели"""
        return {
            "type": self.model_type,
            "name": self._model_name,
            "available_models": self.config.get_available_models()
        }
    
    def _initialize_http_client(self):
        """Initialize HTTP client with connection pooling"""
        # Connection pooling configuration
        limits = Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        
        timeout = Timeout(
            connect=5.0,   # Быстрое подключение
            read=120.0,    # Достаточно для Gemini (2 минуты)
            write=5.0,     # Быстрая запись
            pool=5.0
        )
        
        self._http_client = AsyncClient(
            limits=limits,
            timeout=timeout,
            headers={
                'User-Agent': 'AI-Bot/1.0',
                'Content-Type': 'application/json'
            }
        )
        print("✅ HTTP client с connection pooling инициализирован")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup HTTP client and thread pool"""
        if self._http_client:
            await self._http_client.aclose()
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
    
    async def close(self):
        """Close HTTP client, thread pool and AI service pool explicitly"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None
        
        # Cleanup AI service pool
        with self._pool_lock:
            for ai_service in self._ai_service_pool:
                await ai_service.close()
            self._ai_service_pool.clear()
    
    async def analyze_receipt_phase1(self, image_path: str, model_type: str = None) -> str:
        """
        Phase 1: Analyze receipt image and extract data (async version)
        Uses AI service pool for better resource management
        """
        isolated_ai_service = None
        try:
            # Get an AI service instance from the pool
            isolated_ai_service = self._get_ai_service_from_pool()
            
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Determine model type for proper image part creation
            actual_model_type = model_type or isolated_ai_service.model_type
            
            if actual_model_type.lower() == "flash":
                # Flash model uses vertexai Part (exactly like rollback version)
                image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
            else:
                # Pro model uses google.generativeai format
                image_part = {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            
            # print("Отправка запроса в Gemini (Фаза 1: Анализ) - из пула экземпляров...")  # Отключено для чистоты консоли
            
            # Create a new model instance in the isolated service with specified model type
            model = isolated_ai_service._create_model_instance(model_type)
            model_name = isolated_ai_service._get_model_name_by_type(model_type) if model_type else isolated_ai_service._model_name
            print(f"✅ Модель создана: {model_name} ({model_type or 'default'}), отправляем запрос...")
            
            # Run the synchronous generate_content in our dedicated thread pool
            loop = asyncio.get_running_loop()
            start_time = time.time()
            
            if actual_model_type.lower() == "flash":
                # Flash model uses vertexai format (exactly like rollback version)
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._thread_pool, 
                        lambda: model.generate_content([image_part, isolated_ai_service.prompt_manager.get_analyze_prompt()])
                    ),
                    timeout=120.0  # 2 минуты для Gemini
                )
            else:
                # Pro model uses google.generativeai format
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._thread_pool, 
                        lambda: model.generate_content([image_part, isolated_ai_service.prompt_manager.get_analyze_prompt()])
                    ),
                    timeout=120.0  # 2 минуты для Gemini
                )
            end_time = time.time()
            print(f"⏱️ Время выполнения запроса Gemini: {end_time - start_time:.2f} секунд")
            
            clean_response = response.text.strip().replace("```json", "").replace("```", "")
            # print("Ответ от Gemini (Фаза 1):", clean_response)  # Отключено для чистоты консоли
            
            return clean_response
            
        except asyncio.TimeoutError:
            print(f"⏰ Таймаут Gemini запроса (120 секунд)")
            raise ValueError("Таймаут анализа чека - Gemini не ответил за 2 минуты")
        except Exception as e:
            print(f"❌ Ошибка в analyze_receipt_phase1: {e}")
            raise ValueError(f"Ошибка анализа чека (Фаза 1): {e}")
        finally:
            # Return the service to the pool instead of closing it
            if isolated_ai_service:
                self._return_ai_service_to_pool(isolated_ai_service)
    
    def analyze_receipt_phase1_sync(self, image_path: str, model_type: str = None) -> str:
        """
        Phase 1: Analyze receipt image and extract data (sync version for backward compatibility)
        Creates a new model instance for parallel processing
        """
        # Create a new model instance for this request to avoid blocking
        model = self._create_model_instance(model_type)
        model_name = self._get_model_name_by_type(model_type) if model_type else self._model_name
        print(f"✅ Модель создана (sync): {model_name} ({model_type or 'default'}), отправляем запрос...")
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Determine model type for proper image part creation
        actual_model_type = model_type or self.model_type
        
        if actual_model_type.lower() == "flash":
            # Flash model uses vertexai Part (exactly like rollback version)
            image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
        else:
            # Pro model uses google.generativeai format
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
        
        # print("Отправка запроса в Gemini (Фаза 1: Анализ)...")  # Отключено для чистоты консоли
        response = model.generate_content([image_part, self.prompt_manager.get_analyze_prompt()])
        
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        # print("Ответ от Gemini (Фаза 1):", clean_response)  # Отключено для чистоты консоли
        return clean_response
    
    
    def parse_receipt_data(self, json_str: str) -> Dict[str, Any]:
        """
        Parse JSON response from AI analysis
        """
        try:
            data = json.loads(json_str)
            
            # Preserve original price values by converting them back to strings
            # This prevents loss of decimal places during JSON parsing
            if 'items' in data:
                for item in data['items']:
                    if 'price' in item and item['price'] is not None:
                        # Convert price back to string to preserve decimal places
                        item['price'] = str(item['price'])
                    if 'quantity' in item and item['quantity'] is not None:
                        # Convert quantity back to string to preserve decimal places
                        item['quantity'] = str(item['quantity'])
                    if 'total' in item and item['total'] is not None:
                        # Convert total back to string to preserve decimal places
                        item['total'] = str(item['total'])
            
            return data
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON от Gemini: {e}")
            raise ValueError(f"Не удалось распарсить JSON ответ от AI: {e}")


class ReceiptAnalysisService:
    """Service for receipt analysis operations"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def analyze_receipt(self, image_path: str, model_type: str = None) -> Dict[str, Any]:
        """
        Complete receipt analysis process (async version) - single request like rollback version
        """
        try:
            # Single request to extract data from image (no phases)
            analysis_json_str = await self.ai_service.analyze_receipt_phase1(image_path, model_type)
            
            # Parse the JSON response
            data = self.ai_service.parse_receipt_data(analysis_json_str)
            
            # Check if data is a list (items only) or dict (with items key)
            if isinstance(data, list):
                # If data is a list, wrap it in a dict with 'items' key
                return {'items': data, 'grand_total_text': '0'}
            elif isinstance(data, dict) and 'items' in data:
                # If data is already a dict with 'items' key, return as is
                return data
            else:
                # If data is a dict but doesn't have 'items' key, try to find items
                # This handles cases where AI returns different structure
                if 'items' in data:
                    return data
                else:
                    # If no items key found, assume the whole dict is items
                    return {'items': [data], 'grand_total_text': '0'}
                    
        except Exception as e:
            print(f"❌ Ошибка в analyze_receipt: {e}")
            raise ValueError(f"Ошибка анализа чека: {e}")
    
    def analyze_receipt_sync(self, image_path: str, model_type: str = None) -> Dict[str, Any]:
        """
        Complete receipt analysis process (sync version for backward compatibility) - single request like rollback version
        """
        # Single request to extract data from image (no phases)
        analysis_json_str = self.ai_service.analyze_receipt_phase1_sync(image_path, model_type)
        
        # Parse the JSON response
        data = self.ai_service.parse_receipt_data(analysis_json_str)
        
        # Check if data is a list (items only) or dict (with items key)
        if isinstance(data, list):
            # If data is a list, wrap it in a dict with 'items' key
            return {'items': data, 'grand_total_text': '0'}
        elif isinstance(data, dict) and 'items' in data:
            # If data is already a dict with 'items' key, return as is
            return data
        else:
            # If data is a dict but doesn't have 'items' key, try to find items
            # This handles cases where AI returns different structure
            if 'items' in data:
                return data
            else:
                # If no items key found, assume the whole dict is items
                return {'items': [data], 'grand_total_text': '0'}
    
    async def format_receipt_data(self, data: Dict[str, Any]) -> str:
        """
        Format receipt data for display (async version) - no phases, direct formatting
        """
        try:
            # Direct formatting without AI - just format the data as table
            return self._format_receipt_data_direct(data)
            
        except Exception as e:
            print(f"❌ Ошибка в format_receipt_data: {e}")
            raise ValueError(f"Ошибка форматирования данных чека: {e}")
    
    def format_receipt_data_sync(self, data: Dict[str, Any]) -> str:
        """
        Format receipt data for display (sync version for backward compatibility) - no phases, direct formatting
        """
        # Direct formatting without AI - just format the data as table
        return self._format_receipt_data_direct(data)
    
    def _format_receipt_data_direct(self, data: Dict[str, Any]) -> str:
        """
        Direct formatting of receipt data as table (no AI phases)
        """
        try:
            items = data.get('items', [])
            if not items:
                return "❌ Нет данных для отображения"
            
            # Create table header
            table = "#| Item       |Qty | Price     |   Total |\n"
            table += "------------------------------------------------\n"
            
            # Add items
            for i, item in enumerate(items, 1):
                name = item.get('name', '---')
                quantity = item.get('quantity', '---')
                price = item.get('price', '---')
                total = item.get('total', '---')
                status = item.get('status', 'OK')
                
                # Format status
                if status == 'confirmed':
                    status_display = 'OK'
                elif status == 'error':
                    status_display = 'ERR'
                elif status == 'needs_review':
                    status_display = 'WARN'
                else:
                    status_display = 'OK'
                
                # Format numbers with spaces for thousands
                if isinstance(price, (int, float)) and price != '---':
                    price_str = f"{price:,.0f}".replace(',', ' ')
                else:
                    price_str = str(price)
                
                if isinstance(total, (int, float)) and total != '---':
                    total_str = f"{total:,.0f}".replace(',', ' ')
                else:
                    total_str = str(total)
                
                table += f"{i}| {name[:10]:<10} |{str(quantity):<3} | {price_str:<9} | {total_str:<7} | {status_display}\n"
            
            # Add total
            grand_total = data.get('grand_total_text', '0')
            table += f"\nTOTAL: {grand_total}"
            
            return table
            
        except Exception as e:
            print(f"❌ Ошибка в _format_receipt_data_direct: {e}")
            return f"❌ Ошибка форматирования: {e}"


class ReceiptAnalysisServiceCompat:
    """
    Compatibility wrapper for ReceiptAnalysisService that provides both sync and async methods
    This ensures backward compatibility with existing code
    """
    
    def __init__(self, ai_service: AIService, ai_factory=None):
        self.ai_service = ai_service
        self.ai_factory = ai_factory  # Добавляем фабрику для переключения моделей
        self._async_service = ReceiptAnalysisService(ai_service)
    
    def analyze_receipt(self, image_path: str, model_type: str = None) -> Dict[str, Any]:
        """
        Analyze receipt - uses sync version for compatibility
        """
        # Если указан тип модели и есть фабрика, используем правильный сервис
        if model_type and self.ai_factory:
            print(f"🔄 Переключаемся на модель: {model_type.upper()}")
            target_ai_service = self.ai_factory.get_service(model_type)
            target_async_service = ReceiptAnalysisService(target_ai_service)
            return target_async_service.analyze_receipt_sync(image_path, model_type)
        else:
            # Используем текущий сервис
            return self._async_service.analyze_receipt_sync(image_path, model_type)
    
    async def analyze_receipt_async(self, image_path: str, model_type: str = None) -> Dict[str, Any]:
        """
        Async version of analyze_receipt
        """
        # Если указан тип модели и есть фабрика, используем правильный сервис
        if model_type and self.ai_factory:
            print(f"🔄 Переключаемся на модель (async): {model_type.upper()}")
            target_ai_service = self.ai_factory.get_service(model_type)
            target_async_service = ReceiptAnalysisService(target_ai_service)
            return await target_async_service.analyze_receipt(image_path, model_type)
        else:
            # Используем текущий сервис
            return await self._async_service.analyze_receipt(image_path, model_type)
    
    def format_receipt_data(self, data: Dict[str, Any]) -> str:
        """
        Format receipt data - automatically chooses sync or async based on context
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, we need to run the async version
            if loop.is_running():
                # We're in an async context, but this is a sync method
                # Run the sync version in a thread to avoid blocking
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._async_service.format_receipt_data_sync, data)
                    return future.result()
            else:
                # No event loop running, safe to use sync version directly
                return self._async_service.format_receipt_data_sync(data)
        except RuntimeError:
            # No event loop running, safe to use sync version directly
            return self._async_service.format_receipt_data_sync(data)
    
    async def format_receipt_data_async(self, data: Dict[str, Any]) -> str:
        """
        Async version of format_receipt_data
        """
        return await self._async_service.format_receipt_data(data)


class AIServiceFactory:
    """Фабрика для создания AI сервисов с разными моделями"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager):
        self.config = config
        self.prompt_manager = prompt_manager
        self._services = {}  # Кэш сервисов по типам моделей
    
    def get_service(self, model_type: str = None) -> AIService:
        """Получить AI сервис для указанного типа модели"""
        if model_type is None:
            model_type = self.config.DEFAULT_MODEL
        
        model_type = model_type.lower()
        
        # Проверяем кэш
        if model_type not in self._services:
            self._services[model_type] = AIService(
                self.config, 
                self.prompt_manager, 
                model_type
            )
            print(f"🏭 Создан новый AI сервис для модели: {model_type.upper()}")
        
        return self._services[model_type]
    
    def get_pro_service(self) -> AIService:
        """Получить AI сервис для Pro модели"""
        return self.get_service("pro")
    
    def get_flash_service(self) -> AIService:
        """Получить AI сервис для Flash модели"""
        return self.get_service("flash")
    
    def get_default_service(self) -> AIService:
        """Получить AI сервис по умолчанию (Pro)"""
        return self.get_service()
    
    def close_all_services(self):
        """Закрыть все сервисы"""
        for service in self._services.values():
            asyncio.create_task(service.close())
        self._services.clear()
        print("🔒 Все AI сервисы закрыты")
