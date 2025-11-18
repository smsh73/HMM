"""
Chroma DB 기반 벡터 저장소 (HNSW 인덱싱 지원)
FAISS 대비 장점:
- HNSW 알고리즘으로 고성능 유사도 검색
- 영속성 내장 (별도 저장 로직 불필요)
- 메타데이터 필터링 향상
- 삭제 기능 지원
"""
import os
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    print("Warning: ChromaDB not available. Vector search will not work.")

from app.core.config import settings
from app.core.logging import logger
from app.ai.embedding import EmbeddingGenerator


class ChromaVectorStore:
    """
    Chroma DB 기반 벡터 저장소
    
    저사양 환경 최적화:
    - HNSW M=16 (기본 32 대비 메모리 절약)
    - ef_construction=100 (빌드 속도 vs 품질 균형)
    - ef_search=50 (검색 속도 vs 정확도 균형)
    """
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = None,
        hnsw_m: int = 16,
        hnsw_ef_construction: int = 100,
        hnsw_ef_search: int = 50
    ):
        """
        벡터 저장소 초기화
        
        Args:
            collection_name: 컬렉션 이름
            persist_directory: 영속성 디렉토리 경로
            hnsw_m: HNSW M 파라미터 (메모리와 품질 트레이드오프)
            hnsw_ef_construction: HNSW 빌드 파라미터 (빌드 속도 vs 품질)
            hnsw_ef_search: HNSW 검색 파라미터 (검색 속도 vs 정확도)
        """
        if not HAS_CHROMA:
            raise ImportError("chromadb가 설치되지 않았습니다. pip install chromadb")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.path.join(
            settings.DATA_DIR, "chroma_db"
        )
        
        # HNSW 파라미터 (저사양 최적화)
        self.hnsw_config = {
            "hnsw:space": "cosine",  # 코사인 유사도
            "hnsw:M": hnsw_m,  # 링크 수 (낮을수록 메모리 절약, 기본 32)
            "hnsw:construction_ef": hnsw_ef_construction,  # 빌드 품질 (기본 200)
            "hnsw:search_ef": hnsw_ef_search  # 검색 품질 (기본 10)
        }
        
        # Chroma 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 임베딩 생성기
        self.embedding_generator = EmbeddingGenerator()
        self.dimension = self.embedding_generator.get_embedding_dimension()
        
        # 컬렉션 로드 또는 생성
        self._load_or_create_collection()
        
        logger.info(
            f"Chroma 벡터 스토어 초기화 완료: "
            f"컬렉션={collection_name}, "
            f"차원={self.dimension}, "
            f"HNSW(M={hnsw_m}, ef_construction={hnsw_ef_construction}, "
            f"ef_search={hnsw_ef_search})"
        )
    
    def _load_or_create_collection(self):
        """컬렉션 로드 또는 생성"""
        try:
            # 기존 컬렉션 가져오기 (metadata 파라미터 제거 - 재시작 시 크래시 방지)
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
            logger.info(
                f"기존 컬렉션 로드: {self.collection_name}, "
                f"벡터 수={self.collection.count()}"
            )
        except Exception:
            # 새 컬렉션 생성
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata=self.hnsw_config,
                embedding_function=None  # 직접 임베딩 제공
            )
            logger.info(f"새 컬렉션 생성: {self.collection_name}")
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        문서 추가 및 인덱싱
        
        Args:
            texts: 텍스트 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트 (None이면 자동 생성)
            
        Returns:
            추가된 문서 ID 리스트
        """
        if not texts:
            return []
        
        # 임베딩 생성
        embeddings = self.embedding_generator.generate_embeddings(texts)
        embeddings_list = embeddings.tolist()
        
        # ID 생성 또는 사용
        if ids is None:
            # 자동 ID 생성
            start_id = self.collection.count()
            ids = [f"doc_{start_id + i}" for i in range(len(texts))]
        
        # Chroma에 추가
        self.collection.add(
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"문서 {len(texts)}개 추가 완료 (총 {self.collection.count()}개)")
        
        return ids
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        유사도 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            filter_dict: 메타데이터 필터 (예: {"document_id": "123"})
            
        Returns:
            (document_id, similarity_score, metadata) 튜플 리스트
        """
        if self.collection.count() == 0:
            return []
        
        # 쿼리 임베딩 생성
        query_embedding = self.embedding_generator.generate_embedding(query)
        query_embedding_list = query_embedding.tolist()
        
        # Chroma where 필터 생성
        where_filter = self._build_where_filter(filter_dict) if filter_dict else None
        
        # 검색
        results = self.collection.query(
            query_embeddings=[query_embedding_list],
            n_results=min(top_k, self.collection.count()),
            where=where_filter
        )
        
        # 결과 구성
        output = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                # 거리를 유사도로 변환 (Chroma는 L2 거리 반환)
                # 코사인 유사도를 사용하므로 1 - distance/2로 변환
                distance = results['distances'][0][i]
                similarity = 1 - (distance / 2)  # 0~1 범위로 정규화
                
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                
                output.append((doc_id, similarity, metadata))
        
        logger.debug(f"검색 완료: 쿼리='{query[:50]}...', 결과={len(output)}개")
        
        return output
    
    def _build_where_filter(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chroma where 필터 구성
        
        Args:
            filter_dict: 필터 딕셔너리 {"key": "value"}
            
        Returns:
            Chroma where 필터 구조
        """
        if not filter_dict:
            return None
        
        # 여러 조건을 AND로 결합
        if len(filter_dict) == 1:
            key, value = list(filter_dict.items())[0]
            return {key: {"$eq": value}}
        else:
            conditions = [
                {key: {"$eq": value}}
                for key, value in filter_dict.items()
            ]
            return {"$and": conditions}
    
    def delete_documents(self, ids: List[str]):
        """
        문서 삭제
        
        Args:
            ids: 삭제할 문서 ID 리스트
        """
        if not ids:
            return
        
        try:
            self.collection.delete(ids=ids)
            logger.info(f"문서 {len(ids)}개 삭제 완료")
        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            raise
    
    def update_documents(
        self,
        ids: List[str],
        texts: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        문서 업데이트
        
        Args:
            ids: 업데이트할 문서 ID 리스트
            texts: 새 텍스트 (None이면 유지)
            metadatas: 새 메타데이터 (None이면 유지)
        """
        if not ids:
            return
        
        update_kwargs = {"ids": ids}
        
        if texts is not None:
            embeddings = self.embedding_generator.generate_embeddings(texts)
            update_kwargs["embeddings"] = embeddings.tolist()
            update_kwargs["documents"] = texts
        
        if metadatas is not None:
            update_kwargs["metadatas"] = metadatas
        
        try:
            self.collection.update(**update_kwargs)
            logger.info(f"문서 {len(ids)}개 업데이트 완료")
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """벡터 저장소 통계"""
        return {
            "collection_name": self.collection_name,
            "total_vectors": self.collection.count(),
            "dimension": self.dimension,
            "hnsw_config": self.hnsw_config,
            "persist_directory": self.persist_directory
        }
    
    def reset(self):
        """컬렉션 초기화 (모든 데이터 삭제)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.warning(f"컬렉션 삭제: {self.collection_name}")
            self._load_or_create_collection()
            logger.info(f"컬렉션 재생성: {self.collection_name}")
        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {e}")
            raise
    
    def create_snapshot(self, snapshot_name: str) -> str:
        """
        스냅샷 생성 (백업)
        
        Args:
            snapshot_name: 스냅샷 이름
            
        Returns:
            스냅샷 경로
        """
        snapshot_dir = os.path.join(self.persist_directory, "snapshots", snapshot_name)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Chroma 데이터 복사 (간단히 persist directory 복사)
        import shutil
        shutil.copytree(
            self.persist_directory,
            snapshot_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns('snapshots')
        )
        
        logger.info(f"스냅샷 생성 완료: {snapshot_dir}")
        return snapshot_dir
