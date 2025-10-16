import asyncio
from datetime import datetime, timedelta
from src.database.database import AsyncSessionLocal
from src.database.models import ConversationHistory
from sqlalchemy import delete

async def cleanup_old_messages(days: int = 30):
    """Удаление сообщений старше указанного количества дней"""
    async with AsyncSessionLocal() as session:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = delete(ConversationHistory).where(
            ConversationHistory.timestamp < cutoff_date
        )
        
        result = await session.execute(stmt)
        await session.commit()
        
        print(f"Удалено сообщений: {result.rowcount}")

if __name__ == "__main__":
    asyncio.run(cleanup_old_messages(30))
