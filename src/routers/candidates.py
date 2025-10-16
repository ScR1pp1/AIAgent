from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import select, text

from src.database.database import get_db
from src.database.models import Candidate
from src.schemas import CandidateCreate, CandidateResponse

router = APIRouter()

@router.post("/candidates", response_model=CandidateResponse)
async def create_candidate(
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        candidate = Candidate(**candidate_data.dict())
        db.add(candidate)
        await db.commit()
        await db.refresh(candidate)
        return candidate
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating candidate: {str(e)}")


@router.get("/candidates", response_model=List[CandidateResponse])
async def get_candidates(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Candidate)
        if status:
            stmt = stmt.where(Candidate.status == status)
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        candidates = result.scalars().all()
        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}")

@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate: {str(e)}")

@router.put("/candidates/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        for key, value in candidate_data.dict().items():
            setattr(candidate, key, value)
        
        await db.commit()
        await db.refresh(candidate)
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating candidate: {str(e)}")

@router.delete("/candidates/{candidate_id}")
async def delete_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        await db.delete(candidate)
        await db.commit()
        
        return {"message": "Candidate deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting candidate: {str(e)}")

@router.get("/check-tables")
async def check_tables(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'candidates'
            );
        """))
        table_exists = result.scalar()
        
        count_result = await db.execute(text("SELECT COUNT(*) FROM candidates"))
        count = count_result.scalar()
        
        return {
            "table_exists": table_exists,
            "record_count": count
        }
    except Exception as e:
        return {"error": str(e)}
