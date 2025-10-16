from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from src.database.database import get_db
from src.knowledge.vector_search import VectorSearchService
from src.schemas import KnowledgeBaseCreate, KnowledgeBaseResponse, SearchRequest

router = APIRouter()
vector_search = VectorSearchService()

@router.post("/knowledge", response_model=KnowledgeBaseResponse)
async def add_to_knowledge_base(
    knowledge_data: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        knowledge_item = await vector_search.add_to_knowledge_base(
            content=knowledge_data.content,
            knowledge_metadata=knowledge_data.knowledge_metadata or {},
            content_type=knowledge_data.content_type,
            session=db
        )
        return knowledge_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to knowledge base: {str(e)}")

@router.post("/knowledge/search", response_model=List[Dict[str, Any]])
async def search_knowledge_base(
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        results = await vector_search.semantic_search(
            query=search_request.query,
            session=db,
            limit=search_request.limit,
            similarity_threshold=search_request.similarity_threshold
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching knowledge base: {str(e)}")

@router.get("/knowledge/candidates/search")
async def search_candidates_by_skills(
    query: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    try:
        results = await vector_search.search_candidates_by_skills(
            skills_query=query,
            session=db,
            limit=limit
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching candidates: {str(e)}")
