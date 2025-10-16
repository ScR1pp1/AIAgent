import json
import asyncio
from typing import Dict, List, Optional
from uuid import uuid4, UUID
from datetime import datetime, timedelta
import redis.asyncio as redis
import logging
from src.config import settings

logger = logging.getLogger(__name__)

class RedisSessionManager:
    """Менеджер сессий с использованием Redis"""
    
    def __init__(self):
        self.redis_client = None
        self.session_timeout = 24 * 3600
    
    async def init_redis(self):
        """Инициализация Redis клиента"""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password if settings.redis.password else None,
                db=settings.redis.db,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def get_or_create_session(self, chat_id: int) -> UUID:
        """Получение или создание сессии для chat_id"""
        if not self.redis_client:
            await self.init_redis()
        
        session_key = f"session:{chat_id}"
        existing_session = await self.redis_client.get(session_key)
        
        if existing_session:
            await self.redis_client.expire(session_key, self.session_timeout)
            return UUID(existing_session)
        
        session_id = uuid4()
        await self.redis_client.setex(
            session_key, 
            self.session_timeout, 
            str(session_id)
        )
        return session_id
    
    async def save_conversation(
        self, 
        chat_id: int, 
        user_message: str, 
        bot_response: str
    ):
        """Сохранение сообщения в Redis"""
        if not self.redis_client:
            await self.init_redis()
        
        session_id = await self.get_or_create_session(chat_id)
        conversation_key = f"conversation:{session_id}"
        
        conversation = {
            "user_message": user_message,
            "bot_response": bot_response,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.redis_client.rpush(
            conversation_key, 
            json.dumps(conversation, ensure_ascii=False)
        )
        await self.redis_client.expire(conversation_key, self.session_timeout)
    
    async def get_conversation_history(
        self, 
        chat_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Получение истории диалога"""
        if not self.redis_client:
            await self.init_redis()
        
        session_id = await self.get_or_create_session(chat_id)
        conversation_key = f"conversation:{session_id}"
        
        conversations = await self.redis_client.lrange(
            conversation_key, 
            -limit, 
            -1
        )
        
        return [json.loads(conv) for conv in conversations]
    
    async def clear_session(self, chat_id: int):
        """Очистка сессии"""
        if not self.redis_client:
            await self.init_redis()
        
        session_key = f"session:{chat_id}"
        session_id = await self.redis_client.get(session_key)
        
        if session_id:
            conversation_key = f"conversation:{session_id}"
            await self.redis_client.delete(conversation_key)
            await self.redis_client.delete(session_key)
    
    async def cleanup_expired_sessions(self):
        """Очистка просроченных сессий (вызывается периодически)"""
        pass
    
    async def close(self):
        """Закрытие соединения с Redis"""
        if self.redis_client:
            await self.redis_client.close()

redis_session_manager = RedisSessionManager()
