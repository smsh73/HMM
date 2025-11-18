"""
BM25 기반 키워드 검색
하이브리드 검색의 키워드 검색 컴포넌트
"""
from typing import List, Dict, Any, Tuple
import re
from collections import defaultdict

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    print("Warning: rank-bm25 not available. Keyword search will not work.")

from app.core.logging import logger


class BM25KeywordSearch:
    """
    BM25 알고리즘 기반 키워드 검색
    
    BM25 (Best Matching 25):
    - TF-IDF의 확률론적 변형
    - 문서 길이 정규화 지원
    - 높은 키워드 검색 정확도
    """
    
    def __init__(self):
        """키워드 검색 엔진 초기화"""
        if not HAS_BM25:
            raise ImportError("rank-bm25가 설치되지 않았습니다. pip install rank-bm25")
        
        self.bm25 = None
        self.documents = []  # 원본 문서 리스트
        self.tokenized_docs = []  # 토큰화된 문서 리스트
        self.doc_ids = []  # 문서 ID 리스트
        self.metadatas = []  # 메타데이터 리스트
        
        logger.info("BM25 키워드 검색 엔진 초기화 완료")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        텍스트 토큰화
        
        Args:
            text: 원본 텍스트
            
        Returns:
            토큰 리스트
        """
        # 소문자 변환 및 특수 문자 제거
        text = text.lower()
        
        # 한글, 영문, 숫자만 추출
        tokens = re.findall(r'[가-힣a-z0-9]+', text)
        
        return tokens
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        문서 추가 및 인덱싱
        
        Args:
            texts: 텍스트 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트
        """
        if not texts:
            return
        
        # 문서 저장
        self.documents.extend(texts)
        self.doc_ids.extend(ids)
        self.metadatas.extend(metadatas)
        
        # 토큰화
        for text in texts:
            tokens = self._tokenize(text)
            self.tokenized_docs.append(tokens)
        
        # BM25 인덱스 재구성
        self._rebuild_index()
        
        logger.info(f"BM25: 문서 {len(texts)}개 추가 (총 {len(self.documents)}개)")
    
    def _rebuild_index(self):
        """BM25 인덱스 재구성"""
        if self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)
            logger.debug(f"BM25 인덱스 재구성 완료: {len(self.tokenized_docs)}개 문서")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        키워드 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            filter_dict: 메타데이터 필터
            
        Returns:
            (document_id, score, metadata) 튜플 리스트
        """
        if not self.bm25 or len(self.documents) == 0:
            return []
        
        # 쿼리 토큰화
        query_tokens = self._tokenize(query)
        
        # BM25 점수 계산
        scores = self.bm25.get_scores(query_tokens)
        
        # (인덱스, 점수) 쌍으로 정렬
        scored_indices = [
            (i, score) for i, score in enumerate(scores)
            if score > 0  # 점수가 0보다 큰 것만
        ]
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 추출
        results = []
        for idx, score in scored_indices[:top_k]:
            doc_id = self.doc_ids[idx]
            metadata = self.metadatas[idx]
            
            # 필터 적용
            if filter_dict:
                if not self._matches_filter(metadata, filter_dict):
                    continue
            
            # 점수 정규화 (0~1 범위)
            normalized_score = min(score / 10.0, 1.0)
            
            results.append((doc_id, normalized_score, metadata))
        
        logger.debug(f"BM25 검색 완료: 쿼리='{query[:50]}...', 결과={len(results)}개")
        
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """메타데이터 필터 매칭"""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def delete_documents(self, ids: List[str]):
        """
        문서 삭제
        
        Args:
            ids: 삭제할 문서 ID 리스트
        """
        if not ids:
            return
        
        # 삭제할 인덱스 찾기
        indices_to_remove = []
        for i, doc_id in enumerate(self.doc_ids):
            if doc_id in ids:
                indices_to_remove.append(i)
        
        # 역순으로 삭제 (인덱스 변경 방지)
        for idx in sorted(indices_to_remove, reverse=True):
            del self.documents[idx]
            del self.doc_ids[idx]
            del self.metadatas[idx]
            del self.tokenized_docs[idx]
        
        # 인덱스 재구성
        self._rebuild_index()
        
        logger.info(f"BM25: 문서 {len(indices_to_remove)}개 삭제")
    
    def update_documents(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        """
        문서 업데이트
        
        Args:
            ids: 업데이트할 문서 ID 리스트
            texts: 새 텍스트 리스트
            metadatas: 새 메타데이터 리스트
        """
        if not ids:
            return
        
        # 기존 문서 찾아서 업데이트
        for i, doc_id in enumerate(self.doc_ids):
            if doc_id in ids:
                idx_in_update = ids.index(doc_id)
                self.documents[i] = texts[idx_in_update]
                self.metadatas[i] = metadatas[idx_in_update]
                self.tokenized_docs[i] = self._tokenize(texts[idx_in_update])
        
        # 인덱스 재구성
        self._rebuild_index()
        
        logger.info(f"BM25: 문서 {len(ids)}개 업데이트")
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        return {
            "total_documents": len(self.documents),
            "total_tokens": sum(len(doc) for doc in self.tokenized_docs),
            "avg_doc_length": (
                sum(len(doc) for doc in self.tokenized_docs) / len(self.tokenized_docs)
                if self.tokenized_docs else 0
            )
        }
    
    def reset(self):
        """모든 데이터 초기화"""
        self.bm25 = None
        self.documents = []
        self.tokenized_docs = []
        self.doc_ids = []
        self.metadatas = []
        logger.info("BM25: 초기화 완료")
