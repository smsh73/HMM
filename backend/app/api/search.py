"""
검색 API 라우터
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.schemas import SearchRequest, SearchResponse
from app.services.search_service import SearchService
from app.models.database import User

router = APIRouter(prefix="/search", tags=["검색"])


@router.post("", response_model=SearchResponse)
async def search(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """의미 기반 검색"""
    search_service = SearchService(db)
    result = await search_service.search(
        query=search_request.query,
        user_id=current_user.id,
        top_k=search_request.top_k,
        generate_answer=search_request.generate_answer,
        filter_dict=search_request.filter_dict,
        use_main_system=search_request.use_main_system,
        provider_name=search_request.provider_name
    )
    return result


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="검색어"),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """검색 제안"""
    search_service = SearchService(db)
    suggestions = search_service.get_search_suggestions(q, limit)
    return {"suggestions": suggestions}


@router.get("/history")
async def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """검색 기록 조회"""
    search_service = SearchService(db)
    history = search_service.get_search_history(current_user.id, limit)
    return {"history": history}

