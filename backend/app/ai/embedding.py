"""
임베딩 생성 모듈 - Fallback version without ML libraries
"""
from typing import List
import os
import hashlib

from app.core.config import settings

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    print("Warning: ML libraries not available. Using stub implementation.")


class EmbeddingGenerator:
    """임베딩 생성기"""
    
    def __init__(self, model_name: str = None):
        """임베딩 모델 초기화"""
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
        if HAS_ML_LIBS:
            self._load_model()
    
    def _load_model(self):
        """모델 로드 (지연 로딩)"""
        if HAS_ML_LIBS and self.model is None:
            print(f"임베딩 모델 로딩: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("임베딩 모델 로딩 완료")
    
    def generate_embedding(self, text: str):
        """단일 텍스트 임베딩 생성"""
        if HAS_ML_LIBS:
            self._load_model()
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        else:
            # Fallback: simple hash-based mock embedding
            hash_val = hashlib.md5(text.encode()).digest()
            return [float(b) / 255.0 for b in hash_val[:16]]
    
    def generate_embeddings(self, texts: List[str], batch_size: int = None):
        """여러 텍스트 임베딩 생성 (배치 처리)"""
        if HAS_ML_LIBS:
            self._load_model()
            batch_size = batch_size or settings.BATCH_SIZE
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            return embeddings
        else:
            # Fallback
            return [self.generate_embedding(text) for text in texts]
    
    def get_embedding_dimension(self) -> int:
        """임베딩 차원 반환"""
        if HAS_ML_LIBS:
            self._load_model()
            return self.model.get_sentence_embedding_dimension()
        else:
            return 16  # Mock dimension
