#!/usr/bin/env python3
"""
Скрипт для проверки подключения к PostgreSQL
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from modules.config import settings
from modules.logger import get_logger

logger = get_logger("test_postgres")

def test_postgresql_connection():
    """Тестирует подключение к PostgreSQL"""
    try:
        # Парсим URL подключения
        db_url = settings.DATABASE_URL
        print(f"🔧 Testing connection to: {db_url}")
        
        # Подключаемся к PostgreSQL
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Создаем курсор
        cur = conn.cursor()
        
        # Проверяем версию PostgreSQL
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ PostgreSQL version: {version[0]}")
        
        # Проверяем базу данных
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()
        print(f"✅ Current database: {db_name[0]}")
        
        # Проверяем пользователя
        cur.execute("SELECT current_user;")
        user = cur.fetchone()
        print(f"✅ Current user: {user[0]}")
        
        # Закрываем соединение
        cur.close()
        conn.close()
        
        print("🎉 PostgreSQL connection test passed!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Убедитесь, что PostgreSQL запущен")
        print("2. Проверьте правильность пароля в DATABASE_URL")
        print("3. Убедитесь, что база данных 'emotion_analyzer' существует")
        print("4. Проверьте, что пользователь 'emotion_user' имеет права")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    sys.exit(0 if success else 1)