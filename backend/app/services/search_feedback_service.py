"""
검색 피드백 루프 서비스
사용자 피드백을 수집하여 검색 품질 개선
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.models.database import SearchHistory, SearchFeedback
from app.core.logging import logger


class SearchFeedbackService:
    """검색 피드백 루프 서비스"""
    
    def __init__(self, db: Session):
        """검색 피드백 서비스 초기화"""
        self.db = db
    
    def record_feedback(
        self,
        search_id: str,
        user_id: str,
        query: str,
        result_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None
    ) -> SearchFeedback:
        """
        검색 피드백 기록
        
        Args:
            search_id: 검색 기록 ID
            user_id: 사용자 ID
            query: 검색 쿼리
            result_id: 검색 결과 ID (문서 ID 또는 청크 ID)
            feedback_type: 피드백 타입 ("relevant", "irrelevant", "helpful", "not_helpful")
            rating: 평점 (1-5)
            comment: 코멘트
            
        Returns:
            SearchFeedback 객체
        """
        feedback = SearchFeedback(
            search_id=search_id,
            user_id=user_id,
            query=query,
            result_id=result_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        
        logger.info(
            f"검색 피드백 기록: "
            f"search_id={search_id}, "
            f"type={feedback_type}, "
            f"rating={rating}"
        )
        
        return feedback
    
    def get_feedback_stats(
        self,
        query: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        검색 피드백 통계 조회
        
        Args:
            query: 특정 쿼리 필터 (None이면 전체)
            days: 조회 기간 (일)
            
        Returns:
            통계 딕셔너리
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query_filter = self.db.query(SearchFeedback).filter(
            SearchFeedback.created_at >= cutoff_date
        )
        
        if query:
            query_filter = query_filter.filter(
                SearchFeedback.query.ilike(f"%{query}%")
            )
        
        # 전체 피드백 수
        total_feedback = query_filter.count()
        
        # 피드백 타입별 통계
        type_stats = {}
        for feedback_type in ["relevant", "irrelevant", "helpful", "not_helpful"]:
            count = query_filter.filter(
                SearchFeedback.feedback_type == feedback_type
            ).count()
            type_stats[feedback_type] = count
        
        # 평균 평점
        avg_rating = query_filter.filter(
            SearchFeedback.rating.isnot(None)
        ).with_entities(
            func.avg(SearchFeedback.rating)
        ).scalar()
        
        # 관련성 점수 (relevant / (relevant + irrelevant))
        relevance_score = 0.0
        if type_stats.get("relevant", 0) + type_stats.get("irrelevant", 0) > 0:
            relevance_score = type_stats.get("relevant", 0) / (
                type_stats.get("relevant", 0) + type_stats.get("irrelevant", 0)
            )
        
        # 도움됨 점수 (helpful / (helpful + not_helpful))
        helpfulness_score = 0.0
        if type_stats.get("helpful", 0) + type_stats.get("not_helpful", 0) > 0:
            helpfulness_score = type_stats.get("helpful", 0) / (
                type_stats.get("helpful", 0) + type_stats.get("not_helpful", 0)
            )
        
        return {
            "total_feedback": total_feedback,
            "type_stats": type_stats,
            "average_rating": float(avg_rating) if avg_rating else None,
            "relevance_score": relevance_score,
            "helpfulness_score": helpfulness_score,
            "period_days": days
        }
    
    def get_query_performance(
        self,
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        쿼리별 성능 분석
        
        Args:
            top_n: 상위 N개 쿼리
            
        Returns:
            쿼리 성능 리스트
        """
        # 쿼리별 피드백 집계
        query_stats = self.db.query(
            SearchFeedback.query,
            func.count(SearchFeedback.id).label("total_feedback"),
            func.sum(
                func.case(
                    (SearchFeedback.feedback_type == "relevant", 1),
                    else_=0
                )
            ).label("relevant_count"),
            func.sum(
                func.case(
                    (SearchFeedback.feedback_type == "irrelevant", 1),
                    else_=0
                )
            ).label("irrelevant_count"),
            func.avg(SearchFeedback.rating).label("avg_rating")
        ).group_by(
            SearchFeedback.query
        ).order_by(
            desc("total_feedback")
        ).limit(top_n).all()
        
        results = []
        for query, total, relevant, irrelevant, avg_rating in query_stats:
            relevance_score = 0.0
            if (relevant or 0) + (irrelevant or 0) > 0:
                relevance_score = (relevant or 0) / ((relevant or 0) + (irrelevant or 0))
            
            results.append({
                "query": query,
                "total_feedback": total,
                "relevant_count": relevant or 0,
                "irrelevant_count": irrelevant or 0,
                "relevance_score": relevance_score,
                "average_rating": float(avg_rating) if avg_rating else None
            })
        
        return results
    
    def get_improvement_suggestions(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        검색 개선 제안 (피드백 기반)
        
        Args:
            query: 검색 쿼리
            
        Returns:
            개선 제안 리스트
        """
        # 해당 쿼리의 피드백 조회
        feedbacks = self.db.query(SearchFeedback).filter(
            SearchFeedback.query.ilike(f"%{query}%")
        ).order_by(desc(SearchFeedback.created_at)).limit(10).all()
        
        suggestions = []
        
        # 관련성 낮은 결과가 많은 경우
        irrelevant_count = sum(
            1 for f in feedbacks if f.feedback_type == "irrelevant"
        )
        if irrelevant_count > len(feedbacks) * 0.5:
            suggestions.append({
                "type": "low_relevance",
                "message": "이 쿼리의 검색 결과 관련성이 낮습니다. 키워드 검색 가중치를 조정하는 것을 고려하세요.",
                "severity": "high" if irrelevant_count > len(feedbacks) * 0.7 else "medium"
            })
        
        # 평점이 낮은 경우
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        if ratings and sum(ratings) / len(ratings) < 3.0:
            suggestions.append({
                "type": "low_rating",
                "message": "이 쿼리의 평균 평점이 낮습니다. 벡터 검색 모델을 재학습하거나 쿼리 확장을 고려하세요.",
                "severity": "high" if sum(ratings) / len(ratings) < 2.0 else "medium"
            })
        
        return suggestions
    
    def get_user_feedback_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[SearchFeedback]:
        """
        사용자 피드백 이력 조회
        
        Args:
            user_id: 사용자 ID
            limit: 최대 조회 수
            
        Returns:
            SearchFeedback 리스트
        """
        return self.db.query(SearchFeedback).filter(
            SearchFeedback.user_id == user_id
        ).order_by(desc(SearchFeedback.created_at)).limit(limit).all()

