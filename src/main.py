from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.config import settings
from src.database.database import init_db
from src.routers import health, conversations, knowledge, candidates

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HR Assistant API...")
    
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        
    yield
    
    logger.info("Shutting down HR Assistant API...")
    
    from src.mcp.mcp_client import close_mcp_clients
    await close_mcp_clients()
    logger.info("MCP clients closed")

app = FastAPI(
    title=settings.app_name,
    description="HR Assistant Bot with MCP tools and vector database",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/debug/ai")
async def debug_ai():
    """Эндпоинт для отладки AI сервиса"""
    from src.llm.llm_service import LLMService
    from src.database.database import AsyncSessionLocal
    
    llm_service = LLMService()
    
    debug_info = {
        "ai_provider": settings.ai.ai_provider,
        "base_url": settings.ai.effective_base_url,
        "model": settings.ai.effective_model,
        "has_api_key": bool(settings.ai.api_key),
        "client_initialized": bool(llm_service.client),
        "supported_models": settings.ai.supported_models.get(settings.ai.ai_provider, []),
        "model_valid": settings.ai.validate_model()
    }
    
    if llm_service.client:
        try:
            async with AsyncSessionLocal() as session:
                response = await llm_service.generate_response(
                    user_message="Тестовое сообщение: привет! Как дела?",
                    chat_id=12345,
                    session=session
                )
            debug_info["test_response"] = response[:100] + "..." if len(response) > 100 else response
            debug_info["test_status"] = "success"
            debug_info["response_length"] = len(response)
        except Exception as e:
            debug_info["test_status"] = "error"
            debug_info["test_error"] = str(e)
    else:
        debug_info["test_status"] = "client_not_initialized"
    
    return debug_info

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.allowed_origins,
    allow_credentials=settings.security.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=settings.security.cors_max_age,
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
app.include_router(candidates.router, prefix="/api/v1", tags=["candidates"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/docs", include_in_schema=False)
async def custom_docs():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """Корневой health check эндпоинт"""
    return {"status": "healthy", "service": "HR Assistant", "timestamp": datetime.now()}

@app.get("/api/v1/health")
async def health_check_detailed():
    """Детальный health check"""
    from src.database.database import check_db_connection
    from src.mcp.services import check_mcp_services
    
    db_status = await check_db_connection()
    mcp_status = await check_mcp_services()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": db_status,
        "mcp_services": mcp_status,
        "timestamp": datetime.now()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)