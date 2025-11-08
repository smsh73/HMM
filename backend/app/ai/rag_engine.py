"""
RAG 검색 엔진
"""
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from app.core.config import settings
from app.ai.vector_store import VectorStore
from app.ai.embedding import EmbeddingGenerator
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


class RAGSearchEngine:
    """RAG 기반 검색 엔진"""
    
    def __init__(self, vector_db_path: str = None, llm_provider: Optional[LLMProvider] = None):
        """RAG 검색 엔진 초기화"""
        self.vector_store = VectorStore(vector_db_path)
        self.llm_provider = llm_provider
    
    def index_document(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """문서 인덱싱"""
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": chunk["chunk_index"],
                **chunk.get("metadata", {})
            }
            for chunk in chunks
        ]
        
        vector_ids = self.vector_store.add_documents(texts, metadatas)
        return vector_ids
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """의미 기반 검색"""
        results = self.vector_store.search(query, top_k, filter_dict)
        
        search_results = []
        for vector_id, score, metadata in results:
            search_results.append(SearchResult(
                content=metadata.get("content", ""),
                score=score,
                document_id=metadata.get("document_id", ""),
                chunk_index=metadata.get("chunk_index", 0),
                metadata=metadata
            ))
        
        return search_results
    
    async def generate_answer(
        self,
        query: str,
        context_results: List[SearchResult],
        llm_provider: Optional[LLMProvider] = None
    ) -> AnswerWithSources:
        """검색 결과 기반 답변 생성"""
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
        
        # 프롬프트 구성
        prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.

문서 내용:
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
            print(f"LLM 답변 생성 오류: {e}")
            answer = "답변 생성 중 오류가 발생했습니다."
        
        # 신뢰도 계산 (검색 결과 점수의 평균)
        confidence = sum(r.score for r in context_results) / len(context_results) if context_results else 0.0
        
        return AnswerWithSources(
            answer=answer,
            sources=context_results,
            confidence=confidence
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """검색 엔진 통계"""
        return self.vector_store.get_stats()

