"""
AI service for receipt analysis using Google Gemini
"""
import json
import asyncio
from typing import Dict, Any, Optional
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import httpx
from httpx import AsyncClient, Limits, Timeout

from config.settings import BotConfig
from config.prompts import PromptManager


class AIService:
    """Service for AI operations using Google Gemini"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager):
        self.config = config
        self.prompt_manager = prompt_manager
        self._http_client: Optional[AsyncClient] = None
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
            credentials_file = "just-advice-470905-a3-32c0b9960b41.json"
            if os.path.exists(credentials_file):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
                print(f"✅ Установлена переменная GOOGLE_APPLICATION_CREDENTIALS: {credentials_file}")
            else:
                print(f"❌ Файл учетных данных не найден: {credentials_file}")
        
        # Initialize Vertex AI using ADC (recommended approach for Cloud Run)
        try:
            vertexai.init(project=self.config.PROJECT_ID, location=self.config.LOCATION)
            print("✅ Vertex AI инициализирован с Application Default Credentials (ADC)")
            
            # Create model instance once during initialization
            self.model = GenerativeModel(self.config.MODEL_NAME)
            print(f"✅ Модель {self.config.MODEL_NAME} создана")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации Vertex AI с ADC: {e}")
            # Try fallback to us-central1 if asia-southeast1 fails
            try:
                print("🔄 Пробуем fallback на us-central1...")
                vertexai.init(project=self.config.PROJECT_ID, location="us-central1")
                self.model = GenerativeModel(self.config.MODEL_NAME)
                print("✅ Vertex AI инициализирован с fallback на us-central1")
            except Exception as e2:
                print(f"❌ Ошибка инициализации Vertex AI с fallback: {e2}")
                raise
    
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
        """Async context manager exit - cleanup HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
    
    async def close(self):
        """Close HTTP client explicitly"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def analyze_receipt_phase1(self, image_path: str) -> str:
        """
        Phase 1: Analyze receipt image and extract data (async version)
        """
        try:
            # Use pre-initialized model from __init__
            with open(image_path, "rb") as f:
                image_data = f.read()
            image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
            
            print("Отправка запроса в Gemini (Фаза 1: Анализ)...")
            
            # Run the synchronous generate_content in a thread pool to avoid blocking
            # Use asyncio.to_thread for Python 3.9+ or run_in_executor for older versions
            try:
                # Modern approach (Python 3.9+)
                response = await asyncio.to_thread(
                    self.model.generate_content, 
                    [image_part, self.prompt_manager.get_analyze_prompt()]
                )
            except AttributeError:
                # Fallback for older Python versions
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.model.generate_content([image_part, self.prompt_manager.get_analyze_prompt()])
                )
            
            clean_response = response.text.strip().replace("```json", "").replace("```", "")
            print("Ответ от Gemini (Фаза 1):", clean_response)
            return clean_response
            
        except Exception as e:
            print(f"❌ Ошибка в analyze_receipt_phase1: {e}")
            raise ValueError(f"Ошибка анализа чека (Фаза 1): {e}")
    
    def analyze_receipt_phase1_sync(self, image_path: str) -> str:
        """
        Phase 1: Analyze receipt image and extract data (sync version for backward compatibility)
        """
        # Use pre-initialized model from __init__
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
        
        print("Отправка запроса в Gemini (Фаза 1: Анализ)...")
        response = self.model.generate_content([image_part, self.prompt_manager.get_analyze_prompt()])
        
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        print("Ответ от Gemini (Фаза 1):", clean_response)
        return clean_response
    
    async def analyze_receipt_phase2(self, final_data: str) -> str:
        """
        Phase 2: Format the analyzed data (async version)
        """
        try:
            # Use pre-initialized model from __init__
            print("Отправка запроса в Gemini (Фаза 2: Форматирование)...")
            
            # Run the synchronous generate_content in a thread pool to avoid blocking
            # Use asyncio.to_thread for Python 3.9+ or run_in_executor for older versions
            try:
                # Modern approach (Python 3.9+)
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    self.prompt_manager.get_format_prompt() + final_data
                )
            except AttributeError:
                # Fallback for older Python versions
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(self.prompt_manager.get_format_prompt() + final_data)
                )
            
            print("Ответ от Gemini (Фаза 2):", response.text)
            return response.text
            
        except Exception as e:
            print(f"❌ Ошибка в analyze_receipt_phase2: {e}")
            raise ValueError(f"Ошибка форматирования данных (Фаза 2): {e}")
    
    def analyze_receipt_phase2_sync(self, final_data: str) -> str:
        """
        Phase 2: Format the analyzed data (sync version for backward compatibility)
        """
        # Use pre-initialized model from __init__
        
        print("Отправка запроса в Gemini (Фаза 2: Форматирование)...")
        response = self.model.generate_content(self.prompt_manager.get_format_prompt() + final_data)
        print("Ответ от Gemini (Фаза 2):", response.text)
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
