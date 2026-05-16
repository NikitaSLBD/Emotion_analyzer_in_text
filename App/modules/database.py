from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from Emotion_analyzer_in_text.App.infrastructure.config import settings
from modules.logger import get_logger

logger = get_logger("database")

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("БД создана успешно")
    except Exception as e:
        logger.error(f"Ошибка при создании БД: {str(e)}")
        raise