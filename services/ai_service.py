"""
AI service for basic AI operations using Google Gemini
Template version - simplified for basic bot functionality
"""
import json
import asyncio
import os
from typing import Dict, Any, Optional
import google.generativeai as genai

from config.settings import BotConfig
from config.prompts import PromptManager


class AIService:
    """Service for basic AI operations using Google Gemini - Template version"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager, model_type: str = None):
        self.config = config
        self.prompt_manager = prompt_manager
        self.model_type = model_type or config.DEFAULT_MODEL
        self._model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini AI service"""
        try:
            # Configure Gemini API
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("❌ GEMINI_API_KEY не найден в переменных окружения")
                raise ValueError("GEMINI_API_KEY is required")
            
            genai.configure(api_key=api_key)
            
            # Get model name
            model_name = self.config.get_model_name(self.model_type)
            self._model = genai.GenerativeModel(model_name)
            
            print(f"✅ Gemini AI инициализирован с моделью: {model_name}")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации Gemini AI: {e}")
            raise
    
    def get_current_model_info(self) -> dict:
        """Get information about current model"""
        return {
            "type": self.model_type,
            "name": self.config.get_model_name(self.model_type),
            "available_models": self.config.get_available_models()
        }
    
    async def get_ai_response(self, user_text: str, language: str = "en") -> str:
        """Get AI response for user text"""
        try:
            # Create a simple prompt for basic conversation
            prompt = f"""
You are a helpful AI assistant. Respond to the user's message in a friendly and helpful way.

User message: {user_text}
Language: {language}

Please respond in {language} language.
"""
            
            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self._model.generate_content(prompt)
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Ошибка получения AI ответа: {e}")
            return f"Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже."


class ReceiptAnalysisServiceCompat:
    """
    Compatibility wrapper for basic AI operations
    Template version - simplified for basic bot functionality
    """
    
    def __init__(self, ai_service: AIService, ai_factory=None):
        self.ai_service = ai_service
        self.ai_factory = ai_factory
    
    async def get_ai_response(self, user_text: str, language: str = "en") -> str:
        """Get AI response for user text"""
        return await self.ai_service.get_ai_response(user_text, language)


class AIServiceFactory:
    """Factory for creating AI services - Template version"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager):
        self.config = config
        self.prompt_manager = prompt_manager
        self._services = {}
    
    def get_service(self, model_type: str = None) -> AIService:
        """Get AI service for specified model type"""
        if model_type is None:
            model_type = self.config.DEFAULT_MODEL
        
        model_type = model_type.lower()
        
        # Check cache
        if model_type not in self._services:
            self._services[model_type] = AIService(
                self.config, 
                self.prompt_manager, 
                model_type
            )
            print(f"🏭 Создан новый AI сервис для модели: {model_type.upper()}")
        
        return self._services[model_type]
    
    def get_default_service(self) -> AIService:
        """Get default AI service"""
        return self.get_service()
    
    def close_all_services(self):
        """Close all services"""
        self._services.clear()
        print("🔒 Все AI сервисы закрыты")