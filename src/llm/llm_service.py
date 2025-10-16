import logging
from openai import AsyncOpenAI
from src.config import settings
from src.database.models import ConversationHistory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMService:
    
    def __init__(self):
        self.client = self._create_client()
        logger.info(f"LLMService initialized with provider: {settings.ai.ai_provider}")
    
    def _create_client(self):
        """Создает клиента для выбранного провайдера с валидацией"""
        if not settings.ai.api_key or settings.ai.api_key == "your_ai_api_key_here":
            logger.error("❌ AI_API_KEY не установлен или имеет значение по умолчанию")
            raise ValueError("AI_API_KEY not configured properly")
        
        try:
            client = AsyncOpenAI(
                api_key=settings.ai.api_key,
                base_url=settings.ai.effective_base_url,
                timeout=30.0,
                max_retries=3
            )
            
            if not settings.ai.validate_model():
                logger.warning(f"Модель {settings.ai.effective_model} может не поддерживаться провайдером {settings.ai.ai_provider}")
            
            logger.info(f"✅ AI клиент инициализирован: {settings.ai.effective_base_url}")
            logger.info(f"✅ Модель: {settings.ai.effective_model}")
            return client
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания AI клиента: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self, 
        user_message: str, 
        chat_id: int,
        session: AsyncSession,
        mcp_results: list = None
    ) -> str:
        
        try:
            if not self.client:
                return "🤖 Ошибка: AI сервис не настроен. Проверьте AI_API_KEY в .env файле."
            
            history = await self._get_conversation_history(chat_id, session)
            
            system_prompt = self._build_system_prompt(mcp_results)
            
            messages = [{"role": "system", "content": system_prompt}]
            
            for msg in history[-6:]:
                messages.append(msg)
            
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"Отправка запроса к {settings.ai.chat_model}")
            
            response = await self.client.chat.completions.create(
                model=settings.ai.chat_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            logger.info(f"Получен ответ длиной {len(result)} символов")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка AI API: {e}")
            error_msg = str(e)
            
            if "401" in error_msg:
                return "🤖 Ошибка: неверный API ключ. Проверьте AI_API_KEY в .env файле."
            elif "429" in error_msg:
                return "🤖 Ошибка: превышен лимит запросов. Попробуйте позже."
            elif "404" in error_msg:
                return f"🤖 Ошибка: модель '{settings.ai.chat_model}' не найдена. Проверьте AI_CHAT_MODEL в .env файле."
            else:
                return f"🤖 Ошибка связи с AI сервисом: {error_msg[:100]}..."
    
    async def _get_conversation_history(
        self, 
        chat_id: int, 
        session: AsyncSession,
        limit: int = 20
    ) -> list:
        """Получает историю диалога из базы данных"""
        try:
            stmt = select(ConversationHistory).where(
                ConversationHistory.chat_id == chat_id
            ).order_by(ConversationHistory.timestamp.desc()).limit(limit)
            
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            history = []
            for msg in reversed(messages):
                history.append({"role": "user", "content": msg.user_message})
                history.append({"role": "assistant", "content": msg.bot_response})
            
            logger.debug(f"Загружено {len(history)} сообщений из истории для chat_id {chat_id}")
            return history
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")
            return []
    
    def _build_system_prompt(self, mcp_results: list = None) -> str:
        """Строит системный промпт"""
        base_prompt = """Ты - HR-ассистент для IT-рекрутинга. Твоя задача помогать с поиском кандидатов, 
анализом резюме, планированием собеседований и управлением процесса найма.

Ты имеешь доступ к следующим инструментам:
- База данных кандидатов (можешь искать по навыкам)
- GitHub анализ профилей разработчиков
- Веб-поиск для получения актуальной информации
- Google Sheets для работы с таблицами
- База вакансий

Когда пользователь запрашивает:
- "Найди кандидатов с Python" → используй поиск кандидатов
- "Проанализируй github.com/username" → используй GitHub
- "Какие вакансии открыты?" → проверь базу вакансий
- "Найди информацию о..." → используй веб-поиск

Отвечай на русском языке. Будь полезным, профессиональным и дружелюбным.
Используй инструменты когда это необходимо для ответа на вопрос."""

        if mcp_results:
            base_prompt += "\n\nДоступные инструменты поиска:"
            for result in mcp_results:
                base_prompt += f"\n- {result.get('tool', 'Unknown')}"
        
        return base_prompt
    
    async def generate_embeddings(self, text: str) -> list:
        """Генерация эмбеддингов"""
        try:
            if not self.client:
                return [0.0] * 1536
                
            response = await self.client.embeddings.create(
                model=settings.ai.embeddings_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддингов: {e}")
            return [0.0] * 1536