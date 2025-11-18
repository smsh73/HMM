"""
변경 감지 서비스 (Change Data Capture)
파일 해시 기반 변경 추적 및 증분 처리
"""
import hashlib
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime
from collections import defaultdict

from app.models.database import Document, DocumentVersion, DocumentChunk
from app.core.logging import logger


class CDCService:
    """변경 감지 및 추적 서비스"""
    
    @staticmethod
    def _greedy_align_chunks(
        old_list: List[Dict], 
        new_list: List[Dict]
    ) -> List[Tuple[Optional[int], Optional[int], str]]:
        """
        Greedy alignment로 청크 매칭 (순서 및 중복 해시 지원)
        
        Args:
            old_list: 기존 청크 리스트 (각 항목에 content_hash 포함)
            new_list: 새 청크 리스트 (각 항목에 content_hash 포함)
            
        Returns:
            (old_idx, new_idx, operation) 튜플 리스트
            - operation: 'unchanged', 'modified', 'moved', 'added', 'deleted'
        """
        # 매칭 추적
        used_old = set()
        used_new = set()
        alignments = []
        
        # 1단계: 위치별로 먼저 매칭 (unchanged 또는 modified)
        min_len = min(len(old_list), len(new_list))
        for i in range(min_len):
            old_hash = old_list[i]['content_hash']
            new_hash = new_list[i]['content_hash']
            
            if old_hash == new_hash:
                # 위치도 같고 내용도 같음
                alignments.append((i, i, 'unchanged'))
                used_old.add(i)
                used_new.add(i)
            else:
                # 위치는 같지만 내용이 다름 (수정)
                alignments.append((i, i, 'modified'))
                used_old.add(i)
                used_new.add(i)
        
        # 2단계: 남은 청크 중 해시 매칭으로 이동 감지
        remaining_old = [i for i in range(len(old_list)) if i not in used_old]
        remaining_new = [i for i in range(len(new_list)) if i not in used_new]
        
        # 새 청크별로 기존 청크에서 같은 해시 찾기
        for new_idx in remaining_new[:]:
            new_hash = new_list[new_idx]['content_hash']
            
            for old_idx in remaining_old[:]:
                old_hash = old_list[old_idx]['content_hash']
                
                if old_hash == new_hash:
                    # 같은 내용이지만 다른 위치 (이동)
                    alignments.append((old_idx, new_idx, 'moved'))
                    used_old.add(old_idx)
                    used_new.add(new_idx)
                    remaining_old.remove(old_idx)
                    remaining_new.remove(new_idx)
                    break
        
        # 3단계: 남은 청크 처리
        # 삭제된 청크
        for old_idx in remaining_old:
            alignments.append((old_idx, None, 'deleted'))
        
        # 추가된 청크
        for new_idx in remaining_new:
            alignments.append((None, new_idx, 'added'))
        
        return alignments
    
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
        new_chunks: List[Dict],
        complexity_threshold: int = 1000
    ) -> Optional[List[Dict]]:
        """
        청크 레벨 변경 감지 (Greedy alignment - 정확한 diff)
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            new_chunks: 새 청크 리스트 
                       [{"content": str, "content_hash": str, "chunk_index": int, "metadata": dict}, ...]
            complexity_threshold: diff 복잡도 임계값 (초과 시 전체 재인덱싱 권장)
            
        Returns:
            변경된 청크 리스트 (added/modified/moved/deleted)
            또는 None (복잡도 초과 시)
            
        Note:
            Greedy alignment로 정확한 매칭 수행:
            1. 위치별 비교 (unchanged/modified)
            2. 해시 매칭으로 이동 감지
            3. 남은 청크는 added/deleted
        """
        # 기존 청크 조회 (인덱스 순서대로)
        existing_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
        
        # 기존 청크 리스트 생성
        old_list = [
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
        
        # 새 청크 리스트 생성 (해시 계산)
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
        
        # 복잡도 체크: diff 크기가 임계값 초과 시 None 반환
        diff_complexity = len(old_list) * len(new_list)
        if diff_complexity > complexity_threshold:
            logger.warning(
                f"청크 변경 감지 복잡도 초과: {diff_complexity} > {complexity_threshold} - "
                f"전체 재인덱싱 권장"
            )
            return None
        
        # Greedy alignment로 매칭
        alignments = CDCService._greedy_align_chunks(old_list, new_list)
        
        # 변경 레코드 생성
        changed_chunks = []
        
        for old_idx, new_idx, operation in alignments:
            if operation == 'unchanged':
                # 변경 없음 - skip
                pass
            
            elif operation == 'modified':
                # 내용 변경 (같은 위치, 다른 해시)
                old_chunk = old_list[old_idx]
                new_chunk = new_list[new_idx]
                changed_chunks.append({
                    'chunk_index': new_chunk['chunk_index'],
                    'content': new_chunk['content'],
                    'metadata': new_chunk['metadata'],
                    'content_hash': new_chunk['content_hash'],
                    'change_type': 'modified',
                    'old_chunk_id': old_chunk['id']
                })
            
            elif operation == 'moved':
                # 위치 이동 (다른 위치, 같은 해시)
                old_chunk = old_list[old_idx]
                new_chunk = new_list[new_idx]
                changed_chunks.append({
                    'chunk_index': new_chunk['chunk_index'],
                    'content': new_chunk['content'],
                    'metadata': new_chunk['metadata'],
                    'content_hash': new_chunk['content_hash'],
                    'change_type': 'moved',
                    'old_chunk_id': old_chunk['id'],
                    'old_chunk_index': old_chunk['chunk_index']
                })
            
            elif operation == 'deleted':
                # 삭제됨
                old_chunk = old_list[old_idx]
                changed_chunks.append({
                    'chunk_index': old_chunk['chunk_index'],
                    'content_hash': old_chunk['content_hash'],
                    'change_type': 'deleted',
                    'old_chunk_id': old_chunk['id'],
                    'old_embedding_id': old_chunk.get('embedding_id')
                })
            
            elif operation == 'added':
                # 추가됨
                new_chunk = new_list[new_idx]
                changed_chunks.append({
                    'chunk_index': new_chunk['chunk_index'],
                    'content': new_chunk['content'],
                    'metadata': new_chunk['metadata'],
                    'content_hash': new_chunk['content_hash'],
                    'change_type': 'added'
                })
        
        logger.info(
            f"청크 변경 감지 완료 (Greedy): 문서 {document_id} - "
            f"기존 {len(old_list)}개, 새로운 {len(new_list)}개, "
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
