"""
벡터 데이터베이스 샤딩
분산 저장 및 독립적 검색/업데이트
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import hashlib
from app.core.logging import logger


class VectorSharding:
    """
    벡터 데이터베이스 샤딩
    문서를 여러 샤드로 분산 저장
    """
    
    def __init__(self, n_shards: int = 4):
        """
        벡터 샤딩 초기화
        
        Args:
            n_shards: 샤드 개수
        """
        self.n_shards = n_shards
        self.shards: Dict[int, Dict[str, Any]] = {
            i: {"vectors": [], "metadata": []} for i in range(n_shards)
        }
    
    def get_shard_id(self, document_id: str) -> int:
        """
        문서 ID를 기반으로 샤드 ID 결정
        
        Args:
            document_id: 문서 ID
            
        Returns:
            샤드 ID (0 ~ n_shards-1)
        """
        # 해시 함수를 사용하여 샤드 결정
        hash_value = int(hashlib.md5(document_id.encode()).hexdigest(), 16)
        shard_id = hash_value % self.n_shards
        return shard_id
    
    def add_document(
        self,
        document_id: str,
        vectors: np.ndarray,
        metadata: List[Dict[str, Any]]
    ) -> Dict[int, List[str]]:
        """
        문서를 샤드에 추가
        
        Args:
            document_id: 문서 ID
            vectors: 벡터 배열 (N, D)
            metadata: 메타데이터 리스트
            
        Returns:
            샤드 ID -> 벡터 ID 리스트 매핑
        """
        shard_id = self.get_shard_id(document_id)
        shard = self.shards[shard_id]
        
        # 벡터 ID 생성
        start_id = len(shard["vectors"])
        vector_ids = [
            f"shard_{shard_id}_vec_{start_id + i}"
            for i in range(len(vectors))
        ]
        
        # 샤드에 추가
        shard["vectors"].extend(vectors)
        shard["metadata"].extend(metadata)
        
        logger.info(
            f"문서 샤드 추가: {document_id} -> 샤드 {shard_id}, "
            f"{len(vectors)}개 벡터"
        )
        
        return {shard_id: vector_ids}
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        shard_ids: Optional[List[int]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        샤드에서 검색
        
        Args:
            query_vector: 쿼리 벡터
            top_k: 반환할 최대 결과 수
            shard_ids: 검색할 샤드 ID 리스트 (None이면 모든 샤드)
            
        Returns:
            (vector_id, similarity, metadata) 튜플 리스트
        """
        if shard_ids is None:
            shard_ids = list(range(self.n_shards))
        
        all_results = []
        
        # 각 샤드에서 검색
        for shard_id in shard_ids:
            shard = self.shards[shard_id]
            
            if not shard["vectors"]:
                continue
            
            vectors = np.array(shard["vectors"])
            metadatas = shard["metadata"]
            
            # 코사인 유사도 계산
            similarities = np.dot(vectors, query_vector) / (
                np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vector)
            )
            
            # 상위 K개 선택
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            for idx in top_indices:
                vector_id = f"shard_{shard_id}_vec_{idx}"
                similarity = float(similarities[idx])
                metadata = metadatas[idx] if idx < len(metadatas) else {}
                
                all_results.append((vector_id, similarity, metadata))
        
        # 전체 결과에서 상위 K개 선택
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        return all_results[:top_k]
    
    def get_shard_stats(self) -> Dict[int, Dict[str, Any]]:
        """샤드 통계 조회"""
        stats = {}
        for shard_id, shard in self.shards.items():
            stats[shard_id] = {
                "vector_count": len(shard["vectors"]),
                "metadata_count": len(shard["metadata"])
            }
        return stats


class MultiLayerCache:
    """
    다층 캐싱
    메모리 → SSD → 네트워크 캐시
    """
    
    def __init__(self):
        """다층 캐시 초기화"""
        self.memory_cache: Dict[str, Any] = {}  # L1: 메모리
        self.ssd_cache: Dict[str, str] = {}  # L2: SSD (filepath)
        self.network_cache: Dict[str, str] = {}  # L3: 네트워크 (URL)
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 데이터 가져오기
        
        Args:
            key: 캐시 키
            
        Returns:
            데이터 또는 None
        """
        # L1: 메모리 캐시 확인
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # L2: SSD 캐시 확인
        if key in self.ssd_cache:
            import numpy as np
            filepath = self.ssd_cache[key]
            try:
                data = np.load(filepath)
                # 메모리 캐시로 승격
                self.memory_cache[key] = data
                return data
            except Exception as e:
                logger.warning(f"SSD 캐시 로드 실패: {key} - {e}")
        
        # L3: 네트워크 캐시 확인
        if key in self.network_cache:
            # TODO: 네트워크에서 다운로드
            pass
        
        return None
    
    def put(self, key: str, data: Any, level: int = 1):
        """
        캐시에 데이터 저장
        
        Args:
            key: 캐시 키
            data: 데이터
            level: 캐시 레벨 (1=메모리, 2=SSD, 3=네트워크)
        """
        if level >= 1:
            self.memory_cache[key] = data
        
        if level >= 2:
            import numpy as np
            import os
            import tempfile
            
            cache_dir = os.path.join(tempfile.gettempdir(), "vector_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            filepath = os.path.join(cache_dir, f"{key}.npy")
            np.save(filepath, data)
            self.ssd_cache[key] = filepath
        
        if level >= 3:
            # TODO: 네트워크 캐시에 업로드
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        return {
            "memory_cache_size": len(self.memory_cache),
            "ssd_cache_size": len(self.ssd_cache),
            "network_cache_size": len(self.network_cache)
        }

