from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database - используем правильный формат
    DATABASE_URL: str = "postgresql://emotion_user:password123@localhost:5432/emotion_app"

    # API
    YOUTUBE_API_KEY: str='api-key'
    TELEGRAM_API_ID: str='api-id'
    TELEGRAM_API_HASH: str='api-hash'
    
    # JWT
    SECRET_KEY: str='secret-key'
    ALGORITHM: str='algorithm-type'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_database_url(self) -> str:
        """Возвращает правильную строку подключения с кодировкой"""
        try:
            return self.DATABASE_URL
        except Exception:
            return "postgresql://emotion_user:password123@localhost:5432/emotion_app"

settings = Settings()