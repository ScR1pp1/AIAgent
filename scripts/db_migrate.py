"""
Простой скрипт для миграций базы данных
"""
import asyncio
import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.database import engine
from src.database.models import Base

async def create_tables():
    """Создание всех таблиц"""
    print("🔄 Создание таблиц...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы созданы успешно!")

async def drop_tables():
    """Удаление всех таблиц"""
    print("🔄 Удаление таблиц...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✅ Таблицы удалены успешно!")

async def reset_database():
    """Полный сброс базы данных"""
    await drop_tables()
    await create_tables()

def main():
    parser = argparse.ArgumentParser(description='Database migration tool')
    parser.add_argument('action', choices=['create', 'drop', 'reset', 'init'],
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        asyncio.run(create_tables())
    elif args.action == 'drop':
        asyncio.run(drop_tables())
    elif args.action == 'reset':
        asyncio.run(reset_database())
    elif args.action == 'init':
        asyncio.run(create_tables())

if __name__ == '__main__':
    main()
