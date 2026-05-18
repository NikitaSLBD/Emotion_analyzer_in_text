from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Database - поддержка как локального, так и Docker окружения
    DATABASE_URL: str = "postgresql://emotion_user:password123@localhost:5432/emotion_app"

    # API
    YOUTUBE_API_KEY: str = "api-key"
    TELEGRAM_API_ID: str = "api-id"
    TELEGRAM_API_HASH: str = "api-hash"
    TELEGRAM_BOT_TOKEN: str = "bot-token"

    # OMNIROUTE
    OMNIROUTE_API_KEY: str = "omniroute-api"
    OMNIROUTE_ENDPOINT: str = "endpoint"
    LLM: str = "claude-haiku-4.5"

    # JWT
    SECRET_KEY: str = "secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        # Ищем .env файл в корне проекта или в директории infrastructure
        env_file_paths = [
            Path(__file__).parent.parent.parent / ".env",  # Корень проекта
            Path(__file__).parent / ".env",  # infrastructure директория
        ]

        # Используем первый найденный .env файл
        for path in env_file_paths:
            if path.exists():
                env_file = path
                break
        else:
            env_file = env_file_paths[0]  # По умолчанию корень проекта

        case_sensitive = False
        extra = "allow"  # Разрешаем дополнительные переменные окружения

settings = Settings()