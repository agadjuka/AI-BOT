"""
AI service for receipt analysis using Google Gemini
"""
import json
import asyncio
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
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
        """Initialize Vertex AI once at startup using Application Default Credentials (ADC)"""
        import os
        
        # Debug information
        print(f"🔍 Debug: GOOGLE_APPLICATION_CREDENTIALS = {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        print(f"🔍 Debug: GOOGLE_APPLICATION_CREDENTIALS_JSON exists: {bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))}")
        
        # Set GOOGLE_APPLICATION_CREDENTIALS if not set and credentials file exists
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            credentials_file = "just-advice-470905-a3-ee25a8712359.json"
            if os.path.exists(credentials_file):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
                print(f"✅ Установлена переменная GOOGLE_APPLICATION_CREDENTIALS: {credentials_file}")
            else:
                print(f"❌ Файл учетных данных не найден: {credentials_file}")
        
        # Initialize Google Generative AI using ADC (recommended approach for Cloud Run)
        try:
            # Configure the API key or use ADC
            genai.configure()
            print("✅ Google Generative AI инициализирован с Application Default Credentials (ADC)")
            
            # Store model name based on model type
            self._model_name = self.config.get_model_name(self.model_type)
            print(f"✅ Модель {self._model_name} ({self.model_type.upper()}) готова к созданию экземпляров")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации Google Generative AI с ADC: {e}")
            raise
    
    def _create_model_instance(self):
        """Create a new model instance for parallel processing"""
        return genai.GenerativeModel(self._model_name)
    
    def _create_isolated_ai_service(self):
        """Create a completely isolated AI service instance for maximum parallelization"""
        from config.settings import BotConfig
        from config.prompts import PromptManager
        
        # Create new instances to avoid any shared state
        config = BotConfig()
        prompt_manager = PromptManager()
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
            connect=10.0,
            read=60.0,
            write=10.0,
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
    
    async def analyze_receipt_phase1(self, image_path: str) -> str:
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
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
            
            # print("Отправка запроса в Gemini (Фаза 1: Анализ) - из пула экземпляров...")  # Отключено для чистоты консоли
            
            # Create a new model instance in the isolated service
            model = isolated_ai_service._create_model_instance()
            print("✅ Модель создана, отправляем запрос...")
            
            # Run the synchronous generate_content in our dedicated thread pool
            loop = asyncio.get_running_loop()
            start_time = time.time()
            response = await loop.run_in_executor(
                self._thread_pool, 
                lambda: model.generate_content([image_part, isolated_ai_service.prompt_manager.get_analyze_prompt()])
            )
            end_time = time.time()
            print(f"⏱️ Время выполнения запроса Gemini: {end_time - start_time:.2f} секунд")
            
            clean_response = response.text.strip().replace("```json", "").replace("```", "")
            # print("Ответ от Gemini (Фаза 1):", clean_response)  # Отключено для чистоты консоли
            
            return clean_response
            
        except Exception as e:
            print(f"❌ Ошибка в analyze_receipt_phase1: {e}")
            raise ValueError(f"Ошибка анализа чека (Фаза 1): {e}")
        finally:
            # Return the service to the pool instead of closing it
            if isolated_ai_service:
                self._return_ai_service_to_pool(isolated_ai_service)
    
    def analyze_receipt_phase1_sync(self, image_path: str) -> str:
        """
        Phase 1: Analyze receipt image and extract data (sync version for backward compatibility)
        Creates a new model instance for parallel processing
        """
        # Create a new model instance for this request to avoid blocking
        model = self._create_model_instance()
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_data
        }
        
        # print("Отправка запроса в Gemini (Фаза 1: Анализ)...")  # Отключено для чистоты консоли
        response = model.generate_content([image_part, self.prompt_manager.get_analyze_prompt()])
        
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        # print("Ответ от Gemini (Фаза 1):", clean_response)  # Отключено для чистоты консоли
        return clean_response
    
    async def analyze_receipt_phase2(self, final_data: str) -> str:
        """
        Phase 2: Format the analyzed data (async version)
        Uses AI service pool for better resource management
        """
        isolated_ai_service = None
        try:
            # Get an AI service instance from the pool
            isolated_ai_service = self._get_ai_service_from_pool()
            
            # print("Отправка запроса в Gemini (Фаза 2: Форматирование) - из пула экземпляров...")  # Отключено для чистоты консоли
            
            # Create a new model instance in the isolated service
            model = isolated_ai_service._create_model_instance()
            
            # Run the synchronous generate_content in our dedicated thread pool
            loop = asyncio.get_running_loop()
            start_time = time.time()
            response = await loop.run_in_executor(
                self._thread_pool,
                lambda: model.generate_content(isolated_ai_service.prompt_manager.get_format_prompt() + final_data)
            )
            end_time = time.time()
            print(f"⏱️ Время выполнения запроса Gemini (Фаза 2): {end_time - start_time:.2f} секунд")
            
            # print("Ответ от Gemini (Фаза 2):", response.text)  # Отключено для чистоты консоли
            
            return response.text
            
        except Exception as e:
            print(f"❌ Ошибка в analyze_receipt_phase2: {e}")
            raise ValueError(f"Ошибка форматирования данных (Фаза 2): {e}")
        finally:
            # Return the service to the pool instead of closing it
            if isolated_ai_service:
                self._return_ai_service_to_pool(isolated_ai_service)
    
    def analyze_receipt_phase2_sync(self, final_data: str) -> str:
        """
        Phase 2: Format the analyzed data (sync version for backward compatibility)
        Creates a new model instance for parallel processing
        """
        # Create a new model instance for this request to avoid blocking
        model = self._create_model_instance()
        
        # print("Отправка запроса в Gemini (Фаза 2: Форматирование)...")  # Отключено для чистоты консоли
        response = model.generate_content(self.prompt_manager.get_format_prompt() + final_data)
        # print("Ответ от Gemini (Фаза 2):", response.text)  # Отключено для чистоты консоли
        return response.text
    
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
    
    async def analyze_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        Complete receipt analysis process (async version)
        """
        try:
            # Phase 1: Extract data from image
            analysis_json_str = await self.ai_service.analyze_receipt_phase1(image_path)
            
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
    
    def analyze_receipt_sync(self, image_path: str) -> Dict[str, Any]:
        """
        Complete receipt analysis process (sync version for backward compatibility)
        """
        # Phase 1: Extract data from image
        analysis_json_str = self.ai_service.analyze_receipt_phase1_sync(image_path)
        
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
        Format receipt data for display (async version)
        """
        try:
            # Convert data to JSON string for formatting
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            
            # Phase 2: Format the data
            formatted_text = await self.ai_service.analyze_receipt_phase2(json_str)
            
            return formatted_text
            
        except Exception as e:
            print(f"❌ Ошибка в format_receipt_data: {e}")
            raise ValueError(f"Ошибка форматирования данных чека: {e}")
    
    def format_receipt_data_sync(self, data: Dict[str, Any]) -> str:
        """
        Format receipt data for display (sync version for backward compatibility)
        """
        # Convert data to JSON string for formatting
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Phase 2: Format the data
        formatted_text = self.ai_service.analyze_receipt_phase2_sync(json_str)
        
        return formatted_text


class ReceiptAnalysisServiceCompat:
    """
    Compatibility wrapper for ReceiptAnalysisService that provides both sync and async methods
    This ensures backward compatibility with existing code
    """
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self._async_service = ReceiptAnalysisService(ai_service)
    
    def analyze_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze receipt - uses sync version for compatibility
        """
        # Always use sync version for compatibility
        return self._async_service.analyze_receipt_sync(image_path)
    
    async def analyze_receipt_async(self, image_path: str) -> Dict[str, Any]:
        """
        Async version of analyze_receipt
        """
        return await self._async_service.analyze_receipt(image_path)
    
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
