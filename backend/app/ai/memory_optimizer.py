"""
저사양 환경 최적화
메모리 관리, LRU 캐시, 클러스터링
"""
from typing import Dict, Any, List, Optional, Tuple
from collections import OrderedDict
import numpy as np
from app.core.logging import logger


class LRUCache:
    """LRU (Least Recently Used) 캐시"""
    
    def __init__(self, max_size: int = 100):
        """
        LRU 캐시 초기화
        
        Args:
            max_size: 최대 캐시 크기
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if key in self.cache:
            # 최근 사용된 항목을 맨 뒤로 이동
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any):
        """캐시에 값 저장"""
        if key in self.cache:
            # 기존 항목 업데이트
            self.cache.move_to_end(key)
        else:
            # 새 항목 추가
            if len(self.cache) >= self.max_size:
                # 가장 오래된 항목 제거
                self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self):
        """캐시 비우기"""
        self.cache.clear()
    
    def size(self) -> int:
        """캐시 크기"""
        return len(self.cache)


class HybridMemoryManager:
    """
    하이브리드 메모리 관리
    자주 사용되는 인덱스만 메모리에 캐싱
    """
    
    def __init__(self, memory_limit_mb: int = 2048, cache_size: int = 100):
        """
        하이브리드 메모리 관리자 초기화
        
        Args:
            memory_limit_mb: 메모리 제한 (MB)
            cache_size: LRU 캐시 크기
        """
        self.memory_limit = memory_limit_mb * 1024 * 1024  # bytes
        self.lru_cache = LRUCache(cache_size)
        self.memory_usage = 0
        self.disk_cache: Dict[str, str] = {}  # key -> filepath
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """
        메모리 또는 디스크에서 데이터 가져오기
        
        Args:
            key: 데이터 키
            
        Returns:
            데이터 (numpy array) 또는 None
        """
        # 먼저 LRU 캐시 확인
        data = self.lru_cache.get(key)
        if data is not None:
            return data
        
        # 디스크 캐시 확인
        if key in self.disk_cache:
            filepath = self.disk_cache[key]
            try:
                data = np.load(filepath)
                # 메모리로 로드하고 캐시에 추가
                self._add_to_memory(key, data)
                return data
            except Exception as e:
                logger.warning(f"디스크 캐시 로드 실패: {key} - {e}")
        
        return None
    
    def put(self, key: str, data: np.ndarray, persist: bool = True):
        """
        데이터 저장 (메모리 및 선택적으로 디스크)
        
        Args:
            key: 데이터 키
            data: 데이터 (numpy array)
            persist: 디스크에 영구 저장 여부
        """
        # 메모리 제한 확인
        data_size = data.nbytes
        
        if data_size > self.memory_limit:
            # 데이터가 너무 크면 디스크에만 저장
            if persist:
                self._save_to_disk(key, data)
            return
        
        # 메모리 사용량 확인 및 정리
        while self.memory_usage + data_size > self.memory_limit and self.lru_cache.size() > 0:
            # 가장 오래된 항목 제거
            oldest_key = next(iter(self.lru_cache.cache))
            oldest_data = self.lru_cache.get(oldest_key)
            if oldest_data is not None:
                self.memory_usage -= oldest_data.nbytes
                if persist:
                    self._save_to_disk(oldest_key, oldest_data)
            self.lru_cache.cache.pop(oldest_key, None)
        
        # 메모리에 추가
        self._add_to_memory(key, data)
    
    def _add_to_memory(self, key: str, data: np.ndarray):
        """메모리에 데이터 추가"""
        self.lru_cache.put(key, data)
        self.memory_usage += data.nbytes
    
    def _save_to_disk(self, key: str, data: np.ndarray):
        """디스크에 데이터 저장"""
        import os
        import tempfile
        
        cache_dir = os.path.join(tempfile.gettempdir(), "vector_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        filepath = os.path.join(cache_dir, f"{key}.npy")
        np.save(filepath, data)
        self.disk_cache[key] = filepath
    
    def get_stats(self) -> Dict[str, Any]:
        """메모리 사용 통계"""
        return {
            "memory_usage_mb": self.memory_usage / (1024 * 1024),
            "memory_limit_mb": self.memory_limit / (1024 * 1024),
            "cache_size": self.lru_cache.size(),
            "disk_cache_size": len(self.disk_cache)
        }


class DocumentClustering:
    """
    문서 클러스터링
    유사한 문서들을 그룹화하여 클러스터별 인덱스 구성
    """
    
    def __init__(self, n_clusters: int = 10):
        """
        문서 클러스터링 초기화
        
        Args:
            n_clusters: 클러스터 개수
        """
        self.n_clusters = n_clusters
        self.clusters: Dict[int, List[str]] = {}  # cluster_id -> document_ids
        self.document_cluster: Dict[str, int] = {}  # document_id -> cluster_id
        self.cluster_centroids: Dict[int, np.ndarray] = {}  # cluster_id -> centroid
    
    def fit(self, document_vectors: Dict[str, np.ndarray]):
        """
        문서 클러스터링 수행
        
        Args:
            document_vectors: 문서 ID -> 벡터 매핑
        """
        if len(document_vectors) < self.n_clusters:
            # 문서 수가 클러스터 수보다 적으면 각 문서를 별도 클러스터로
            for i, (doc_id, vector) in enumerate(document_vectors.items()):
                self.clusters[i] = [doc_id]
                self.document_cluster[doc_id] = i
                self.cluster_centroids[i] = vector
            return
        
        try:
            from sklearn.cluster import KMeans
            
            # 벡터 배열 준비
            doc_ids = list(document_vectors.keys())
            vectors = np.array([document_vectors[doc_id] for doc_id in doc_ids])
            
            # K-means 클러스터링
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(vectors)
            
            # 클러스터 구성
            self.clusters = {}
            self.cluster_centroids = {}
            
            for i in range(self.n_clusters):
                cluster_doc_ids = [doc_ids[j] for j in range(len(doc_ids)) if labels[j] == i]
                if cluster_doc_ids:
                    self.clusters[i] = cluster_doc_ids
                    self.cluster_centroids[i] = kmeans.cluster_centers_[i]
                    
                    for doc_id in cluster_doc_ids:
                        self.document_cluster[doc_id] = i
            
            logger.info(f"문서 클러스터링 완료: {len(document_vectors)}개 문서, {len(self.clusters)}개 클러스터")
        
        except ImportError:
            logger.warning("sklearn이 설치되지 않아 클러스터링을 건너뜁니다.")
    
    def get_cluster(self, document_id: str) -> Optional[int]:
        """문서의 클러스터 ID 반환"""
        return self.document_cluster.get(document_id)
    
    def get_cluster_documents(self, cluster_id: int) -> List[str]:
        """클러스터의 문서 ID 리스트 반환"""
        return self.clusters.get(cluster_id, [])
    
    def find_nearest_clusters(self, query_vector: np.ndarray, top_k: int = 3) -> List[int]:
        """
        쿼리 벡터와 가장 가까운 클러스터 찾기
        
        Args:
            query_vector: 쿼리 벡터
            top_k: 반환할 클러스터 개수
            
        Returns:
            클러스터 ID 리스트
        """
        if not self.cluster_centroids:
            return []
        
        # 각 클러스터 중심과의 거리 계산
        distances = []
        for cluster_id, centroid in self.cluster_centroids.items():
            distance = np.linalg.norm(query_vector - centroid)
            distances.append((cluster_id, distance))
        
        # 거리 순으로 정렬
        distances.sort(key=lambda x: x[1])
        
        # 상위 K개 클러스터 반환
        return [cluster_id for cluster_id, _ in distances[:top_k]]

