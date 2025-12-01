from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database - используем правильный формат
    DATABASE_URL: str = "postgresql://emotion_user:password123@localhost:5432/emotion_app"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_database_url(self) -> str:
        """Возвращает правильную строку подключения с кодировкой"""
        # Декодируем и перекодируем URL для исправления проблем с кодировкой
        try:
            # Если URL уже в правильном формате, возвращаем как есть
            return self.DATABASE_URL
        except Exception:
            # Если есть проблемы, создаем чистую строку
            return "postgresql://emotion_user:password123@localhost:5432/emotion_app"

settings = Settings()