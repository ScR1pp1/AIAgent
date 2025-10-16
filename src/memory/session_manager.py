from typing import Dict, List, Optional
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

from src.database.models import ConversationHistory
from src.memory.redis_manager import redis_session_manager

logger = logging.getLogger(__name__)

class SessionManager:
    """Гибридный менеджер сессий (Redis + PostgreSQL)"""
    
    def __init__(self):
        self.active_sessions: Dict[int, UUID] = {}
        self.session_timeouts: Dict[UUID, datetime] = {}
    
    async def get_or_create_session(self, chat_id: int) -> UUID:
        """Получение или создание сессии для chat_id"""
        try:
            return await redis_session_manager.get_or_create_session(chat_id)
        except Exception as e:
            logger.warning(f"Redis session failed, using memory: {e}")
            if chat_id in self.active_sessions:
                session_id = self.active_sessions[chat_id]
                self.session_timeouts[session_id] = datetime.now()
                return session_id
            
            session_id = uuid4()
            self.active_sessions[chat_id] = session_id
            self.session_timeouts[session_id] = datetime.now()
            return session_id
    
    async def get_session_history(
        self, 
        chat_id: int, 
        session: AsyncSession,
        limit: Optional[int] = 10
    ) -> List[dict]:
        """Получение истории диалога (сначала Redis, потом PostgreSQL)"""
        
        try:
            redis_history = await redis_session_manager.get_conversation_history(chat_id, limit)
            if redis_history:
                return redis_history
        except Exception as e:
            logger.warning(f"Redis history failed: {e}")
        
        try:
            session_id = await self.get_or_create_session(chat_id)
            
            stmt = select(ConversationHistory).where(
                ConversationHistory.session_id == session_id
            ).order_by(ConversationHistory.timestamp.asc())
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await session.execute(stmt)
            db_history = result.scalars().all()
            
            history_list = []
            for msg in db_history:
                history_list.append({
                    "user_message": msg.user_message,
                    "bot_response": msg.bot_response,
                    "timestamp": msg.timestamp.isoformat()
                })
            
            try:
                for conv in history_list:
                    await redis_session_manager.save_conversation(
                        chat_id, conv['user_message'], conv['bot_response']
                    )
            except Exception as e:
                logger.warning(f"Failed to cache history in Redis: {e}")
            
            return history_list
            
        except Exception as e:
            logger.error(f"Database history failed: {e}")
            return []
    
    async def save_conversation(
        self, 
        chat_id: int,
        user_message: str,
        bot_response: str,
        session: AsyncSession
    ) -> ConversationHistory:
        """Сохранение сообщения (и в Redis, и в PostgreSQL)"""
        
        try:
            await redis_session_manager.save_conversation(
                chat_id, user_message, bot_response
            )
        except Exception as e:
            logger.warning(f"Failed to save to Redis: {e}")
        
        session_id = await self.get_or_create_session(chat_id)
        
        conversation = ConversationHistory(
            chat_id=chat_id,
            user_message=user_message,
            bot_response=bot_response,
            session_id=session_id
        )
        
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        
        return conversation
    
    async def clear_session(self, chat_id: int, session: AsyncSession):
        """Очистка сессии (и в Redis, и в PostgreSQL)"""
        
        try:
            await redis_session_manager.clear_session(chat_id)
        except Exception as e:
            logger.warning(f"Failed to clear Redis session: {e}")
        
        if chat_id in self.active_sessions:
            session_id = self.active_sessions[chat_id]
            del self.active_sessions[chat_id]
            if session_id in self.session_timeouts:
                del self.session_timeouts[session_id]
        
        try:
            session_id = await self.get_or_create_session(chat_id)
            
            stmt = delete(ConversationHistory).where(
                ConversationHistory.session_id == session_id
            )
            await session.execute(stmt)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to clear database session: {e}")
            await session.rollback()
    
    async def cleanup_expired_sessions(self, timeout_hours: int = 24):
        """Очистка просроченных сессий в памяти"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, last_activity in self.session_timeouts.items():
            if now - last_activity > timedelta(hours=timeout_hours):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            chat_id = None
            for cid, sid in self.active_sessions.items():
                if sid == session_id:
                    chat_id = cid
                    break
            
            if chat_id:
                del self.active_sessions[chat_id]
            del self.session_timeouts[session_id]

    async def get_conversation_statistics(self, chat_id: int, session: AsyncSession) -> Dict:
        """Статистика по диалогу"""
        from sqlalchemy import func, select
        stmt = select(
            func.count(ConversationHistory.id),
            func.min(ConversationHistory.timestamp),
            func.max(ConversationHistory.timestamp)
        ).where(ConversationHistory.chat_id == chat_id)
        
        result = await session.execute(stmt)
        count, first_msg, last_msg = result.one()
        
        return {
            "total_messages": count,
            "first_message": first_msg,
            "last_message": last_msg,
            "session_duration": last_msg - first_msg if last_msg and first_msg else None
        }

    async def search_conversations(self, query: str, chat_id: int, session: AsyncSession) -> List[Dict]:
        """Поиск по истории сообщений"""
        from sqlalchemy import or_
        stmt = select(ConversationHistory).where(
            ConversationHistory.chat_id == chat_id,
            or_(
                ConversationHistory.user_message.ilike(f"%{query}%"),
                ConversationHistory.bot_response.ilike(f"%{query}%")
            )
        ).order_by(ConversationHistory.timestamp.desc())
        
        result = await session.execute(stmt)
        return [msg for msg in result.scalars().all()]

session_manager = SessionManager()
