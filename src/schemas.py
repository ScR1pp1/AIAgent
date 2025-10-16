from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class ConversationCreate(BaseModel):
    chat_id: int
    user_message: str
    bot_response: str
    session_id: UUID
    message_type: str = "text"

class ConversationResponse(BaseModel):
    id: int
    chat_id: int
    user_message: str
    bot_response: str
    timestamp: datetime
    session_id: UUID

    class Config:
        from_attributes=True

class KnowledgeBaseCreate(BaseModel):
    content: str
    knowledge_metadata: Optional[Dict[str, Any]] = None
    content_type: str = "text"

class KnowledgeBaseResponse(BaseModel):
    id: int
    content: str
    knowledge_metadata: Optional[Dict[str, Any]]
    content_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes=True

class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    skills: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    status: str = "new"
    notes: Optional[str] = None

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    github_url: Optional[str]
    linkedin_url: Optional[str]
    skills: Optional[Dict[str, Any]]
    experience_level: Optional[str]
    status: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes=True

class CandidateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    skills: Optional[Dict[str, str]] = None
    experience_level: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class VacancyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    required_skills: Optional[Dict[str, str]] = None
    experience_level: Optional[str] = None
    status: str = "active"

class VacancyResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    required_skills: Optional[Dict[str, str]]
    experience_level: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes=True
        
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class HealthResponse(BaseModel):
    status: str
    database: bool
    telegram: bool
    mcp_services: Dict[str, bool]
    timestamp: datetime

class MCPRequest(BaseModel):
    tool: str = Field(..., description="github, web_search, google_sheets")
    action: str = Field(..., description="Действие для инструмента")
    parameters: Dict[str, Any]

class MCPResponse(BaseModel):
    status: str
    data: Optional[Any] = None
    error: Optional[str] = None

class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None

class LLMRequest(BaseModel):
    message: str
    chat_id: int
    use_mcp_tools: bool = True
    include_history: bool = True

class LLMResponse(BaseModel):
    response: str
    used_mcp_tools: List[str] = []
    processing_time: float

class VectorSearchResult(BaseModel):
    id: int
    content: str
    metadata: Optional[Dict[str, Any]]
    content_type: str
    similarity: float
    created_at: datetime

class SessionInfo(BaseModel):
    session_id: UUID
    chat_id: int
    last_activity: datetime
    message_count: int

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    timestamp: datetime

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = None
    timestamp: datetime
