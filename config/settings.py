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
        
        
        # Google Sheets settings
        self.GOOGLE_SHEETS_CREDENTIALS: str = "just-advice-470905-a3-ee25a8712359.json"  # Путь к файлу credentials.json
        self.GOOGLE_SHEETS_SPREADSHEET_ID: str = "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"  # ID таблицы Google Sheets
        self.GOOGLE_SHEETS_WORKSHEET_NAME: str = "Лист1"  # Название листа
        
        # Ingredient matching settings - now handled by personal ingredients from Firestore
        
        # Google Cloud settings
        self.PROJECT_ID: str = secrets.PROJECT_ID
        self.LOCATION: str = "asia-southeast1"  # Сингапур для Flash-модели как в откатной версии
        self.LOCATION_GLOBAL: str = "global"  # Global для Pro-модели
        
        # AI Model settings - поддержка двух моделей
        self.MODEL_PRO: str = "gemini-2.5-pro"  # Основная модель (Pro)
        self.MODEL_FLASH: str = "gemini-2.5-flash"  # Быстрая модель (Flash)
        
        # Читаем настройки из переменных окружения для Cloud Run
        self.DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "pro")  # По умолчанию Pro
        self.MODEL_NAME: str = self.MODEL_PRO  # Для обратной совместимости
        
        # Режим анализа Gemini - debug или production
        self.GEMINI_ANALYSIS_MODE: str = os.getenv("GEMINI_ANALYSIS_MODE", "production")
        
        # Оптимизация производительности - отключить сложный анализ OpenCV
        self.DISABLE_OPENCV_ANALYSIS: bool = os.getenv("DISABLE_OPENCV_ANALYSIS", "true").lower() == "true"
        
        # Переопределяем локацию из переменных окружения если задана
        if os.getenv("GOOGLE_CLOUD_LOCATION"):
            self.LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
        
        # Conversation states
        self.AWAITING_CORRECTION = 0
        self.AWAITING_INPUT = 1
        self.AWAITING_LINE_NUMBER = 2
        self.AWAITING_FIELD_EDIT = 3
        self.AWAITING_DELETE_LINE_NUMBER = 4
        self.AWAITING_TOTAL_EDIT = 5
        self.AWAITING_INGREDIENT_MATCHING = 6
        self.AWAITING_MANUAL_MATCH = 7
        self.AWAITING_DASHBOARD = 8
        
        # Google Sheets management states
        self.AWAITING_SHEET_URL = 9
        self.AWAITING_SHEET_NAME = 10
        self.AWAITING_CONFIRM_MAPPING = 11
        self.EDIT_MAPPING = 12
        self.AWAITING_COLUMN_INPUT = 13
        self.AWAITING_SHEET_NAME_INPUT = 14
        self.AWAITING_START_ROW_INPUT = 15
        
        # Ingredients management states
        self.AWAITING_INGREDIENTS_FILE = 16
        self.AWAITING_INGREDIENTS_TEXT = 17
        
        # Admin panel states
        self.AWAITING_ADMIN_USERNAME = 18
        self.AWAITING_ADMIN_CONFIRM_DELETE = 19
        
        # Message settings
        self.MAX_MESSAGE_LENGTH = 4096
        self.MESSAGE_DELAY = 0.5
        
        # Language settings
        self.SUPPORTED_LANGUAGES = ['ru', 'en', 'id']
        self.DEFAULT_LANGUAGE = 'en'
        self.LANGUAGE_COLLECTION_NAME = 'user_languages'
        
        # Admin settings
        self.ADMIN_TELEGRAM_ID: int = 261617302
    
    def get_model_name(self, model_type: str = None) -> str:
        """Получить имя модели по типу"""
        if model_type is None:
            model_type = self.DEFAULT_MODEL
        
        if model_type.lower() == "pro":
            return self.MODEL_PRO
        elif model_type.lower() == "flash":
            return self.MODEL_FLASH
        else:
            return self.MODEL_PRO  # По умолчанию Pro
    
    def get_available_models(self) -> dict:
        """Получить список доступных моделей"""
        return {
            "pro": self.MODEL_PRO,
            "flash": self.MODEL_FLASH
        }
    
    def get_location_by_model_type(self, model_type: str = None) -> str:
        """Получить локацию по типу модели"""
        if model_type is None:
            model_type = self.DEFAULT_MODEL
        
        if model_type.lower() == "flash":
            return self.LOCATION  # asia-southeast1 для Flash
        else:
            return self.LOCATION_GLOBAL  # global для Pro


# AI prompts moved to config/prompts.py
