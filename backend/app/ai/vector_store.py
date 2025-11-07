"""
벡터 저장소 관리
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict, Any
from pathlib import Path

from app.core.config import settings
from app.ai.embedding import EmbeddingGenerator


class VectorStore:
    """FAISS 기반 벡터 저장소"""
    
    def __init__(self, vector_db_path: str = None):
        """벡터 저장소 초기화"""
        self.vector_db_path = vector_db_path or settings.VECTOR_DB_PATH
        self.index = None
        self.metadata_store = {}  # {vector_id: metadata}
        self.embedding_generator = EmbeddingGenerator()
        self.dimension = self.embedding_generator.get_embedding_dimension()
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """인덱스 로드 또는 생성"""
        index_path = os.path.join(self.vector_db_path, "faiss.index")
        metadata_path = os.path.join(self.vector_db_path, "metadata.pkl")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            # 기존 인덱스 로드
            self.index = faiss.read_index(index_path)
            with open(metadata_path, 'rb') as f:
                self.metadata_store = pickle.load(f)
            print(f"벡터 인덱스 로드 완료: {self.index.ntotal}개 벡터")
        else:
            # 새 인덱스 생성
            self.index = faiss.IndexFlatL2(self.dimension)
            print(f"새 벡터 인덱스 생성: 차원 {self.dimension}")
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """문서 추가 및 인덱싱"""
        if not texts:
            return []
        
        # 임베딩 생성
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        # 벡터 ID 생성
        start_id = self.index.ntotal
        vector_ids = [str(start_id + i) for i in range(len(texts))]
        
        # 인덱스에 추가
        self.index.add(embeddings.astype('float32'))
        
        # 메타데이터 저장
        for vector_id, metadata in zip(vector_ids, metadatas):
            self.metadata_store[vector_id] = metadata
        
        # 저장
        self._save_index()
        
        return vector_ids
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """유사도 검색"""
        if self.index.ntotal == 0:
            return []
        
        # 쿼리 임베딩 생성
        query_embedding = self.embedding_generator.generate_embedding(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # 검색
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)
        
        # 결과 구성
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS의 빈 결과
                continue
            
            vector_id = str(idx)
            metadata = self.metadata_store.get(vector_id, {})
            
            # 필터 적용
            if filter_dict:
                if not self._matches_filter(metadata, filter_dict):
                    continue
            
            # 거리를 유사도 점수로 변환 (L2 거리이므로 낮을수록 유사)
            similarity = 1 / (1 + distance)
            
            results.append((vector_id, similarity, metadata))
        
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """메타데이터 필터 매칭"""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def delete_documents(self, vector_ids: List[str]):
        """문서 삭제 (FAISS는 삭제를 직접 지원하지 않으므로 재구성 필요)"""
        # FAISS는 삭제를 직접 지원하지 않으므로
        # 전체 인덱스를 재구성해야 함
        # 실제 운영 환경에서는 더 효율적인 방법 고려 필요
        pass
    
    def _save_index(self):
        """인덱스 저장"""
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        index_path = os.path.join(self.vector_db_path, "faiss.index")
        metadata_path = os.path.join(self.vector_db_path, "metadata.pkl")
        
        faiss.write_index(self.index, index_path)
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata_store, f)
    
    def get_stats(self) -> Dict[str, Any]:
        """벡터 저장소 통계"""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": type(self.index).__name__
        }

