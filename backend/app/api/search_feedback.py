"""
검색 피드백 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.search_feedback_service import SearchFeedbackService
from app.models.database import User

router = APIRouter(prefix="/search/feedback", tags=["검색 피드백"])


class FeedbackRequest(BaseModel):
    """피드백 요청"""
    search_id: str = Field(..., description="검색 기록 ID")
    result_id: str = Field(..., description="검색 결과 ID")
    feedback_type: str = Field(..., description="피드백 타입: relevant, irrelevant, helpful, not_helpful")
    rating: Optional[int] = Field(None, ge=1, le=5, description="평점 (1-5)")
    comment: Optional[str] = Field(None, description="코멘트")


@router.post("")
async def record_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """검색 피드백 기록"""
    # 검색 기록 조회
    from app.models.database import SearchHistory
    search_history = db.query(SearchHistory).filter(
        SearchHistory.id == feedback.search_id
    ).first()
    
    if not search_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검색 기록을 찾을 수 없습니다."
        )
    
    feedback_service = SearchFeedbackService(db)
    result = feedback_service.record_feedback(
        search_id=feedback.search_id,
        user_id=current_user.id,
        query=search_history.query,
        result_id=feedback.result_id,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        comment=feedback.comment
    )
    
    return {
        "id": result.id,
        "message": "피드백이 기록되었습니다."
    }


@router.get("/stats")
async def get_feedback_stats(
    query: Optional[str] = Query(None, description="검색 쿼리 필터"),
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """검색 피드백 통계 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 통계를 조회할 수 있습니다."
        )
    
    feedback_service = SearchFeedbackService(db)
    stats = feedback_service.get_feedback_stats(query=query, days=days)
    return stats


@router.get("/performance")
async def get_query_performance(
    top_n: int = Query(20, ge=1, le=100, description="상위 N개 쿼리"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """쿼리별 성능 분석"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 성능 분석을 조회할 수 있습니다."
        )
    
    feedback_service = SearchFeedbackService(db)
    performance = feedback_service.get_query_performance(top_n=top_n)
    return {"queries": performance}


@router.get("/suggestions")
async def get_improvement_suggestions(
    query: str = Query(..., description="검색 쿼리"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """검색 개선 제안"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 개선 제안을 조회할 수 있습니다."
        )
    
    feedback_service = SearchFeedbackService(db)
    suggestions = feedback_service.get_improvement_suggestions(query=query)
    return {"suggestions": suggestions}


@router.get("/history")
async def get_user_feedback_history(
    limit: int = Query(50, ge=1, le=200, description="최대 조회 수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 피드백 이력 조회"""
    feedback_service = SearchFeedbackService(db)
    history = feedback_service.get_user_feedback_history(
        user_id=current_user.id,
        limit=limit
    )
    
    return {
        "feedbacks": [
            {
                "id": f.id,
                "search_id": f.search_id,
                "query": f.query,
                "result_id": f.result_id,
                "feedback_type": f.feedback_type,
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in history
        ]
    }

