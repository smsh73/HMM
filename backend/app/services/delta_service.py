"""
델타 서비스
변경된 데이터만 추출하여 델타 패키지 생성
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json
import zipfile
import hashlib
from pathlib import Path

from app.models.database import DeltaPackage, Document, DocumentChunk, SystemRole
from app.services.system_role_service import SystemRoleService
from app.core.config import settings
from app.core.logging import logger


class DeltaService:
    """델타 서비스"""
    
    def __init__(self, db: Session):
        """델타 서비스 초기화"""
        self.db = db
        self.system_role_service = SystemRoleService(db)
        self.delta_dir = os.path.join(settings.VECTOR_DB_PATH, "deltas")
        os.makedirs(self.delta_dir, exist_ok=True)
    
    def create_delta_package(
        self,
        document_ids: List[str],
        package_type: str = "document_add"
    ) -> Dict[str, Any]:
        """
        델타 패키지 생성
        
        Args:
            document_ids: 변경된 문서 ID 리스트
            package_type: 패키지 타입 (document_add, document_update, document_delete)
            
        Returns:
            델타 패키지 정보
        """
        # 시스템 역할 확인
        system_role = self.system_role_service.get_system_role()
        if not system_role or system_role.role != "main_server":
            raise ValueError("델타 패키지는 메인서버에서만 생성할 수 있습니다.")
        
        # 변경된 문서 조회
        documents = self.db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.is_indexed == True
        ).all()
        
        if not documents:
            raise ValueError("변경된 문서를 찾을 수 없습니다.")
        
        # 변경된 청크 추출
        chunk_ids = []
        chunk_data = []
        
        for doc in documents:
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc.id
            ).all()
            
            for chunk in chunks:
                chunk_ids.append(chunk.id)
                chunk_data.append({
                    "id": chunk.id,
                    "document_id": doc.id,
                    "document_name": doc.filename,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding_id": chunk.embedding_id,
                    "metadata": chunk.chunk_metadata or {}
                })
        
        # 델타 패키지 생성
        delta_package = DeltaPackage(
            package_type=package_type,
            source_system=system_role.system_name or "main_server",
            target_system=system_role.connection_ip or "ship_client",
            document_ids=document_ids,
            chunk_ids=chunk_ids,
            status="pending",
            package_metadata={
                "document_count": len(documents),
                "chunk_count": len(chunk_data),
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        self.db.add(delta_package)
        self.db.commit()
        self.db.refresh(delta_package)
        
        # 델타 파일 생성
        package_file = self._create_delta_file(delta_package.id, documents, chunk_data)
        
        # 파일 정보 업데이트
        delta_package.file_path = package_file["file_path"]
        delta_package.file_size = package_file["file_size"]
        delta_package.checksum = package_file["checksum"]
        delta_package.status = "ready"
        self.db.commit()
        
        logger.info(
            f"델타 패키지 생성 완료: {delta_package.id} - "
            f"문서 {len(documents)}개, 청크 {len(chunk_data)}개"
        )
        
        return {
            "package_id": delta_package.id,
            "package_type": package_type,
            "document_count": len(documents),
            "chunk_count": len(chunk_data),
            "file_path": delta_package.file_path,
            "file_size": delta_package.file_size,
            "checksum": delta_package.checksum,
            "status": delta_package.status
        }
    
    def _create_delta_file(
        self,
        package_id: str,
        documents: List[Document],
        chunk_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        델타 파일 생성 (ZIP)
        
        Args:
            package_id: 패키지 ID
            documents: 문서 리스트
            chunk_data: 청크 데이터 리스트
            
        Returns:
            파일 정보
        """
        package_dir = os.path.join(self.delta_dir, package_id)
        os.makedirs(package_dir, exist_ok=True)
        
        # 메타데이터 파일
        metadata = {
            "package_id": package_id,
            "package_type": "delta",
            "created_at": datetime.utcnow().isoformat(),
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "metadata": doc.doc_metadata or {}
                }
                for doc in documents
            ],
            "chunks": chunk_data
        }
        
        metadata_path = os.path.join(package_dir, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 벡터 임베딩 추출 (Chroma에서)
        from app.ai.hybrid_rag_engine import HybridRAGEngine
        rag_engine = HybridRAGEngine()
        
        # 변경된 청크의 임베딩 ID로 벡터 추출
        embedding_ids = [chunk["embedding_id"] for chunk in chunk_data if chunk.get("embedding_id")]
        
        # 벡터 데이터 추출 (실제 구현은 벡터 스토어에 따라 다름)
        vectors_data = self._extract_vectors(embedding_ids)
        
        if vectors_data:
            vectors_path = os.path.join(package_dir, "vectors.json")
            with open(vectors_path, "w", encoding="utf-8") as f:
                json.dump(vectors_data, f)
        
        # ZIP 파일 생성
        zip_path = os.path.join(self.delta_dir, f"{package_id}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(metadata_path, "metadata.json")
            if vectors_data:
                zipf.write(vectors_path, "vectors.json")
        
        # 파일 크기 및 체크섬 계산
        file_size = os.path.getsize(zip_path)
        checksum = self._calculate_checksum(zip_path)
        
        # 임시 파일 정리
        os.remove(metadata_path)
        if vectors_data and os.path.exists(vectors_path):
            os.remove(vectors_path)
        os.rmdir(package_dir)
        
        return {
            "file_path": zip_path,
            "file_size": file_size,
            "checksum": checksum
        }
    
    def _extract_vectors(self, embedding_ids: List[str]) -> Optional[Dict[str, Any]]:
        """벡터 임베딩 추출"""
        # 벡터는 용량이 크므로 메타데이터만 전송하고
        # 수신 측에서 재임베딩하는 것이 효율적
        # 필요시 Chroma에서 벡터 추출 가능
        try:
            from app.ai.vector_store_chroma import ChromaVectorStore
            vector_store = ChromaVectorStore()
            # Chroma collection.get()으로 벡터 추출 가능하지만
            # 용량 문제로 메타데이터만 전송
            return None
        except Exception as e:
            logger.warning(f"벡터 추출 실패: {e}")
            return None
    
    def _calculate_checksum(self, file_path: str) -> str:
        """파일 체크섬 계산"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_pending_deltas(self) -> List[Dict[str, Any]]:
        """전송 대기 중인 델타 패키지 조회"""
        packages = self.db.query(DeltaPackage).filter(
            DeltaPackage.status.in_(["ready", "pending"])
        ).order_by(DeltaPackage.created_at.desc()).all()
        
        return [
            {
                "id": p.id,
                "package_type": p.package_type,
                "document_count": len(p.document_ids) if p.document_ids else 0,
                "chunk_count": len(p.chunk_ids) if p.chunk_ids else 0,
                "file_size": p.file_size,
                "status": p.status,
                "send_type": p.send_type,
                "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in packages
        ]

