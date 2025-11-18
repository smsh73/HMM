"""
하이브리드 RAG 검색 엔진 (Chroma + BM25 기반)
기존 RAGSearchEngine의 업그레이드 버전
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import logger
from app.ai.hybrid_search import HybridSearchEngine
from app.ai.llm_providers import LLMProvider


@dataclass
class SearchResult:
    """검색 결과"""
    content: str
    score: float
    document_id: str
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class AnswerWithSources:
    """출처가 포함된 답변"""
    answer: str
    sources: List[SearchResult]
    confidence: float


class HybridRAGEngine:
    """
    Hybrid RAG 검색 엔진
    
    특징:
    - Chroma 벡터 검색 (HNSW 인덱싱)
    - BM25 키워드 검색
    - RRF 기반 하이브리드 검색
    - LLM 기반 답변 생성
    """
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = None,
        llm_provider: Optional[LLMProvider] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        """
        Hybrid RAG 엔진 초기화
        
        Args:
            collection_name: Chroma 컬렉션 이름
            persist_directory: Chroma 영속성 디렉토리
            llm_provider: LLM 프로바이더
            vector_weight: 벡터 검색 가중치
            keyword_weight: 키워드 검색 가중치
        """
        self.hybrid_search = HybridSearchEngine(
            collection_name=collection_name,
            persist_directory=persist_directory,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight
        )
        self.llm_provider = llm_provider
        
        logger.info(
            f"Hybrid RAG 엔진 초기화: "
            f"컬렉션={collection_name}, "
            f"가중치(벡터={vector_weight}, 키워드={keyword_weight})"
        )
    
    def index_document(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        문서 인덱싱 (Chroma + BM25)
        
        Args:
            document_id: 문서 ID
            chunks: 청크 리스트 [{"content": str, "chunk_index": int, "metadata": dict}, ...]
            
        Returns:
            인덱싱된 문서 ID 리스트
        """
        # 텍스트 및 메타데이터 준비
        # IMPORTANT: content를 메타데이터에 포함 (검색 시 SearchResult에 필요)
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],  # 검색 결과에 필요 (RAG용)
                **chunk.get("metadata", {})
            }
            for chunk in chunks
        ]
        
        # 하이브리드 인덱싱
        doc_ids = self.hybrid_search.add_documents(texts, metadatas)
        
        logger.info(f"문서 인덱싱 완료: {document_id}, {len(doc_ids)}개 청크")
        
        return doc_ids
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None,
        search_mode: str = "hybrid"
    ) -> List[SearchResult]:
        """
        하이브리드 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            filter_dict: 메타데이터 필터
            search_mode: 검색 모드 ("hybrid", "vector", "keyword")
            
        Returns:
            검색 결과 리스트
        """
        # 하이브리드 검색 수행
        results = self.hybrid_search.search(query, top_k, filter_dict, search_mode)
        
        # SearchResult 객체로 변환
        search_results = []
        for doc_id, score, metadata in results:
            search_results.append(SearchResult(
                content=metadata.get("content", ""),
                score=score,
                document_id=metadata.get("document_id", ""),
                chunk_index=metadata.get("chunk_index", 0),
                metadata=metadata
            ))
        
        logger.debug(
            f"검색 완료: 모드={search_mode}, 쿼리='{query[:50]}...', 결과={len(search_results)}개"
        )
        
        return search_results
    
    async def generate_answer(
        self,
        query: str,
        context_results: List[SearchResult],
        llm_provider: Optional[LLMProvider] = None
    ) -> AnswerWithSources:
        """
        검색 결과 기반 답변 생성 (한글 프롬프트)
        
        Args:
            query: 질문
            context_results: 검색 결과 (컨텍스트)
            llm_provider: LLM 프로바이더 (None이면 기본 사용)
            
        Returns:
            답변 및 출처
        """
        if not context_results:
            return AnswerWithSources(
                answer="관련 문서를 찾을 수 없습니다.",
                sources=[],
                confidence=0.0
            )
        
        # 컨텍스트 구성
        context_text = "\n\n".join([
            f"[문서 {i+1}]\n{result.content}"
            for i, result in enumerate(context_results)
        ])
        
        # 한글 프롬프트 구성
        prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.
답변은 한국어로 작성하고, 문서에 있는 정보만을 기반으로 답변해주세요.

참고 문서:
{context_text}

질문: {query}

답변:"""
        
        # LLM 프로바이더를 통한 답변 생성
        provider = llm_provider or self.llm_provider
        if not provider:
            # 기본 Ollama 사용
            from app.ai.llm_providers import OllamaProvider
            provider = OllamaProvider(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL
            )
        
        try:
            answer = await provider.generate(prompt)
        except Exception as e:
            logger.error(f"LLM 답변 생성 오류: {e}")
            answer = f"답변 생성 중 오류가 발생했습니다: {str(e)}"
        
        # 신뢰도 계산 (검색 결과 점수의 평균)
        confidence = sum(r.score for r in context_results) / len(context_results) if context_results else 0.0
        
        return AnswerWithSources(
            answer=answer,
            sources=context_results,
            confidence=confidence
        )
    
    def delete_documents(self, document_ids: List[str]):
        """
        문서 삭제
        
        Args:
            document_ids: 삭제할 문서 ID 리스트
        """
        self.hybrid_search.delete_documents(document_ids)
        logger.info(f"문서 삭제: {len(document_ids)}개")
    
    def update_documents(
        self,
        document_ids: List[str],
        chunks: List[Dict[str, Any]]
    ):
        """
        문서 업데이트
        
        Args:
            document_ids: 업데이트할 문서 ID 리스트
            chunks: 새 청크 리스트
        """
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [
            {
                "document_id": document_ids[i] if i < len(document_ids) else "",
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                **chunk.get("metadata", {})
            }
            for i, chunk in enumerate(chunks)
        ]
        
        self.hybrid_search.update_documents(document_ids, texts, metadatas)
        logger.info(f"문서 업데이트: {len(document_ids)}개")
    
    def get_stats(self) -> Dict[str, Any]:
        """검색 엔진 통계"""
        return self.hybrid_search.get_stats()
