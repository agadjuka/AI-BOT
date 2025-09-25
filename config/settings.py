"""
Configuration settings for the AI Bot
"""
import os
from typing import Optional
from .secrets import secrets
from .locales import language_buttons


class BotConfig:
    """Bot configuration settings"""
    
    def __init__(self):
        # Bot settings
        self.BOT_TOKEN: str = secrets.BOT_TOKEN
        self.PHOTO_FILE_NAME: str = "last_photo.jpg"
        
        
        # Google Sheets settings removed for template
        
        # Google Cloud settings
        self.PROJECT_ID: str = secrets.PROJECT_ID
        # Читаем локацию из переменных окружения для Cloud Run
        self.LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-southeast1")  # Сингапур для Flash-модели
        self.LOCATION_GLOBAL: str = "global"  # Global для Pro-модели
        
        # AI Model settings - simplified for template
        self.MODEL_NAME: str = "gemini-2.5-flash"  # Basic model for template
        self.DEFAULT_MODEL: str = "flash"  # Default model type (pro/flash)
        self.MODEL_PRO: str = "gemini-2.5-pro"  # Pro model name
        self.MODEL_FLASH: str = "gemini-2.5-flash"  # Flash model name
        
        # Analysis settings
        self.DISABLE_OPENCV_ANALYSIS: bool = os.getenv("DISABLE_OPENCV_ANALYSIS", "true").lower() == "true"
        self.GEMINI_ANALYSIS_MODE: str = os.getenv("GEMINI_ANALYSIS_MODE", "production")
        
        # Переопределяем локацию из переменных окружения если задана
        if os.getenv("GOOGLE_CLOUD_LOCATION"):
            self.LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
        
        # Basic conversation states for template
        self.AWAITING_INPUT = 1
        
        # Message settings
        self.MAX_MESSAGE_LENGTH = 4096
        self.MESSAGE_DELAY = 0.5
        
        # Language settings - simplified for template
        self.DEFAULT_LANGUAGE = 'en'
    
    def get_model_name(self, model_type: str = None) -> str:
        """Get the model name for template or specific model type"""
        if model_type is None:
            return self.MODEL_NAME
        
        if model_type.lower() == "pro":
            return self.MODEL_PRO
        elif model_type.lower() == "flash":
            return self.MODEL_FLASH
        else:
            return self.MODEL_NAME
    
    def get_location_by_model_type(self, model_type: str) -> str:
        """Get location based on model type"""
        if model_type.lower() == "flash":
            return self.LOCATION  # asia-southeast1
        elif model_type.lower() == "pro":
            return self.LOCATION_GLOBAL  # global
        else:
            return self.LOCATION  # default to flash location
    
    def get_available_models(self) -> list:
        """Get list of available models"""
        return ["pro", "flash"]


# AI prompts moved to config/prompts.py
