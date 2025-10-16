import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import logging
load_dotenv()
logger = logging.getLogger(__name__)


class AISettings(BaseSettings):
    ai_provider: str = os.getenv("AI_PROVIDER", "groq")
    api_key: str = os.getenv("AI_API_KEY", "")
    base_url: str = os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1")
    chat_model: str = os.getenv("AI_CHAT_MODEL", "openai/gpt-oss-120b")
    embeddings_model: str = os.getenv("AI_EMBEDDINGS_MODEL", "text-embedding-ada-002")
    
    @property
    def effective_base_url(self) -> str:
        return self.base_url
    
    @property
    def effective_model(self) -> str:
        return self.chat_model
    
    @property
    def supported_models(self) -> dict:
        return {
            "groq": [
                "llama3-8b-8192",
                "llama3-70b-8192", 
                "mixtral-8x7b-32768"
            ],
            "openai": [
                "gpt-4",
                "gpt-3.5-turbo"
            ]
        }
    
    def validate_model(self) -> bool:
        supported = self.supported_models.get(self.ai_provider, [])
        if self.effective_model not in supported:
            logger.warning(
                f"Модель '{self.effective_model}' может не поддерживаться провайдером '{self.ai_provider}'. "
                f"Рекомендуемые модели: {', '.join(supported)}"
            )
            return False
        return True

class DatabaseSettings(BaseSettings):
    postgres_db: str = os.getenv("POSTGRES_DB", "hr_assistant")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres") 
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "myfirsttgbot")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

class SecuritySettings(BaseSettings):
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    cors_allow_credentials: bool = True
    cors_max_age: int = 600

class TelegramSettings(BaseSettings):
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    bot_name: str = "HRProAssistant"
    bot_username: str = "HRProAssistant_bot"
    webhook_url: Optional[str] = os.getenv("WEBHOOK_URL")
    admin_chat_id: Optional[int] = os.getenv("ADMIN_CHAT_ID")
    description: str = "🤖 AI-помощник для IT-рекрутинга. Найду лучших разработчиков, проанализирую GitHub и организую процесс найма!"

class MCPSettings(BaseSettings):
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    web_search_api_key: str = os.getenv("WEB_SEARCH_API_KEY", "")
    google_credentials_path: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "./google_credentials.json")
    
    github_url: str = os.getenv("MCP_GITHUB_URL", "http://mcp_github:8001")
    web_search_url: str = os.getenv("MCP_WEB_SEARCH_URL", "http://mcp_web_search:8002")
    sheets_url: str = os.getenv("MCP_SHEETS_URL", "http://mcp_sheets:8003")
    
    enable_mcp: bool = os.getenv("ENABLE_MCP", "true").lower() == "true"

class VectorDBSettings(BaseSettings):
    vector_dimension: int = int(os.getenv("VECTOR_DIMENSION", "1536"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

class RedisSettings(BaseSettings):
    host: str = os.getenv("REDIS_HOST", "redis")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    db: int = int(os.getenv("REDIS_DB", "0"))
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

class MonitoringSettings(BaseSettings):
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "9090"))
    grafana_port: int = int(os.getenv("GRAFANA_PORT", "3000"))
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    metrics_port: int = int(os.getenv("METRICS_PORT", "8000"))

class CICDSettings(BaseSettings):
    test_timeout: int = int(os.getenv("TEST_TIMEOUT", "30"))
    coverage_threshold: int = int(os.getenv("COVERAGE_THRESHOLD", "80"))
    docker_registry: str = os.getenv("DOCKER_REGISTRY", "")
    deploy_environment: str = os.getenv("DEPLOY_ENVIRONMENT", "staging")

class Settings(BaseSettings):
    app_name: str = "HR Assistant Bot"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_conversation_history: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
    
    database: DatabaseSettings = DatabaseSettings()
    telegram: TelegramSettings = TelegramSettings()
    mcp: MCPSettings = MCPSettings()
    vector_db: VectorDBSettings = VectorDBSettings()
    ai: AISettings = AISettings()
    redis: RedisSettings = RedisSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    cicd: CICDSettings = CICDSettings()
    security: SecuritySettings = SecuritySettings()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def validate_settings(self):
        # """Валидация критических настроек"""
        # errors = []
        
        # if not self.telegram.bot_token or "AAHOzTIes6G" in self.telegram.bot_token:
        #     errors.append("Invalid Telegram bot token - contains compromised or default value")
        
        # if not self.ai.api_key or "your_ai_api_key" in self.ai.api_key:
        #     errors.append("Invalid AI API key - not configured or using default value")
        
        # if self.mcp.enable_mcp and (not self.mcp.github_token or "ghp_" in self.mcp.github_token):
        #     errors.append("Invalid GitHub token - contains real token in code")
        
        # if self.mcp.enable_mcp and not os.path.exists(self.mcp.google_credentials_path):
        #     errors.append(f"Google credentials file not found: {self.mcp.google_credentials_path}")
        
        # if not self.database.postgres_password or "myfirsttgbot" in self.database.postgres_password:
        #     errors.append("Using default database password - change immediately")
        
        # if errors:
        #     error_msg = "Configuration validation failed:\n" + "\n".join(f"• {error}" for error in errors)
        #     logger.error(error_msg)
        #     raise ValueError(error_msg)
        
        # logger.info("✅ All configuration settings validated successfully")

        """Упрощенная валидация для отладки"""
        warnings = []
        
        if not self.telegram.bot_token:
            warnings.append("❌ TELEGRAM_BOT_TOKEN обязателен!")
        else:
            logger.info(f"✅ Telegram token: {self.telegram.bot_token[:10]}...")
        
        if not self.ai.api_key or self.ai.api_key == "your_ai_api_key_here":
            warnings.append("⚠️ AI_API_KEY не установлен - бот будет работать в ограниченном режиме")
        else:
            logger.info(f"✅ AI API key: {self.ai.api_key[:10]}...")
        
        if warnings:
            logger.warning("Предупреждения конфигурации:\n" + "\n".join(warnings))
        else:
            logger.info("✅ Базовая конфигурация проверена")

settings = Settings()

try:
    settings.validate_settings()
except ValueError as e:
    logger.critical(f"CRITICAL: {e}")