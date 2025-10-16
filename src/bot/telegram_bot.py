import os
import sys
import logging
import asyncio
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes
)
from sqlalchemy.ext.asyncio import AsyncSession

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.config import settings
    from src.database.database import AsyncSessionLocal
    from src.memory.session_manager import session_manager
    from src.llm.llm_service import LLMService
    from src.mcp.mcp_client import mcp_client
    from src.knowledge.vector_search import VectorSearchService
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📁 Текущая директория:", os.getcwd())
    print("📁 Путь проекта:", project_root)
    sys.exit(1)

logger = logging.getLogger(__name__)

class HRAssistantBot:
    
    def __init__(self):
        self.application = None
        self.is_running = False
        
        try:
            self.llm_service = LLMService()
            logger.info("✅ LLMService инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации LLMService: {e}")
            self.llm_service = None
        
        try:
            self.vector_search = VectorSearchService()
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации VectorSearch: {e}")
            self.vector_search = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
🤖 Добро пожаловать в HR Assistant Bot!

Я ваш интеллектуальный помощник для IT-рекрутинга.

Доступные команды:
/help - показать справку
/health - проверить статус сервисов
/clear - очистить историю диалога

Просто напишите, чем могу помочь!
        """
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📋 **Доступные команды:**

/start - начать работу
/help - показать справку  
/health - статус сервисов
/clear - очистить историю

🎯 **Что я могу сделать:**

• Поиск кандидатов
• Анализ GitHub профилей
• Управление базой кандидатов
• Ответы на вопросы о рекрутинге
        """
        await update.message.reply_text(help_text)
    
    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            from src.database.database import check_db_connection
            from src.mcp.services import check_mcp_services
            
            db_status = await check_db_connection()
            mcp_status = await check_mcp_services()
            
            service_names = {
                "github": "GitHub",
                "web_search": "Web Search", 
                "google_sheets": "Google Sheets"
            }
            
            mcp_services_text = ""
            for service, status in mcp_status.items():
                status_icon = "🟢" if status else "🔴"
                name = service_names.get(service, service.replace('_', ' ').title())
                mcp_services_text += f"• {name}: {status_icon}\n"
            
            ai_status = "🟢" if self.llm_service and self.llm_service.client else "🔴"
            
            health_status = "🟢 Все системы работают" if db_status and all(mcp_status.values()) else "🟡 Частичные проблемы" if db_status else "🔴 Критические проблемы"
            
            status_text = f"""
{health_status}

📊 **Статус сервисов:**
• База данных: {'🟢' if db_status else '🔴'}
• Telegram API: 🟢
• AI сервис: {ai_status}

🔧 **MCP инструменты:**
{mcp_services_text}
            """
    
            await update.message.reply_text(status_text)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            await update.message.reply_text("🔴 Ошибка при проверке статуса")
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        async with AsyncSessionLocal() as session:
            await session_manager.clear_session(chat_id, session)
        
        await update.message.reply_text("🧹 История диалога очищена! Начинаем новый разговор.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        chat_id = update.effective_chat.id
        
        logger.info(f"📨 Получено сообщение от {chat_id}: {user_message}")
        
        try:
            simple_response = self._get_simple_response(user_message)
            if simple_response:
                await update.message.reply_text(simple_response)
                return
            
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            
            async with AsyncSessionLocal() as session:
                if self.llm_service and self.llm_service.client:
                    mcp_results = await self._process_user_request(user_message, session)
                    response = await self.llm_service.generate_response(
                        user_message=user_message,
                        chat_id=chat_id,
                        session=session,
                        mcp_results=mcp_results
                    )
                else:
                    response = "🤖 Режим ограниченной функциональности. AI сервис настраивается."
                
                await session_manager.save_conversation(
                    chat_id=chat_id,
                    user_message=user_message,
                    bot_response=response,
                    session=session
                )
                await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_message = "⚠️ Произошла ошибка при обработке запроса. Попробуйте еще раз."
            await update.message.reply_text(error_message)

    async def _process_user_request(self, user_message: str, session: AsyncSession) -> list:
        """Обработка запросов с MCP инструментами"""
        mcp_results = []
        
        if not settings.mcp.enable_mcp:
            return mcp_results
            
        try:
            message_lower = user_message.lower()
            
            if any(keyword in message_lower for keyword in ['github', 'профиль', 'репозиторий', 'git']):
                github_result = await self._handle_github_request(user_message)
                if github_result:
                    mcp_results.append({"tool": "github", "result": github_result})
            
            if any(keyword in message_lower for keyword in ['найди', 'поищи', 'информация', 'search']):
                search_result = await self._handle_web_search(user_message)
                if search_result:
                    mcp_results.append({"tool": "web_search", "result": search_result})
            
            if any(keyword in message_lower for keyword in ['таблиц', 'sheet', 'excel', 'обнови']):
                sheets_result = await self._handle_sheets_request(user_message)
                if sheets_result:
                    mcp_results.append({"tool": "google_sheets", "result": sheets_result})
                    
        except Exception as e:
            logger.error(f"Error in MCP processing: {e}")
        
        return mcp_results
    
    async def _handle_github_request(self, message: str) -> str:
        try:
            words = message.split()
            for word in words:
                if 'github.com/' in word:
                    username = word.split('github.com/')[-1].split('/')[0]
                    return await mcp_client.github.get_user_profile(username)
            
            return await mcp_client.github.search_repositories(message)
            
        except Exception as e:
            logger.error(f"GitHub request error: {e}")
            return f"Ошибка при работе с GitHub: {str(e)}"
    
    async def _handle_web_search(self, message: str) -> str:
        try:
            search_query = self._extract_search_query(message)
            
            if not search_query:
                return "🔍 Пожалуйста, уточните что именно вы хотите найти"
                
            result = await mcp_client.web_search.search_web(search_query, num_results=3)
            return result
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"❌ Ошибка при поиске: {str(e)}"

    def _get_simple_response(self, message: str) -> str:
        """Простые ответы без LLM"""
        message_lower = message.lower()
        
        responses = {
            'привет': '👋 Привет! Я HR-ассистент. Чем могу помочь?',
            'hello': '👋 Hello! I am HR Assistant. How can I help you?',
            'как дела': '🤖 У меня все отлично! Готов помочь с поиском кандидатов.',
            'help': '📋 Используйте /help для списка команд',
            'start': '🚀 Используйте /start для начала работы',
            'health': '🏥 Используйте /health для проверки статуса',
            'test': '🧪 Тестовый режим работает!',
            'тест': '🧪 Тестовый режим работает!',
        }
        
        for key, response in responses.items():
            if key in message_lower:
                return response
        
        return None

    def _extract_search_query(self, message: str) -> str:
        """Извлекает поисковый запрос из сообщения"""
        search_keywords = ['найди', 'поищи', 'ищи', 'search', 'find', 'google']
        
        words = message.lower().split()
        query_words = []
        
        collect = False
        for word in words:
            if word in search_keywords:
                collect = True
                continue
            if collect:
                if word not in ['информацию', 'информация', 'про', 'о', 'the', 'a', 'an']:
                    query_words.append(word)
        
        if not query_words:
            bot_names = ['бот', 'bot', 'assistant', 'помощник']
            query_words = [word for word in words if word not in bot_names]
        
        return ' '.join(query_words).strip()
    
    async def _handle_sheets_request(self, message: str) -> str:
        try:
            if 'прочитай' in message.lower() or 'покажи' in message.lower():
                return await mcp_client.sheets.read_spreadsheet(
                    "your-spreadsheet-id", "A1:D10"
                )
            elif 'обнови' in message.lower():
                return "Google Sheets: Готов обновить таблицу (нужен spreadsheet_id)"
            else:
                return "Google Sheets: Могу читать и обновлять таблицы кандидатов"
                
        except Exception as e:
            logger.error(f"Google Sheets error: {e}")
            return f"Ошибка при работе с Google Sheets: {str(e)}"
    
    async def setup_commands(self):
        commands = [
            BotCommand("start", "Начать работу"),
            BotCommand("help", "Помощь и команды"),
            BotCommand("health", "Статус сервисов"),
            BotCommand("clear", "Очистить историю"),
        ]
        await self.application.bot.set_my_commands(commands)
    
    def run(self):
        """Синхронный запуск бота для локального использования"""
        print("🤖 Запуск HR Assistant Bot...")
        
        if not settings.telegram.bot_token:
            print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
            return
        
        try:
            self.application = (
                Application.builder()
                .token(settings.telegram.bot_token)
                .build()
            )
            
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("health", self.health_command))
            self.application.add_handler(CommandHandler("clear", self.clear_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.setup_commands())
            
            print("✅ Бот инициализирован")
            print("🚀 Запуск...")
            print("📱 Отправьте /start вашему боту в Telegram")
            print("⏹️  Для остановки нажмите Ctrl+C")
            
            self.application.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )
            
        except KeyboardInterrupt:
            print("\n🛑 Бот остановлен")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

