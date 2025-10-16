# Деплой HR Assistant Bot

## Предварительные требования

- Docker & Docker Compose
- PostgreSQL (если не используется Docker)
- Redis (если не используется Docker)

## Настройка окружения

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ScR1pp1/AIAgent.git
cd AIAgent
```

2. Создайте файл окружения:
```bash
cp .example.env .env
```

3. Заполните переменные в `.env`.

## Запуск (Docker Compose)

```bash
docker-compose up -d --build
```

Проверка сервисов:
- API: http://localhost:8080/health
- GitHub MCP: http://localhost:8001/health
- Web Search MCP: http://localhost:8002/health
- Google Sheets MCP: http://localhost:8003/health

## Обновление
```bash
docker-compose pull && docker-compose up -d --build
```

## Локальный запуск (без Docker)

Требуется PostgreSQL и Redis локально.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```
