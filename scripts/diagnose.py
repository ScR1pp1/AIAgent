#!/usr/bin/env python3
"""
Скрипт диагностики проекта
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.config import settings
from src.database.database import check_db_connection
from src.llm.llm_service import LLMService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose():
    print("🔍 Запуск диагностики HR Assistant Bot...\n")
    
    print("1. 📋 Проверка переменных окружения:")
    required_vars = {
        "TELEGRAM_BOT_TOKEN": settings.telegram.bot_token,
        "AI_API_KEY": settings.ai.api_key,
        "POSTGRES_PASSWORD": settings.database.postgres_password,
    }
    
    for var_name, value in required_vars.items():
        if value and len(str(value)) > 5:
            print(f"   ✅ {var_name}: установлен")
        else:
            print(f"   ❌ {var_name}: НЕ установлен или слишком короткий")
    
    print("\n2. 🗄️ Проверка базы данных:")
    db_ok = await check_db_connection()
    print(f"   {'✅ База данных подключена' if db_ok else '❌ База данных не подключена'}")
    
    print("\n3. 🤖 Проверка LLM сервиса:")
    llm_service = LLMService()
    if llm_service.client:
        print(f"   ✅ LLM клиент инициализирован")
        print(f"   📝 Провайдер: {settings.ai.ai_provider}")
        print(f"   🧠 Модель: {settings.ai.chat_model}")
        print(f"   🌐 Base URL: {settings.ai.base_url}")
    else:
        print("   ❌ LLM клиент не инициализирован")
    
    print("\n📋 Рекомендации:")
    if not db_ok:
        print("   • Запустите базу данных: docker-compose up db -d")
        print("   • Проверьте параметры подключения в .env файле")
    
    if not llm_service.client:
        print("   • Проверьте AI_API_KEY в .env файле")
        print("   • Убедитесь что провайдер поддерживает выбранную модель")
    
    print("   • Для полного запуска: docker-compose up -d")
    print("   • Для просмотра логов: docker-compose logs -f app")

if __name__ == "__main__":
    asyncio.run(diagnose())