"""
Скрипт для диагностики проблем с ботом
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.config import settings
from src.database.database import AsyncSessionLocal, check_db_connection
from src.llm.llm_service import LLMService
from src.mcp.mcp_client import mcp_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_service():
    """Тестируем LLM сервис"""
    print("🤖 Тестирование LLM сервиса...")
    
    llm_service = LLMService()
    
    if not llm_service.client:
        print("❌ LLM клиент не инициализирован")
        return False
    
    print(f"✅ LLM клиент инициализирован: {llm_service.client.base_url}")
    
    try:
        test_message = "Привет! Ответь коротко: тест"
        async with AsyncSessionLocal() as session:
            response = await llm_service.generate_response(
                user_message=test_message,
                chat_id=12345,
                session=session
            )
        
        print(f"✅ LLM ответил: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка LLM: {e}")
        return False

async def test_mcp_services():
    """Тестируем MCP сервисы"""
    print("\n🔧 Тестирование MCP сервисов...")
    
    services = {
        "GitHub": mcp_client.github,
        "Web Search": mcp_client.web_search,
        "Google Sheets": mcp_client.sheets
    }
    
    all_working = True
    
    for name, client in services.items():
        try:
            if hasattr(client, 'base_url'):
                print(f"   {name}: {client.base_url} - ✅ Настроен")
            else:
                print(f"   {name}: ❌ Не настроен")
                all_working = False
                
        except Exception as e:
            print(f"   {name}: ❌ Ошибка - {e}")
            all_working = False
    
    return all_working

async def test_database():
    """Тестируем базу данных"""
    print("\n🗄️ Тестирование базы данных...")
    
    try:
        is_connected = await check_db_connection()
        if is_connected:
            print("✅ База данных подключена")
            return True
        else:
            print("❌ База данных не подключена")
            return False
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

async def test_environment():
    """Проверяем переменные окружения"""
    print("\n🔑 Проверка переменных окружения...")
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "AI_API_KEY",
        "AI_PROVIDER"
    ]
    
    for var in required_vars:
        value = getattr(settings, var, None) or getattr(settings.ai, var.lower(), None)
        if value and len(str(value)) > 5:
            print(f"   {var}: ✅ Установлен")
        else:
            print(f"   {var}: ❌ НЕ установлен или слишком короткий")

async def main():
    print("🔍 Запуск диагностики HR Assistant Bot...\n")
    
    await test_environment()
    await test_database()
    await test_mcp_services()
    await test_llm_service()
    
    print("\n📋 Рекомендации:")
    print("• Проверьте AI_API_KEY в .env файле")
    print("• Убедитесь что AI_PROVIDER поддерживает выбранную модель")
    print("• Проверьте доступность AI сервиса (OpenRouter/Ollama)")
    print("• Проверьте логи командой: docker-compose logs app --tail=20")

if __name__ == "__main__":
    asyncio.run(main())
