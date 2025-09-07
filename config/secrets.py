"""
Секретные данные и токены для AI Bot
Загружает значения из переменных окружения с fallback на значения по умолчанию
"""
import os
from typing import Optional


class SecretsConfig:
    """Конфигурация секретных данных"""
    
    def __init__(self):
        # Bot Token - токен Telegram бота
        self.BOT_TOKEN: str = self._get_env_var(
            "BOT_TOKEN", 
            "8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE"
        )
        
        # Poster Token - токен для API Poster
        self.POSTER_TOKEN: str = self._get_env_var(
            "POSTER_TOKEN", 
            "853931:71424838d41a70ee724e07ef6c6f0774"
        )
        
        # Google Cloud Project ID
        self.PROJECT_ID: str = self._get_env_var(
            "PROJECT_ID", 
            "just-advice-470905-a3"
        )
    
    def _get_env_var(self, env_name: str, default_value: str) -> str:
        """
        Получает значение из переменной окружения с fallback на значение по умолчанию
        
        Args:
            env_name: Имя переменной окружения
            default_value: Значение по умолчанию
            
        Returns:
            Значение из переменной окружения или значение по умолчанию
        """
        return os.getenv(env_name, default_value)
    
    def validate_tokens(self) -> bool:
        """
        Проверяет, что все необходимые токены установлены
        
        Returns:
            True если все токены валидны, False иначе
        """
        required_tokens = [
            ("BOT_TOKEN", self.BOT_TOKEN),
            ("POSTER_TOKEN", self.POSTER_TOKEN),
            ("PROJECT_ID", self.PROJECT_ID)
        ]
        
        for token_name, token_value in required_tokens:
            if not token_value or token_value.strip() == "":
                print(f"Warning: {token_name} is not set or empty")
                return False
        
        return True


# Создаем глобальный экземпляр конфигурации
secrets = SecretsConfig()

# Для обратной совместимости экспортируем токены напрямую
BOT_TOKEN = secrets.BOT_TOKEN
POSTER_TOKEN = secrets.POSTER_TOKEN
PROJECT_ID = secrets.PROJECT_ID
