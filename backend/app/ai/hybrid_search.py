"""
하이브리드 검색 엔진
벡터 유사도 검색(Chroma) + 키워드 검색(BM25) 결합
"""
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

from app.core.logging import logger
from app.ai.vector_store_chroma import ChromaVectorStore
from app.ai.keyword_search import BM25KeywordSearch


class HybridSearchEngine:
    """
    하이브리드 검색 엔진
    
    검색 방식:
    1. 벡터 검색: 의미적 유사도 (Chroma + HNSW)
    2. 키워드 검색: 키워드 매칭 (BM25)
    3. 결과 결합: RRF (Reciprocal Rank Fusion) 또는 가중치 평균
    """
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        """
        하이브리드 검색 엔진 초기화
        
        Args:
            collection_name: Chroma 컬렉션 이름
            persist_directory: Chroma 영속성 디렉토리
            vector_weight: 벡터 검색 가중치 (0~1)
            keyword_weight: 키워드 검색 가중치 (0~1)
        """
        # 벡터 검색 엔진
        self.vector_store = ChromaVectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        
        # 키워드 검색 엔진
        self.keyword_search = BM25KeywordSearch()
        
        # 가중치 설정
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        
        # 가중치 정규화
        total_weight = vector_weight + keyword_weight
        self.vector_weight = vector_weight / total_weight
        self.keyword_weight = keyword_weight / total_weight
        
        # BM25 영속성: Chroma에서 기존 문서 로드하여 BM25 재구성
        self._rebuild_bm25_from_chroma()
        
        logger.info(
            f"하이브리드 검색 엔진 초기화: "
            f"벡터 가중치={self.vector_weight:.2f}, "
            f"키워드 가중치={self.keyword_weight:.2f}"
        )
    
    def _rebuild_bm25_from_chroma(self):
        """
        Chroma 컬렉션에서 기존 문서를 로드하여 BM25 인덱스 재구성
        (영속성 문제 해결 - 재시작 시 BM25 복원)
        
        IMPORTANT: 재구성 전에 BM25 상태를 초기화하여 중복 및 삭제된 문서 방지
        """
        try:
            # Chroma 컬렉션의 모든 문서 가져오기
            count = self.vector_store.collection.count()
            
            if count == 0:
                logger.info("BM25 재구성: Chroma 컬렉션이 비어있음")
                return
            
            # 모든 문서 조회 (limit을 충분히 크게 설정)
            results = self.vector_store.collection.get(
                limit=count,
                include=["metadatas", "documents"]
            )
            
            if not results or not results['ids']:
                logger.info("BM25 재구성: 문서를 찾을 수 없음")
                return
            
            # CRITICAL: BM25 상태 초기화 (중복 및 삭제된 문서 방지)
            self.keyword_search.reset()
            
            # BM25에 문서 추가
            ids = results['ids']
            documents = results['documents']
            metadatas = results['metadatas']
            
            # Content 복원 (metadata에서 또는 documents에서)
            texts = []
            for i, doc in enumerate(documents):
                # 메타데이터에 content가 있으면 사용, 없으면 documents 사용
                if metadatas and i < len(metadatas) and 'content' in metadatas[i]:
                    texts.append(metadatas[i]['content'])
                elif doc:
                    texts.append(doc)
                else:
                    texts.append("")
            
            # BM25 인덱스 재구성
            self.keyword_search.add_documents(texts, metadatas, ids)
            
            logger.info(f"BM25 재구성 완료: {len(ids)}개 문서 로드")
            
        except Exception as e:
            logger.warning(f"BM25 재구성 실패 (신규 컬렉션일 수 있음): {e}")
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        문서 추가 (벡터 + 키워드 인덱싱)
        
        Args:
            texts: 텍스트 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트 (None이면 자동 생성)
            
        Returns:
            추가된 문서 ID 리스트
        """
        if not texts:
            return []
        
        # 벡터 스토어에 추가
        doc_ids = self.vector_store.add_documents(texts, metadatas, ids)
        
        # 키워드 검색 인덱스에 추가
        self.keyword_search.add_documents(texts, metadatas, doc_ids)
        
        logger.info(f"하이브리드 인덱스: 문서 {len(texts)}개 추가")
        
        return doc_ids
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        search_mode: str = "hybrid"
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        하이브리드 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            filter_dict: 메타데이터 필터
            search_mode: 검색 모드 ("hybrid", "vector", "keyword")
            
        Returns:
            (document_id, combined_score, metadata) 튜플 리스트
        """
        if search_mode == "vector":
            # 벡터 검색만
            return self.vector_store.search(query, top_k, filter_dict)
        
        elif search_mode == "keyword":
            # 키워드 검색만
            return self.keyword_search.search(query, top_k, filter_dict)
        
        else:
            # 하이브리드 검색
            return self._hybrid_search(query, top_k, filter_dict)
    
    def _hybrid_search(
        self,
        query: str,
        top_k: int,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        하이브리드 검색 (벡터 + 키워드)
        
        RRF (Reciprocal Rank Fusion) 사용:
        - 각 검색 결과의 순위를 기반으로 점수 계산
        - score = 1 / (rank + k), k=60 (기본값)
        - 두 검색의 점수를 가중치 평균
        """
        # 벡터 검색
        vector_results = self.vector_store.search(query, top_k * 2, filter_dict)
        
        # 키워드 검색
        keyword_results = self.keyword_search.search(query, top_k * 2, filter_dict)
        
        # RRF 상수
        k = 60
        
        # 벡터 검색 결과의 RRF 점수
        vector_scores = {}
        for rank, (doc_id, score, metadata) in enumerate(vector_results):
            rrf_score = 1 / (rank + k)
            vector_scores[doc_id] = {
                'rrf_score': rrf_score,
                'original_score': score,
                'metadata': metadata
            }
        
        # 키워드 검색 결과의 RRF 점수
        keyword_scores = {}
        for rank, (doc_id, score, metadata) in enumerate(keyword_results):
            rrf_score = 1 / (rank + k)
            keyword_scores[doc_id] = {
                'rrf_score': rrf_score,
                'original_score': score,
                'metadata': metadata
            }
        
        # 모든 문서 ID 수집
        all_doc_ids = set(vector_scores.keys()) | set(keyword_scores.keys())
        
        # 하이브리드 점수 계산
        combined_results = []
        for doc_id in all_doc_ids:
            vector_rrf = vector_scores.get(doc_id, {}).get('rrf_score', 0)
            keyword_rrf = keyword_scores.get(doc_id, {}).get('rrf_score', 0)
            
            # 가중치 평균
            combined_score = (
                self.vector_weight * vector_rrf +
                self.keyword_weight * keyword_rrf
            )
            
            # 메타데이터 (벡터 검색 우선)
            metadata = (
                vector_scores.get(doc_id, {}).get('metadata') or
                keyword_scores.get(doc_id, {}).get('metadata', {})
            )
            
            combined_results.append((doc_id, combined_score, metadata))
        
        # 점수 기준 정렬
        combined_results.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 반환
        top_results = combined_results[:top_k]
        
        logger.info(
            f"하이브리드 검색 완료: "
            f"벡터 {len(vector_results)}개, "
            f"키워드 {len(keyword_results)}개, "
            f"결합 {len(top_results)}개"
        )
        
        return top_results
    
    def delete_documents(self, ids: List[str]):
        """
        문서 삭제 (벡터 + 키워드 인덱스)
        
        Args:
            ids: 삭제할 문서 ID 리스트
        """
        if not ids:
            return
        
        self.vector_store.delete_documents(ids)
        self.keyword_search.delete_documents(ids)
        
        logger.info(f"하이브리드 인덱스: 문서 {len(ids)}개 삭제")
    
    def update_documents(
        self,
        ids: List[str],
        texts: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        문서 업데이트 (벡터 + 키워드 인덱스)
        
        Args:
            ids: 업데이트할 문서 ID 리스트
            texts: 새 텍스트 (None이면 유지)
            metadatas: 새 메타데이터 (None이면 유지)
        """
        if not ids:
            return
        
        # 벡터 스토어 업데이트
        self.vector_store.update_documents(ids, texts, metadatas)
        
        # 키워드 검색 업데이트
        if texts is not None and metadatas is not None:
            self.keyword_search.update_documents(ids, texts, metadatas)
        
        logger.info(f"하이브리드 인덱스: 문서 {len(ids)}개 업데이트")
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        vector_stats = self.vector_store.get_stats()
        keyword_stats = self.keyword_search.get_stats()
        
        return {
            "vector_search": vector_stats,
            "keyword_search": keyword_stats,
            "weights": {
                "vector": self.vector_weight,
                "keyword": self.keyword_weight
            }
        }
    
    def reset(self):
        """모든 인덱스 초기화"""
        self.vector_store.reset()
        self.keyword_search.reset()
        logger.warning("하이브리드 인덱스: 초기화 완료")
