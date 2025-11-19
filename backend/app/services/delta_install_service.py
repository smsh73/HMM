"""
델타 패키지 설치 서비스
수신된 델타 패키지를 설치하여 벡터DB 및 인덱스 업데이트
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
import os
import json
import zipfile
import shutil

from app.models.database import Document, DocumentChunk
from app.ai.hybrid_rag_engine import HybridRAGEngine
from app.core.config import settings
from app.core.logging import logger


class DeltaInstallService:
    """델타 패키지 설치 서비스"""
    
    def __init__(self, db: Session):
        """델타 설치 서비스 초기화"""
        self.db = db
        self.rag_engine = HybridRAGEngine()
        self.install_dir = os.path.join(settings.VECTOR_DB_PATH, "delta_installs")
        os.makedirs(self.install_dir, exist_ok=True)
    
    def install_delta_package(self, package_file_path: str) -> Dict[str, Any]:
        """
        델타 패키지 설치
        
        Args:
            package_file_path: 델타 패키지 ZIP 파일 경로
            
        Returns:
            설치 결과
        """
        # 압축 해제
        extract_dir = os.path.join(self.install_dir, os.path.basename(package_file_path).replace(".zip", ""))
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(package_file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 메타데이터 로드
            metadata_path = os.path.join(extract_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                raise ValueError("메타데이터 파일을 찾을 수 없습니다.")
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # 문서 및 청크 설치
            installed_docs = []
            installed_chunks = []
            
            for doc_data in metadata.get("documents", []):
                # 문서 생성 또는 업데이트
                document = self.db.query(Document).filter(
                    Document.id == doc_data["id"]
                ).first()
                
                if not document:
                    # 새 문서 생성
                    document = Document(
                        id=doc_data["id"],
                        filename=doc_data["filename"],
                        file_type=doc_data["file_type"],
                        doc_metadata=doc_data.get("metadata", {}),
                        is_indexed=True
                    )
                    self.db.add(document)
                    self.db.flush()
                
                # 청크 설치
                for chunk_data in doc_data.get("chunks", []):
                    chunk = self.db.query(DocumentChunk).filter(
                        DocumentChunk.id == chunk_data["id"]
                    ).first()
                    
                    if not chunk:
                        # 새 청크 생성
                        chunk = DocumentChunk(
                            id=chunk_data["id"],
                            document_id=doc_data["id"],
                            chunk_index=chunk_data["chunk_index"],
                            content=chunk_data["content"],
                            embedding_id=chunk_data.get("embedding_id"),
                            chunk_metadata=chunk_data.get("metadata", {})
                        )
                        self.db.add(chunk)
                        installed_chunks.append(chunk_data["id"])
                
                installed_docs.append(doc_data["id"])
            
            # 벡터DB에 청크 추가 (재임베딩)
            for doc_data in metadata.get("documents", []):
                chunks = [
                    {
                        "content": chunk["content"],
                        "chunk_index": chunk["chunk_index"],
                        "metadata": chunk.get("metadata", {})
                    }
                    for chunk in doc_data.get("chunks", [])
                ]
                
                if chunks:
                    # RAG 엔진에 인덱싱
                    vector_ids = self.rag_engine.index_document(
                        document_id=doc_data["id"],
                        chunks=chunks
                    )
                    
                    # embedding_id 업데이트
                    for i, chunk_data in enumerate(doc_data.get("chunks", [])):
                        if i < len(vector_ids):
                            chunk = self.db.query(DocumentChunk).filter(
                                DocumentChunk.id == chunk_data["id"]
                            ).first()
                            if chunk:
                                chunk.embedding_id = vector_ids[i]
            
            self.db.commit()
            
            logger.info(
                f"델타 패키지 설치 완료: 문서 {len(installed_docs)}개, "
                f"청크 {len(installed_chunks)}개"
            )
            
            return {
                "status": "installed",
                "document_count": len(installed_docs),
                "chunk_count": len(installed_chunks),
                "message": "델타 패키지 설치가 완료되었습니다."
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"델타 패키지 설치 실패: {e}", exc_info=True)
            raise
        
        finally:
            # 임시 파일 정리
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)

