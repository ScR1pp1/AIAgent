from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    message_type = Column(String(50), default="text")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))
    knowledge_metadata = Column(JSONB)
    content_type = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    github_url = Column(String(500))
    linkedin_url = Column(String(500))
    skills = Column(JSONB)
    experience_level = Column(String(50))
    status = Column(String(50), default="new")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Vacancy(Base):
    __tablename__ = "vacancies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    required_skills = Column(JSONB)
    experience_level = Column(String(50))
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
