"""
AI service for receipt analysis using Google Gemini
"""
import json
from typing import Dict, Any
import vertexai
from vertexai.generative_models import GenerativeModel, Part

from config.settings import BotConfig
from config.prompts import PromptManager


class AIService:
    """Service for AI operations using Google Gemini"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager):
        self.config = config
        self.prompt_manager = prompt_manager
        self._initialize_vertex_ai()
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI once at startup using Application Default Credentials (ADC)"""
        import os
        
        # Debug information
        print(f"🔍 Debug: GOOGLE_APPLICATION_CREDENTIALS = {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        print(f"🔍 Debug: GOOGLE_APPLICATION_CREDENTIALS_JSON exists: {bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))}")
        
        # Initialize Vertex AI using ADC (recommended approach for Cloud Run)
        try:
            vertexai.init(project=self.config.PROJECT_ID, location=self.config.LOCATION)
            print("✅ Vertex AI инициализирован с Application Default Credentials (ADC)")
        except Exception as e:
            print(f"❌ Ошибка инициализации Vertex AI с ADC: {e}")
            raise
    
    def analyze_receipt_phase1(self, image_path: str) -> str:
        """
        Phase 1: Analyze receipt image and extract data
        """
        # Vertex AI already initialized in __init__
        model = GenerativeModel(self.config.MODEL_NAME)
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_part = Part.from_data(data=image_data, mime_type="image/jpeg")
        
        print("Отправка запроса в Gemini (Фаза 1: Анализ)...")
        response = model.generate_content([image_part, self.prompt_manager.get_analyze_prompt()])
        
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        print("Ответ от Gemini (Фаза 1):", clean_response)
        return clean_response
    
    def analyze_receipt_phase2(self, final_data: str) -> str:
        """
        Phase 2: Format the analyzed data
        """
        # Vertex AI already initialized in __init__
        model = GenerativeModel(self.config.MODEL_NAME)
        
        print("Отправка запроса в Gemini (Фаза 2: Форматирование)...")
        response = model.generate_content(self.prompt_manager.get_format_prompt() + final_data)
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
    
    def analyze_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        Complete receipt analysis process
        """
        # Phase 1: Extract data from image
        analysis_json_str = self.ai_service.analyze_receipt_phase1(image_path)
        
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
    
    def format_receipt_data(self, data: Dict[str, Any]) -> str:
        """
        Format receipt data for display
        """
        # Convert data to JSON string for formatting
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Phase 2: Format the data
        formatted_text = self.ai_service.analyze_receipt_phase2(json_str)
        
        return formatted_text
