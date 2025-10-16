from fastapi import APIRouter
from datetime import datetime
from src.database.database import check_db_connection
from src.bot.telegram_bot import check_bot_health
from src.mcp.services import check_mcp_services
from src.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        db_status = await check_db_connection()
        telegram_status = await check_bot_health()
        mcp_status = await check_mcp_services()

        telegram_healthy = telegram_status.get("status") == "healthy"
        
        overall_status = "healthy" if all([db_status, telegram_healthy]) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            database=db_status,
            telegram=telegram_healthy,
            mcp_services=mcp_status,
            timestamp=datetime.now()
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database=False,
            telegram=False,
            mcp_services={},
            timestamp=datetime.now()
        )

@router.get("/health/db")
async def health_db():
    status = await check_db_connection()
    return {"database": "connected" if status else "disconnected"}

@router.get("/health/telegram")
async def health_telegram():
    status = await check_bot_health()
    return status

@router.get("/health/mcp")
async def health_mcp():
    status = await check_mcp_services()
    return {"mcp_services": status}
