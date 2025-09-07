"""
Configuration settings for the AI Bot
"""
import os
from typing import Optional
from .ingredients import IngredientConfig


class BotConfig:
    """Bot configuration settings"""
    
    def __init__(self):
        # Bot settings
        self.BOT_TOKEN: str = "8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE"
        self.PHOTO_FILE_NAME: str = "last_photo.jpg"
        
        # Poster settings
        self.POSTER_TOKEN: str = "853931:71424838d41a70ee724e07ef6c6f0774"
        
        # Google Sheets settings
        self.GOOGLE_SHEETS_CREDENTIALS: str = "google_sheets_credentials.json"  # Путь к файлу credentials.json
        self.GOOGLE_SHEETS_SPREADSHEET_ID: str = "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"  # ID таблицы Google Sheets
        self.GOOGLE_SHEETS_WORKSHEET_NAME: str = "Лист1"  # Название листа
        
        # Ingredient matching settings - moved to config/ingredients.py
        self.ingredient_config = IngredientConfig()
        
        # Google Cloud settings
        self.PROJECT_ID: str = "just-advice-470905-a3"
        self.LOCATION: str = "us-central1"
        self.MODEL_NAME: str = "gemini-2.5-flash"
        
        # Conversation states
        self.AWAITING_CORRECTION = 0
        self.AWAITING_INPUT = 1
        self.AWAITING_LINE_NUMBER = 2
        self.AWAITING_FIELD_EDIT = 3
        self.AWAITING_DELETE_LINE_NUMBER = 4
        self.AWAITING_TOTAL_EDIT = 5
        self.AWAITING_INGREDIENT_MATCHING = 6
        self.AWAITING_MANUAL_MATCH = 7
        
        # Message settings
        self.MAX_MESSAGE_LENGTH = 4096
        self.MESSAGE_DELAY = 0.5


# AI prompts moved to config/prompts.py

# Poster API token
POSTER_TOKEN = "853931:71424838d41a70ee724e07ef6c6f0774"
