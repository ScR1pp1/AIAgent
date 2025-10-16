from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from src.database.models import KnowledgeBase
from src.llm.llm_service import LLMService

logger = logging.getLogger(__name__)

class VectorSearchService:
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def add_document(
        self,
        content: str,
        doc_type: str,
        metadata: dict,
        session: AsyncSession
    ) -> KnowledgeBase:
        """Добавление документов в векторную БЗ"""
        embedding = await self.llm_service.generate_embeddings(content)
        
        knowledge_item = KnowledgeBase(
            content=content,
            embedding=embedding,
            knowledge_metadata=metadata,
            content_type=doc_type
        )
        
        session.add(knowledge_item)
        await session.commit()
        await session.refresh(knowledge_item)
        
        logger.info(f"Документ добавлен в базу знаний: {doc_type}, ID: {knowledge_item.id}")
        return knowledge_item
    
    async def semantic_search(
        self,
        query: str,
        session: AsyncSession,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Семантический поиск по всем документам с использованием pgvector"""
        query_embedding = await self.llm_service.generate_embeddings(query)
        
        sql = text("""
            SELECT 
                id,
                content,
                knowledge_metadata,
                content_type,
                created_at,
                1 - (embedding <=> :embedding) as similarity
            FROM knowledge_base
            WHERE 1 - (embedding <=> :embedding) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)
        
        result = await session.execute(
            sql,
            {
                "embedding": query_embedding,
                "threshold": similarity_threshold,
                "limit": limit
            }
        )
        
        search_results = []
        for row in result:
            search_results.append({
                "id": row[0],
                "content": row[1],
                "metadata": row[2],
                "content_type": row[3],
                "created_at": row[4],
                "similarity": float(row[5])
            })
        
        logger.info(f"Семантический поиск: найдено {len(search_results)} результатов")
        return search_results
    
    async def search_candidates_by_skills(
        self,
        skills_query: str,
        session: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Прямой поиск кандидатов по навыкам в таблице candidates"""
        
        try:
            keywords = [word.strip().lower() for word in skills_query.split() if word.strip()]
            
            if not keywords:
                return []
            
            conditions = []
            params = {"limit": limit}
            
            for i, keyword in enumerate(keywords):
                param_name = f"keyword_{i}"
                conditions.append(f"""
                    (skills::text ILIKE %({param_name})s 
                    OR EXISTS (
                        SELECT 1 
                        FROM jsonb_each_text(skills) AS skill 
                        WHERE skill.key ILIKE %({param_name})s 
                        OR skill.value ILIKE %({param_name})s
                    ))
                """)
                params[param_name] = f"%{keyword}%"
            
            where_clause = " OR ".join(conditions)
            
            sql = text(f"""
            SELECT 
                id, name, email, github_url, skills, experience_level
            FROM candidates
            WHERE {where_clause}
            LIMIT :limit
            """)
            
            result = await session.execute(sql, params)
            
            candidates = []
            for row in result:
                candidates.append({
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "github_url": row[3],
                    "skills": row[4],
                    "experience_level": row[5]
                })
            
            logger.info(f"Найдено кандидатов по запросу '{skills_query}': {len(candidates)}")
            return candidates
            
        except Exception as e:
            logger.error(f"Ошибка поиска кандидатов: {e}")
            return []
    
    async def add_to_knowledge_base(
        self,
        content: str,
        knowledge_metadata: Dict[str, Any],
        content_type: str,
        session: AsyncSession
    ) -> KnowledgeBase:
        """Алиас для обратной совместимости"""
        return await self.add_document(content, content_type, knowledge_metadata, session)