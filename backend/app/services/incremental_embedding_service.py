"""
증분 임베딩 서비스
변경된 청크만 임베딩을 생성하고 벡터 DB에 반영
"""
from typing import List, Dict, Tuple
import numpy as np
from sqlalchemy.orm import Session

from app.ai.embedding import EmbeddingGenerator
from app.ai.vector_store import VectorStore
from app.models.database import Document, DocumentChunk
from app.services.cdc_service import CDCService
from app.core.logging import logger
from app.core.config import settings


class IncrementalEmbeddingService:
    """증분 임베딩 처리 서비스"""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.cdc_service = CDCService()
        self.similarity_threshold = 0.95  # 코사인 유사도 임계값 (중복 제거용)
    
    def calculate_cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """
        두 벡터 간 코사인 유사도 계산
        
        Args:
            vec1: 벡터 1
            vec2: 벡터 2
            
        Returns:
            코사인 유사도 (0~1)
        """
        # 벡터 정규화
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)
        
        # 코사인 유사도
        similarity = np.dot(vec1_norm, vec2_norm)
        
        return float(similarity)
    
    def find_duplicate_embeddings(
        self,
        new_embedding: np.ndarray,
        existing_embeddings: List[np.ndarray]
    ) -> List[int]:
        """
        기존 임베딩 중 중복 찾기 (코사인 유사도 기반)
        
        Args:
            new_embedding: 새 임베딩
            existing_embeddings: 기존 임베딩 리스트
            
        Returns:
            중복 임베딩의 인덱스 리스트
        """
        duplicates = []
        
        for idx, existing_emb in enumerate(existing_embeddings):
            similarity = self.calculate_cosine_similarity(new_embedding, existing_emb)
            
            if similarity >= self.similarity_threshold:
                duplicates.append(idx)
                logger.debug(
                    f"중복 임베딩 발견: 인덱스={idx}, 유사도={similarity:.4f}"
                )
        
        return duplicates
    
    def process_incremental_chunks(
        self,
        db: Session,
        document_id: str,
        changed_chunks: List[Dict]
    ) -> Dict:
        """
        증분 청크 처리 (임베딩 생성 및 벡터 DB 업데이트)
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            changed_chunks: 변경된 청크 리스트
            
        Returns:
            처리 결과 통계
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        stats = {
            'total_chunks': len(changed_chunks),
            'added': 0,
            'modified': 0,
            'deleted': 0,
            'skipped_duplicates': 0
        }
        
        # 기존 임베딩 로드 (중복 체크용)
        existing_chunk_ids = [
            chunk.embedding_id for chunk in
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.embedding_id.isnot(None)
            ).all()
        ]
        
        # 처리할 청크 분류
        to_add = []
        to_modify = []
        to_delete = []
        to_move = []
        
        for chunk_data in changed_chunks:
            change_type = chunk_data.get('change_type', 'added')
            
            if change_type == 'deleted':
                to_delete.append(chunk_data)
            elif change_type == 'added':
                to_add.append(chunk_data)
            elif change_type == 'modified':
                to_modify.append(chunk_data)
            elif change_type == 'moved':
                to_move.append(chunk_data)
        
        # 1. 삭제된 청크 처리
        for chunk_data in to_delete:
            old_chunk_id = chunk_data.get('old_chunk_id')
            if old_chunk_id:
                old_chunk = db.query(DocumentChunk).filter(
                    DocumentChunk.id == old_chunk_id
                ).first()
                
                if old_chunk and old_chunk.embedding_id:
                    # 벡터 DB에서 삭제
                    try:
                        self.vector_store.delete_document(old_chunk.embedding_id)
                        logger.info(f"벡터 삭제: {old_chunk.embedding_id}")
                    except Exception as e:
                        logger.warning(f"벡터 삭제 실패: {str(e)}")
                
                # DB에서 삭제
                db.delete(old_chunk)
                stats['deleted'] += 1
        
        # 1-1. 이동된 청크 처리 (내용 같고 인덱스만 변경 - 임베딩 재사용)
        for chunk_data in to_move:
            old_chunk_id = chunk_data.get('old_chunk_id')
            if old_chunk_id:
                chunk = db.query(DocumentChunk).filter(
                    DocumentChunk.id == old_chunk_id
                ).first()
                
                if chunk:
                    # 인덱스만 업데이트 (임베딩은 재사용)
                    chunk.chunk_index = chunk_data['chunk_index']
                    logger.debug(
                        f"청크 인덱스 업데이트: {old_chunk_id} - "
                        f"{chunk_data.get('old_chunk_index')} → {chunk_data['chunk_index']}"
                    )
                    # moved는 modified에 포함시키지 않음 (stats는 별도 카운트 가능)
        
        # 2. 추가/수정된 청크 처리
        chunks_to_process = to_add + to_modify
        
        if chunks_to_process:
            # 텍스트 추출
            texts = [c['content'] for c in chunks_to_process]
            
            # 배치 임베딩 생성
            logger.info(f"임베딩 생성 시작: {len(texts)}개 청크")
            embeddings = self.embedding_generator.generate_embeddings(
                texts,
                batch_size=settings.BATCH_SIZE
            )
            
            # 메타데이터 준비
            metadatas = []
            for chunk_data in chunks_to_process:
                metadata = {
                    'document_id': document_id,
                    'document_name': document.filename,
                    'chunk_index': chunk_data['chunk_index'],
                    'chunk_metadata': chunk_data.get('metadata', {}),
                    'text': chunk_data['content'][:500]  # 처음 500자만 저장
                }
                metadatas.append(metadata)
            
            # 벡터 DB에 추가
            vector_ids = self.vector_store.add_documents(texts, metadatas)
            
            # 3. DB 업데이트
            for idx, chunk_data in enumerate(chunks_to_process):
                change_type = chunk_data['change_type']
                
                if change_type == 'modified':
                    # 기존 청크 업데이트
                    old_chunk_id = chunk_data.get('old_chunk_id')
                    if old_chunk_id:
                        chunk = db.query(DocumentChunk).filter(
                            DocumentChunk.id == old_chunk_id
                        ).first()
                        
                        if chunk:
                            # 기존 벡터 삭제
                            if chunk.embedding_id:
                                try:
                                    self.vector_store.delete_document(chunk.embedding_id)
                                except Exception as e:
                                    logger.warning(f"기존 벡터 삭제 실패: {str(e)}")
                            
                            # 업데이트
                            chunk.content = chunk_data['content']
                            chunk.chunk_metadata = chunk_data.get('metadata', {})
                            chunk.content_hash = chunk_data['content_hash']
                            chunk.embedding_id = vector_ids[idx]
                            stats['modified'] += 1
                
                elif change_type == 'added':
                    # 새 청크 생성
                    new_chunk = DocumentChunk(
                        document_id=document_id,
                        chunk_index=chunk_data['chunk_index'],
                        content=chunk_data['content'],
                        chunk_metadata=chunk_data.get('metadata', {}),
                        content_hash=chunk_data['content_hash'],
                        embedding_id=vector_ids[idx]
                    )
                    db.add(new_chunk)
                    stats['added'] += 1
        
        db.commit()
        
        logger.info(
            f"증분 청크 처리 완료: {document.filename} - "
            f"추가={stats['added']}, 수정={stats['modified']}, "
            f"삭제={stats['deleted']}, 중복제거={stats['skipped_duplicates']}"
        )
        
        return stats
    
    def process_document_reindex(
        self,
        db: Session,
        document_id: str,
        new_chunks: List[Dict],
        user_id: str
    ) -> Dict:
        """
        문서 재인덱싱 처리 (증분 방식, 복잡도 초과 시 전체 재인덱싱)
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            new_chunks: 새 청크 리스트
            user_id: 사용자 ID
            
        Returns:
            처리 결과 통계
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        logger.info(f"증분 재인덱싱 시작: {document.filename}")
        
        # 1. 청크 레벨 변경 감지 (LCS 기반)
        changed_chunks = self.cdc_service.detect_chunk_changes(
            db, document_id, new_chunks
        )
        
        # 복잡도 초과 시 None 반환 → 전체 재인덱싱
        if changed_chunks is None:
            logger.warning(
                f"복잡도 초과로 전체 재인덱싱 수행: {document.filename}"
            )
            return self._full_reindex(db, document_id, new_chunks, user_id)
        
        if not changed_chunks:
            logger.info(f"변경사항 없음: {document.filename}")
            return {
                'total_chunks': len(new_chunks),
                'added': 0,
                'modified': 0,
                'deleted': 0,
                'skipped_duplicates': 0
            }
        
        # 2. 증분 임베딩 처리
        stats = self.process_incremental_chunks(db, document_id, changed_chunks)
        
        # 3. 버전 기록
        self.cdc_service.record_document_version(
            db, document_id, document.file_hash, changed_chunks, user_id
        )
        
        # 4. 재인덱싱 플래그 해제
        document.needs_reindex = False
        document.is_indexed = True
        db.commit()
        
        logger.info(f"증분 재인덱싱 완료: {document.filename} - 통계={stats}")
        
        return stats
    
    def _full_reindex(
        self,
        db: Session,
        document_id: str,
        new_chunks: List[Dict],
        user_id: str
    ) -> Dict:
        """
        전체 재인덱싱 (복잡도 초과 또는 강제 재인덱싱 시)
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            new_chunks: 새 청크 리스트
            user_id: 사용자 ID
            
        Returns:
            처리 결과 통계
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        logger.info(f"전체 재인덱싱 시작: {document.filename}")
        
        # 1. 기존 청크 및 임베딩 삭제
        existing_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        deleted_count = 0
        for chunk in existing_chunks:
            if chunk.embedding_id:
                try:
                    self.vector_store.delete_document(chunk.embedding_id)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"벡터 삭제 실패: {chunk.embedding_id}, {str(e)}")
            db.delete(chunk)
        
        db.commit()
        
        # 2. 새 청크 임베딩 생성
        texts = [c['content'] for c in new_chunks]
        metadatas = [
            {
                'document_id': document_id,
                'document_name': document.filename,
                'chunk_index': c['chunk_index'],
                'chunk_metadata': c.get('metadata', {}),
                'text': c['content'][:500]
            }
            for c in new_chunks
        ]
        
        logger.info(f"임베딩 생성 시작: {len(texts)}개 청크")
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        # 3. 벡터 DB에 추가
        vector_ids = self.vector_store.add_documents(texts, metadatas)
        
        # 4. DB에 청크 저장
        for idx, (chunk_data, vector_id) in enumerate(zip(new_chunks, vector_ids)):
            new_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_data['chunk_index'],
                content=chunk_data['content'],
                chunk_metadata=chunk_data.get('metadata', {}),
                content_hash=chunk_data['content_hash'],
                embedding_id=vector_id
            )
            db.add(new_chunk)
        
        # 5. 버전 기록 (전체 재인덱싱)
        self.cdc_service.record_document_version(
            db, document_id, document.file_hash, 
            [{'chunk_index': i, 'change_type': 'recreated'} for i in range(len(new_chunks))],
            user_id
        )
        
        # 6. 문서 상태 업데이트
        document.needs_reindex = False
        document.is_indexed = True
        db.commit()
        
        stats = {
            'total_chunks': len(new_chunks),
            'added': len(new_chunks),
            'modified': 0,
            'deleted': deleted_count,
            'skipped_duplicates': 0,
            'full_reindex': True
        }
        
        logger.info(
            f"전체 재인덱싱 완료: {document.filename} - "
            f"삭제={deleted_count}, 추가={len(new_chunks)}"
        )
        
        return stats
    
    def batch_process_pending_documents(
        self,
        db: Session,
        user_id: str,
        max_documents: int = 10
    ) -> List[Dict]:
        """
        재인덱싱 대기 중인 문서를 일괄 처리
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            max_documents: 최대 처리 문서 수
            
        Returns:
            처리 결과 리스트
        """
        # 재인덱싱 필요한 문서 조회
        documents = self.cdc_service.get_documents_needing_reindex(db)
        documents = documents[:max_documents]
        
        results = []
        
        for document in documents:
            try:
                # 파싱된 청크 가져오기 (실제로는 파서를 통해 다시 파싱해야 함)
                # 여기서는 간단히 기존 청크를 사용
                existing_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document.id
                ).all()
                
                new_chunks = [
                    {
                        'content': chunk.content,
                        'metadata': chunk.chunk_metadata or {}
                    }
                    for chunk in existing_chunks
                ]
                
                # 재인덱싱
                stats = self.process_document_reindex(
                    db, document.id, new_chunks, user_id
                )
                
                results.append({
                    'document_id': document.id,
                    'filename': document.filename,
                    'success': True,
                    'stats': stats
                })
            
            except Exception as e:
                logger.error(
                    f"문서 재인덱싱 실패: {document.filename} - {str(e)}"
                )
                results.append({
                    'document_id': document.id,
                    'filename': document.filename,
                    'success': False,
                    'error': str(e)
                })
        
        return results
