"""
Скрипт для инициализации базы данных
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from modules.database import init_db, engine
from modules.logger import get_logger

logger = get_logger("init_db")

def main():
    """Основная функция инициализации"""
    try:
        logger.info("Starting database initialization...")
        init_db()
        logger.info("Database initialization completed successfully!")

        from modules.models import User, TextAnalysis
        from modules.database import Base
        tables = Base.metadata.tables.keys()
        logger.info(f"Created tables: {list(tables)}")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()