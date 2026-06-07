from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from App.modules.logger import get_logger
from App.infrastructure.config import settings

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
        # Импортируем модели здесь, чтобы они были зарегистрированы в Base.metadata
        from App.modules import models

        Base.metadata.create_all(bind=engine)
        logger.info("БД создана успешно")
    except Exception as e:
        logger.error(f"Ошибка при создании БД: {str(e)}")
        raise