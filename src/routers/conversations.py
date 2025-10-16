from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database.database import get_db
from src.memory.session_manager import session_manager
from src.schemas import ConversationResponse

router = APIRouter()

@router.get("/conversations/{chat_id}", response_model=List[ConversationResponse])
async def get_conversation_history(
    chat_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    try:
        history = await session_manager.get_session_history(chat_id, db, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation history: {str(e)}")

@router.delete("/conversations/{chat_id}")
async def clear_conversation_history(
    chat_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        await session_manager.clear_session(chat_id, db)
        return {"message": "Conversation history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation history: {str(e)}")

@router.get("/conversations/{chat_id}/stats")
async def get_conversation_stats(
    chat_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику диалога"""
    stats = await session_manager.get_conversation_statistics(chat_id, db)
    return stats

@router.get("/conversations/{chat_id}/search")
async def search_conversation(
    chat_id: int,
    query: str,
    db: AsyncSession = Depends(get_db)
):
    """Поиск по истории диалога"""
    results = await session_manager.search_conversations(query, chat_id, db)
    return {"results": results}

@router.get("/conversations/{chat_id}/export")
async def export_conversation(
    chat_id: int,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """Экспорт истории диалога"""
    history = await session_manager.get_session_history(chat_id, db, limit=1000)
    
    if format == "json":
        return {"chat_id": chat_id, "messages": history}
    elif format == "txt":
        text_content = f"История диалога {chat_id}\n\n"
        for msg in history:
            text_content += f"Пользователь: {msg['user_message']}\n"
            text_content += f"Бот: {msg['bot_response']}\n\n"
        return Response(content=text_content, media_type="text/plain")
