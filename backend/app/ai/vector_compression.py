"""
벡터 압축 및 양자화
Product Quantization (PQ) 기법 적용
"""
import numpy as np
from typing import List, Tuple, Optional
import pickle
import gzip
from app.core.logging import logger

try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("sklearn not available. PQ will use fallback clustering.")


class ProductQuantization:
    """
    Product Quantization (PQ) 기법
    32비트 float 벡터를 4비트/5비트로 압축
    """
    
    def __init__(self, n_subvectors: int = 8, n_clusters: int = 16):
        """
        PQ 초기화
        
        Args:
            n_subvectors: 부벡터 개수 (원본 벡터를 나눌 개수)
            n_clusters: 클러스터 개수 (코드북 크기, 16 = 4비트)
        """
        self.n_subvectors = n_subvectors
        self.n_clusters = n_clusters
        self.codebooks: List[np.ndarray] = []  # 각 부벡터별 코드북
        self.subvector_dim: int = 0  # 부벡터 차원
    
    def fit(self, vectors: np.ndarray):
        """
        코드북 학습
        
        Args:
            vectors: 학습용 벡터 배열 (N, D)
        """
        n_vectors, vector_dim = vectors.shape
        
        # 부벡터 차원 계산
        self.subvector_dim = vector_dim // self.n_subvectors
        
        logger.info(f"PQ 학습 시작: {n_vectors}개 벡터, {vector_dim}차원")
        
        # 각 부벡터별로 코드북 학습
        if not HAS_SKLEARN:
            raise ImportError("sklearn이 설치되지 않았습니다. pip install scikit-learn")
        
        self.codebooks = []
        for i in range(self.n_subvectors):
            start_idx = i * self.subvector_dim
            end_idx = start_idx + self.subvector_dim
            
            # 부벡터 추출
            subvectors = vectors[:, start_idx:end_idx]
            
            # K-means 클러스터링으로 코드북 생성
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            kmeans.fit(subvectors)
            
            self.codebooks.append(kmeans.cluster_centers_)
            
            logger.debug(f"부벡터 {i+1}/{self.n_subvectors} 코드북 생성 완료")
        
        logger.info("PQ 코드북 학습 완료")
    
    def encode(self, vectors: np.ndarray) -> np.ndarray:
        """
        벡터 인코딩 (압축)
        
        Args:
            vectors: 인코딩할 벡터 배열 (N, D)
            
        Returns:
            압축된 코드 배열 (N, n_subvectors) - 각 값은 0~n_clusters-1
        """
        n_vectors, vector_dim = vectors.shape
        codes = np.zeros((n_vectors, self.n_subvectors), dtype=np.uint8)
        
        for i in range(self.n_subvectors):
            start_idx = i * self.subvector_dim
            end_idx = start_idx + self.subvector_dim
            
            # 부벡터 추출
            subvectors = vectors[:, start_idx:end_idx]
            
            # 가장 가까운 코드북 벡터 찾기
            codebook = self.codebooks[i]
            distances = np.linalg.norm(
                subvectors[:, np.newaxis, :] - codebook[np.newaxis, :, :],
                axis=2
            )
            codes[:, i] = np.argmin(distances, axis=1)
        
        return codes
    
    def decode(self, codes: np.ndarray) -> np.ndarray:
        """
        벡터 디코딩 (복원)
        
        Args:
            codes: 압축된 코드 배열 (N, n_subvectors)
            
        Returns:
            복원된 벡터 배열 (N, D)
        """
        n_vectors = codes.shape[0]
        vector_dim = self.subvector_dim * self.n_subvectors
        decoded = np.zeros((n_vectors, vector_dim), dtype=np.float32)
        
        for i in range(self.n_subvectors):
            start_idx = i * self.subvector_dim
            end_idx = start_idx + self.subvector_dim
            
            # 코드북에서 해당 코드의 벡터 가져오기
            codebook = self.codebooks[i]
            decoded[:, start_idx:end_idx] = codebook[codes[:, i]]
        
        return decoded
    
    def save(self, filepath: str):
        """코드북 저장"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'n_subvectors': self.n_subvectors,
                'n_clusters': self.n_clusters,
                'subvector_dim': self.subvector_dim,
                'codebooks': self.codebooks
            }, f)
        logger.info(f"PQ 코드북 저장: {filepath}")
    
    def load(self, filepath: str):
        """코드북 로드"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.n_subvectors = data['n_subvectors']
            self.n_clusters = data['n_clusters']
            self.subvector_dim = data['subvector_dim']
            self.codebooks = data['codebooks']
        logger.info(f"PQ 코드북 로드: {filepath}")


class VectorCompressor:
    """벡터 압축기 (PQ + GZIP)"""
    
    def __init__(self, use_pq: bool = True, pq_n_subvectors: int = 8, pq_n_clusters: int = 16):
        """
        벡터 압축기 초기화
        
        Args:
            use_pq: Product Quantization 사용 여부
            pq_n_subvectors: PQ 부벡터 개수
            pq_n_clusters: PQ 클러스터 개수 (16 = 4비트, 32 = 5비트)
        """
        self.use_pq = use_pq
        self.pq = ProductQuantization(pq_n_subvectors, pq_n_clusters) if use_pq else None
        self.pq_trained = False
    
    def train_pq(self, sample_vectors: np.ndarray):
        """PQ 코드북 학습"""
        if self.pq:
            self.pq.fit(sample_vectors)
            self.pq_trained = True
    
    def compress_vectors(self, vectors: np.ndarray) -> bytes:
        """
        벡터 압축
        
        Args:
            vectors: 압축할 벡터 배열 (N, D)
            
        Returns:
            압축된 바이트 데이터
        """
        if self.use_pq and self.pq_trained:
            # PQ 인코딩
            codes = self.pq.encode(vectors)
            # 바이트로 변환
            data = codes.tobytes()
        else:
            # PQ 없이 직접 바이트 변환
            data = vectors.tobytes()
        
        # GZIP 압축
        compressed = gzip.compress(data)
        
        compression_ratio = len(data) / len(compressed) if len(compressed) > 0 else 1.0
        logger.info(f"벡터 압축 완료: {len(vectors)}개, 압축률 {compression_ratio:.2f}x")
        
        return compressed
    
    def decompress_vectors(self, compressed_data: bytes, original_shape: Tuple[int, int]) -> np.ndarray:
        """
        벡터 압축 해제
        
        Args:
            compressed_data: 압축된 바이트 데이터
            original_shape: 원본 벡터 형태 (N, D)
            
        Returns:
            복원된 벡터 배열
        """
        # GZIP 압축 해제
        data = gzip.decompress(compressed_data)
        
        if self.use_pq and self.pq_trained:
            # PQ 디코딩
            n_vectors, vector_dim = original_shape
            n_subvectors = self.pq.n_subvectors
            codes = np.frombuffer(data, dtype=np.uint8).reshape(n_vectors, n_subvectors)
            vectors = self.pq.decode(codes)
        else:
            # 직접 복원
            vectors = np.frombuffer(data, dtype=np.float32).reshape(original_shape)
        
        logger.info(f"벡터 압축 해제 완료: {original_shape}")
        
        return vectors

