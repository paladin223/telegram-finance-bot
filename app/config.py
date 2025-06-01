"""
Конфигурация приложения
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Класс конфигурации приложения"""
    
    # Bot settings
    telegram_bot_token: str
    
    # Database settings
    database_url: str
    
    # Environment settings
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Создание конфигурации из переменных окружения"""
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set")
            
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL must be set")
        
        return cls(
            telegram_bot_token=telegram_token,
            database_url=database_url,
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "True").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


# Глобальная конфигурация
config: Optional[Config] = None


def get_config() -> Config:
    """Получение конфигурации"""
    global config
    if config is None:
        config = Config.from_env()
    return config 