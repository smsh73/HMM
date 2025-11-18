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
        청크 레벨 변경 감지 (순서 기반 매칭 - 중복 청크 대응)
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            new_chunks: 새 청크 리스트 
                       [{"content": str, "content_hash": str, "chunk_index": int, "metadata": dict}, ...]
            
        Returns:
            변경된 청크 리스트 (추가/수정/삭제)
            
        Note:
            순서를 유지하며 content_hash로 비교하여 중복 청크도 정확히 처리
        """
        # 기존 청크 조회 (인덱스 순서대로)
        existing_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
        
        # 기존 청크를 리스트로 유지 (순서 보존)
        existing_list = [
            {
                'id': chunk.id,
                'chunk_index': chunk.chunk_index,
                'content_hash': chunk.content_hash,
                'content': chunk.content,
                'embedding_id': chunk.embedding_id,
                'metadata': chunk.chunk_metadata
            }
            for chunk in existing_chunks
        ]
        
        # 새 청크 처리 (hash 계산)
        new_list = []
        for chunk_data in new_chunks:
            content_hash = chunk_data.get('content_hash')
            if not content_hash:
                content_hash = CDCService.calculate_content_hash(
                    chunk_data.get('content', '')
                )
            
            new_list.append({
                'chunk_index': chunk_data.get('chunk_index'),
                'content': chunk_data.get('content', ''),
                'content_hash': content_hash,
                'metadata': chunk_data.get('metadata', {})
            })
        
        # 순서 기반 매칭 (Longest Common Subsequence 기반)
        changed_chunks = []
        
        # 간단한 순서 비교: 인덱스 순서대로 비교
        max_len = max(len(existing_list), len(new_list))
        
        for i in range(max_len):
            old_chunk = existing_list[i] if i < len(existing_list) else None
            new_chunk = new_list[i] if i < len(new_list) else None
            
            if old_chunk and new_chunk:
                # 둘 다 존재 - 비교
                if old_chunk['content_hash'] != new_chunk['content_hash']:
                    # 내용 변경 (수정)
                    changed_chunks.append({
                        'chunk_index': new_chunk['chunk_index'],
                        'content': new_chunk['content'],
                        'metadata': new_chunk['metadata'],
                        'content_hash': new_chunk['content_hash'],
                        'change_type': 'modified',
                        'old_chunk_id': old_chunk['id']
                    })
                elif old_chunk['chunk_index'] != new_chunk['chunk_index']:
                    # 내용 같지만 인덱스 변경 (이동)
                    changed_chunks.append({
                        'chunk_index': new_chunk['chunk_index'],
                        'content': new_chunk['content'],
                        'metadata': new_chunk['metadata'],
                        'content_hash': new_chunk['content_hash'],
                        'change_type': 'moved',
                        'old_chunk_id': old_chunk['id'],
                        'old_chunk_index': old_chunk['chunk_index']
                    })
                # 내용도 같고 인덱스도 같으면 변경 없음 (skip)
            
            elif old_chunk and not new_chunk:
                # 기존에는 있었지만 새 버전에는 없음 (삭제)
                changed_chunks.append({
                    'chunk_index': old_chunk['chunk_index'],
                    'content_hash': old_chunk['content_hash'],
                    'change_type': 'deleted',
                    'old_chunk_id': old_chunk['id'],
                    'old_embedding_id': old_chunk.get('embedding_id')
                })
            
            elif not old_chunk and new_chunk:
                # 새 버전에만 있음 (추가)
                changed_chunks.append({
                    'chunk_index': new_chunk['chunk_index'],
                    'content': new_chunk['content'],
                    'metadata': new_chunk['metadata'],
                    'content_hash': new_chunk['content_hash'],
                    'change_type': 'added'
                })
        
        logger.info(
            f"청크 변경 감지 완료: 문서 {document_id} - "
            f"기존 {len(existing_list)}개, 새로운 {len(new_list)}개, "
            f"변경 {len(changed_chunks)}개 "
            f"(추가: {sum(1 for c in changed_chunks if c['change_type'] == 'added')}개, "
            f"수정: {sum(1 for c in changed_chunks if c['change_type'] == 'modified')}개, "
            f"이동: {sum(1 for c in changed_chunks if c['change_type'] == 'moved')}개, "
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
