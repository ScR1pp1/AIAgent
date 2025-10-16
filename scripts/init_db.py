"""
Скрипт для инициализации базы данных
Можно использовать как альтернативу Alembic
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.database import init_db, engine
from src.database.models import Base, Candidate, ConversationHistory, Vacancy

async def initialize_database():
    """Инициализация базы данных"""
    print("🔄 Инициализация базы данных...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[
            ConversationHistory.__table__,
            Candidate.__table__, 
            Vacancy.__table__
        ])
        
        print("✅ База данных успешно инициализирована!")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(initialize_database())
