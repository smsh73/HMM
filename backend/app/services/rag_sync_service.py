"""
RAG 동기화 서비스
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import os
import shutil
import json
import pickle
from pathlib import Path

from app.models.database import RAGSync, Document, DocumentChunk
from app.core.config import settings


class RAGSyncService:
    """RAG 동기화 서비스"""
    
    def __init__(self, db: Session):
        """RAG 동기화 서비스 초기화"""
        self.db = db
        self.vector_db_path = settings.VECTOR_DB_PATH
    
    def export_rag(
        self,
        target_system: str,
        sync_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """RAG 데이터 내보내기 (메인 시스템 -> 선박 시스템)"""
        if not sync_id:
            sync_record = RAGSync(
                sync_type="export",
                source_system="main",
                target_system=target_system,
                status="in_progress"
            )
            self.db.add(sync_record)
            self.db.commit()
            sync_id = sync_record.id
        else:
            sync_record = self.db.query(RAGSync).filter(RAGSync.id == sync_id).first()
            if not sync_record:
                raise ValueError("동기화 기록을 찾을 수 없습니다.")
        
        try:
            # 벡터 DB 파일 복사
            vector_db_files = [
                "faiss.index",
                "metadata.pkl"
            ]
            
            export_dir = os.path.join(settings.VECTOR_DB_PATH, "exports", sync_id)
            os.makedirs(export_dir, exist_ok=True)
            
            for filename in vector_db_files:
                src_path = os.path.join(self.vector_db_path, filename)
                if os.path.exists(src_path):
                    dst_path = os.path.join(export_dir, filename)
                    shutil.copy2(src_path, dst_path)
            
            # 문서 메타데이터 내보내기
            documents = self.db.query(Document).filter(
                Document.is_indexed == True
            ).all()
            
            metadata = {
                "documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "file_type": doc.file_type,
                        "metadata": doc.doc_metadata,
                        "chunks": [
                            {
                                "id": chunk.id,
                                "chunk_index": chunk.chunk_index,
                                "embedding_id": chunk.embedding_id,
                                "metadata": chunk.chunk_metadata
                            }
                            for chunk in doc.chunks
                        ]
                    }
                    for doc in documents
                ]
            }
            
            metadata_path = os.path.join(export_dir, "metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 동기화 기록 업데이트
            sync_record.status = "completed"
            sync_record.vector_db_path = export_dir
            sync_record.metadata_path = metadata_path
            sync_record.progress = 100
            from datetime import datetime
            sync_record.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "sync_id": sync_id,
                "status": "completed",
                "export_path": export_dir,
                "document_count": len(documents)
            }
        except Exception as e:
            sync_record.status = "failed"
            sync_record.error_message = str(e)
            self.db.commit()
            raise
    
    def import_rag(
        self,
        sync_id: str,
        source_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """RAG 데이터 가져오기 (선박 시스템 <- 메인 시스템)"""
        sync_record = self.db.query(RAGSync).filter(RAGSync.id == sync_id).first()
        if not sync_record:
            raise ValueError("동기화 기록을 찾을 수 없습니다.")
        
        import_path = source_path or sync_record.vector_db_path
        if not import_path or not os.path.exists(import_path):
            raise ValueError("가져올 경로가 유효하지 않습니다.")
        
        try:
            sync_record.status = "in_progress"
            sync_record.sync_type = "import"
            self.db.commit()
            
            # 벡터 DB 파일 복사
            vector_db_files = [
                "faiss.index",
                "metadata.pkl"
            ]
            
            for filename in vector_db_files:
                src_path = os.path.join(import_path, filename)
                if os.path.exists(src_path):
                    dst_path = os.path.join(self.vector_db_path, filename)
                    shutil.copy2(src_path, dst_path)
            
            # 메타데이터 가져오기 (선택적)
            metadata_path = os.path.join(import_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    # 메타데이터는 참고용으로만 사용 (실제 문서는 별도로 동기화 필요)
            
            sync_record.status = "completed"
            sync_record.progress = 100
            from datetime import datetime
            sync_record.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "sync_id": sync_id,
                "status": "completed",
                "message": "RAG 데이터 동기화가 완료되었습니다."
            }
        except Exception as e:
            sync_record.status = "failed"
            sync_record.error_message = str(e)
            self.db.commit()
            raise
    
    def get_sync_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """동기화 기록 조회"""
        syncs = self.db.query(RAGSync).order_by(
            RAGSync.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": s.id,
                "sync_type": s.sync_type,
                "source_system": s.source_system,
                "target_system": s.target_system,
                "status": s.status,
                "progress": s.progress,
                "error_message": s.error_message,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in syncs
        ]

