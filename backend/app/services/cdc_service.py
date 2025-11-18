"""
변경 감지 서비스 (Change Data Capture)
파일 해시 기반 변경 추적 및 증분 처리
"""
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.database import Document, DocumentVersion, DocumentChunk
from app.core.logging import logger


class CDCService:
    """변경 감지 및 추적 서비스"""
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        파일의 SHA-256 해시 계산
        
        Args:
            file_path: 파일 경로
            
        Returns:
            SHA-256 해시 문자열
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # 파일을 청크 단위로 읽어 메모리 효율적으로 처리
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"파일 해시 계산 실패: {file_path}, {str(e)}")
            raise
    
    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """
        텍스트 콘텐츠의 SHA-256 해시 계산
        
        Args:
            content: 텍스트 콘텐츠
            
        Returns:
            SHA-256 해시 문자열
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def detect_document_change(
        db: Session,
        document_id: str,
        new_file_path: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        문서 변경 감지
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            new_file_path: 새 파일 경로
            
        Returns:
            (변경 여부, 이전 해시, 새 해시)
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        # 새 파일 해시 계산
        new_hash = CDCService.calculate_file_hash(new_file_path)
        old_hash = document.file_hash
        
        # 변경 감지
        has_changed = (old_hash != new_hash) if old_hash else True
        
        logger.info(
            f"문서 변경 감지: {document.filename} - "
            f"변경됨={has_changed}, 이전={old_hash[:8] if old_hash else 'None'}, "
            f"새로운={new_hash[:8]}"
        )
        
        return has_changed, old_hash, new_hash
    
    @staticmethod
    def detect_chunk_changes(
        db: Session,
        document_id: str,
        new_chunks: List[Dict]
    ) -> List[Dict]:
        """
        청크 레벨 변경 감지 (증분 처리)
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            new_chunks: 새 청크 리스트 [{"content": str, "metadata": dict}, ...]
            
        Returns:
            변경된 청크 리스트 (추가/수정된 것만)
        """
        # 기존 청크 조회
        existing_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()
        
        # 기존 청크를 해시 기반 딕셔너리로 변환
        existing_chunk_map = {
            chunk.chunk_index: {
                'id': chunk.id,
                'hash': chunk.content_hash,
                'content': chunk.content
            }
            for chunk in existing_chunks
        }
        
        changed_chunks = []
        
        for idx, new_chunk in enumerate(new_chunks):
            content = new_chunk.get('content', '')
            new_hash = CDCService.calculate_content_hash(content)
            
            # 기존 청크와 비교
            if idx in existing_chunk_map:
                old_hash = existing_chunk_map[idx]['hash']
                if old_hash != new_hash:
                    # 변경됨
                    changed_chunks.append({
                        'chunk_index': idx,
                        'content': content,
                        'metadata': new_chunk.get('metadata', {}),
                        'content_hash': new_hash,
                        'change_type': 'modified',
                        'old_chunk_id': existing_chunk_map[idx]['id']
                    })
            else:
                # 새로 추가됨
                changed_chunks.append({
                    'chunk_index': idx,
                    'content': content,
                    'metadata': new_chunk.get('metadata', {}),
                    'content_hash': new_hash,
                    'change_type': 'added'
                })
        
        # 삭제된 청크 감지 (기존에는 있었지만 새 버전에는 없는 것)
        new_indices = set(range(len(new_chunks)))
        deleted_indices = set(existing_chunk_map.keys()) - new_indices
        
        for idx in deleted_indices:
            changed_chunks.append({
                'chunk_index': idx,
                'change_type': 'deleted',
                'old_chunk_id': existing_chunk_map[idx]['id']
            })
        
        logger.info(
            f"청크 변경 감지 완료: 문서 {document_id} - "
            f"전체 {len(new_chunks)}개, 변경 {len(changed_chunks)}개 "
            f"(추가/수정: {sum(1 for c in changed_chunks if c['change_type'] != 'deleted')}개, "
            f"삭제: {sum(1 for c in changed_chunks if c['change_type'] == 'deleted')}개)"
        )
        
        return changed_chunks
    
    @staticmethod
    def record_document_version(
        db: Session,
        document_id: str,
        file_hash: str,
        changed_chunks: List[Dict],
        user_id: str
    ) -> DocumentVersion:
        """
        문서 버전 기록
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            file_hash: 파일 해시
            changed_chunks: 변경된 청크 리스트
            user_id: 사용자 ID
            
        Returns:
            생성된 DocumentVersion 객체
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        # 변경 타입 결정
        if document.version == 1:
            change_type = "created"
        else:
            change_type = "modified"
        
        # 버전 기록 생성
        version_record = DocumentVersion(
            document_id=document_id,
            version=document.version,
            file_hash=file_hash,
            change_type=change_type,
            changed_chunks=[c.get('chunk_index') for c in changed_chunks],
            delta_size=len(changed_chunks),
            created_by=user_id
        )
        
        db.add(version_record)
        
        logger.info(
            f"문서 버전 기록: {document.filename} v{document.version} - "
            f"타입={change_type}, 변경 청크={len(changed_chunks)}개"
        )
        
        return version_record
    
    @staticmethod
    def mark_document_for_reindex(
        db: Session,
        document_id: str,
        new_file_hash: str
    ):
        """
        문서에 재인덱싱 플래그 설정
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            new_file_hash: 새 파일 해시
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
        
        # 이전 해시 저장
        document.previous_hash = document.file_hash
        
        # 새 해시 및 플래그 설정
        document.file_hash = new_file_hash
        document.needs_reindex = True
        document.is_indexed = False
        document.version += 1
        document.last_modified = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            f"재인덱싱 플래그 설정: {document.filename} - "
            f"버전 {document.version-1} → {document.version}"
        )
    
    @staticmethod
    def get_documents_needing_reindex(db: Session) -> List[Document]:
        """
        재인덱싱이 필요한 문서 조회
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            재인덱싱이 필요한 문서 리스트
        """
        documents = db.query(Document).filter(
            Document.needs_reindex == True
        ).all()
        
        logger.info(f"재인덱싱 필요 문서: {len(documents)}개")
        
        return documents
