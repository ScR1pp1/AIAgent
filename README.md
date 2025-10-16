# HR Assistant Bot - IT Recruitment Agent

🤖 Интеллектуальный HR-агент для IT-рекрутинга с Telegram интерфейсом, использующий MCP-инструменты и векторную базу знаний.

## 🚀 Функциональность

- **Telegram интерфейс** с командами /start, /help, /health, /clear
- **3 MCP-инструмента**: Google Sheets, GitHub, Web Search
- **Контекстная память** диалогов на PostgreSQL и Redis
- **Векторная база знаний** с pgvector для семантического поиска кандидатов
- **Автоматическое развертывание** через Docker Compose
- **REST API** для интеграции с другими системами

## 🛠 Технологии

- Python 3.12 + FastAPI
- PostgreSQL + pgvector
- Redis для кэширования сессий
- MCP (Model Context Protocol)
- python-telegram-bot
- Docker & Docker Compose
- Groq API для LLM

## 📦 Быстрый старт

```bash
# Клонирование репозитория
git clone https://github.com/ScR1pp1/AIAgent.git
cd AIAgent

# Настройка окружения
cp .env.example .env
# заполните .env файл своими токенами

# Запуск через Docker
docker-compose up -d
🔧 Команды бота
/start - начать работу

/help - справка по командам

/health - статус сервисов

/clear - очистить историю диалога

🗃️ Структура проекта
text
AIAgent/
├── src/                    # Исходный код
│   ├── bot/               # Telegram бот
│   ├── database/          # Модели и подключение БД
│   ├── llm/              # Сервис языковой модели
│   ├── mcp/              # MCP-серверы и клиенты
│   ├── memory/           # Система памяти и сессий
│   └── routers/          # API эндпоинты
├── scripts/              # Вспомогательные скрипты
├── database/             # SQL скрипты и миграции
├── docker-compose.yml    # Конфигурация Docker
└── README.md            # Документация
## ⚙️ Настройка окружения

Создайте `.env` файл на основе `.env.example`:

```bash
# Обязательные переменные
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
AI_API_KEY=your_ai_api_key_here
POSTGRES_PASSWORD=your_secure_password_here

# MCP сервисы
GITHUB_TOKEN=your_github_personal_access_token_here
GOOGLE_CREDENTIALS_PATH=./google_credentials.json

# Опциональные
WEB_SEARCH_API_KEY=your_web_search_api_key_here


## 📊 Мониторинг

- PGAdmin: http://localhost:5050
- Логи приложения: `docker-compose logs app -f`
- Логи базы данных: `docker-compose logs db -f`


## 🐛 Решение проблем

### Бот не отвечает:
```bash
docker-compose logs bot --tail=50

docker-compose exec db psql -U postgres -d hr_assistant

Проверка здоровья:
curl http://localhost:8080/health

📊 API Endpoints
GET /health - статус сервисов

GET /api/v1/conversations/{chat_id} - история диалога

POST /api/v1/knowledge/search - семантический поиск

GET /api/v1/candidates - управление кандидатами