bot_instance = HRAssistantBot()

async def stop_bot():
    """Функция для остановки из main.py"""
    if bot_instance.application and bot_instance.is_running:
        await bot_instance.application.stop()
        await bot_instance.application.shutdown()
        bot_instance.is_running = False
        logger.info("Telegram bot stopped")

async def check_bot_health() -> dict:
    """Функция проверки здоровья бота - исправленная версия"""
    try:
        from src.config import settings
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.telegram.org/bot{settings.telegram.bot_token}/getMe",
                timeout=10
            ) as response:
                bot_ok = response.status == 200
                
        try:
            from src.memory.session_manager import session_manager
            active_sessions = len(session_manager.active_sessions)
        except Exception:
            active_sessions = 0
            
        return {
            "status": "healthy" if bot_ok else "unhealthy",
            "message": "Bot is connected to Telegram API" if bot_ok else "Bot is not connected",
            "active_sessions": active_sessions,
            "telegram_api": bot_ok
        }
        
    except Exception as e:
        logger.error(f"Error checking bot health: {e}")
        return {
            "status": "unhealthy",
            "message": f"Health check error: {str(e)}",
            "active_sessions": 0,
            "telegram_api": False
        }

if __name__ == "__main__":
    bot = HRAssistantBot()
    bot.run()