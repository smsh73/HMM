"""
검색 서비스
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.database import SearchHistory, User
from app.ai.rag_engine import RAGSearchEngine, SearchResult, AnswerWithSources
from app.services.llm_service import LLMService


class SearchService:
    """검색 서비스"""
    
    def __init__(self, db: Session):
        """검색 서비스 초기화"""
        self.db = db
        self.rag_engine = RAGSearchEngine()
        self.llm_service = LLMService(db)
    
    async def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        generate_answer: bool = False,
        filter_dict: Dict[str, Any] = None,
        use_main_system: bool = True,
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """검색 수행"""
        # 검색 수행
        search_results = self.rag_engine.semantic_search(
            query=query,
            top_k=top_k,
            filter_dict=filter_dict
        )
        
        # 답변 생성 (요청 시)
        answer = None
        if generate_answer:
            # LLM 프로바이더 가져오기
            llm_provider = self.llm_service.get_provider(
                provider_name=provider_name,
                use_main_system=use_main_system
            )
            answer = await self.rag_engine.generate_answer(
                query, 
                search_results,
                llm_provider=llm_provider
            )
        
        # 검색 기록 저장
        search_history = SearchHistory(
            user_id=user_id,
            query=query,
            results_count=len(search_results)
        )
        self.db.add(search_history)
        self.db.commit()
        
        return {
            "query": query,
            "results": [
                {
                    "content": result.content,
                    "score": result.score,
                    "document_id": result.document_id,
                    "chunk_index": result.chunk_index,
                    "metadata": result.metadata
                }
                for result in search_results
            ],
            "answer": {
                "answer": answer.answer,
                "sources": [
                    {
                        "content": src.content,
                        "document_id": src.document_id,
                        "score": src.score
                    }
                    for src in answer.sources
                ],
                "confidence": answer.confidence
            } if answer else None,
            "total_results": len(search_results)
        }
    
    def get_search_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """검색 기록 조회"""
        history = self.db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(
            SearchHistory.search_date.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": h.id,
                "query": h.query,
                "results_count": h.results_count,
                "search_date": h.search_date.isoformat()
            }
            for h in history
        ]
    
    def get_search_suggestions(
        self,
        query_prefix: str,
        limit: int = 5
    ) -> List[str]:
        """검색 제안 (검색 기록 기반)"""
        # 간단한 구현: 검색 기록에서 유사한 쿼리 찾기
        history = self.db.query(SearchHistory).filter(
            SearchHistory.query.like(f"%{query_prefix}%")
        ).distinct().limit(limit).all()
        
        return [h.query for h in history]

