"""
Скрипт проверки переменных окружения
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    print("🔍 Проверка переменных окружения...")
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "AI_API_KEY", 
        "GITHUB_TOKEN",
        "POSTGRES_PASSWORD"
    ]
    
    optional_vars = [
        "WEB_SEARCH_API_KEY",
        "SERPER_API_KEY"
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлен")
        else:
            print(f"❌ {var}: НЕ УСТАНОВЛЕН")
            all_good = False
    
    print("\n📋 Опциональные переменные:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлен")
        else:
            print(f"⚠️  {var}: не установлен (может ограничить функциональность)")
    
    return all_good

if __name__ == "__main__":
    if check_environment():
        print("\n🎉 Все обязательные переменные установлены!")
        sys.exit(0)
    else:
        print("\n🚫 Некоторые обязательные переменные не установлены!")
        sys.exit(1)
