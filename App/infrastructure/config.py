from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database - используем правильный формат
    DATABASE_URL: str = "postgresql://emotion_user:password123@localhost:5432/emotion_app"

    # API
    YOUTUBE_API_KEY: str = "api-key"
    TELEGRAM_API_ID: str = "api-id"
    TELEGRAM_API_HASH: str = "api-hash"
    # OMNIROUTE
    OMNIROUTE_API_KEY: str = "omniroute-api"
    OMNIROUTE_ENDPOINT: str = "endpoint"
    LLM: str = "claude-haiku-4.5"
    
    # JWT
    SECRET_KEY: str = "secret-key"
    ALGORITHM: str = "algorithm-type"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        # Указываем абсолютный путь к .env файлу
        env_file = Path(__file__).parent / ".env"
        case_sensitive = False
        

settings = Settings()