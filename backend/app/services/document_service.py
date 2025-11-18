"""
문서 서비스 (CDC 및 증분 임베딩 통합)
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path

from app.models.database import Document, DocumentChunk, User
from app.parsers.parser_factory import ParserFactory
from app.parsers.base import ParsedDocument
from app.ai.hybrid_rag_engine import HybridRAGEngine
from app.services.cdc_service import CDCService
from app.services.incremental_embedding_service import IncrementalEmbeddingService
from app.core.config import settings
from app.core.logging import logger


class DocumentService:
    """문서 관리 서비스 (CDC 및 증분 임베딩 지원, Hybrid RAG 사용)"""
    
    def __init__(self, db: Session):
        """문서 서비스 초기화"""
        self.db = db
        # Hybrid RAG 엔진 사용 (Chroma + BM25)
        self.rag_engine = HybridRAGEngine(
            collection_name="documents",
            vector_weight=0.7,
            keyword_weight=0.3
        )
        self.cdc_service = CDCService()
        self.incremental_embedding_service = IncrementalEmbeddingService()
    
    def upload_document(
        self,
        file_path: str,
        filename: str,
        user_id: str
    ) -> Document:
        """문서 업로드 (SHA-256 해시 기반 변경 감지)"""
        # 파일 정보
        file_size = os.path.getsize(file_path)
        file_type = Path(filename).suffix.lower().replace(".", "")
        
        # 파일 해시 계산 (변경 감지용)
        file_hash = self.cdc_service.calculate_file_hash(file_path)
        logger.info(f"파일 업로드: {filename}, 해시={file_hash[:16]}...")
        
        # 기존 문서 확인 (동일 파일명)
        existing_doc = self.db.query(Document).filter(
            Document.filename == filename
        ).first()
        
        if existing_doc:
            # 파일이 변경되었는지 확인
            if existing_doc.file_hash == file_hash:
                logger.info(f"동일한 문서 감지: {filename} - 업로드 생략")
                return existing_doc
            else:
                # 파일이 변경됨 - 버전 업데이트
                logger.info(
                    f"문서 변경 감지: {filename} - "
                    f"v{existing_doc.version} → v{existing_doc.version + 1}"
                )
                existing_doc.previous_hash = existing_doc.file_hash
                existing_doc.file_hash = file_hash
                existing_doc.version += 1
                existing_doc.needs_reindex = True
                existing_doc.is_parsed = False
                existing_doc.is_indexed = False
                existing_doc.file_size = file_size
                
                # 새 파일로 교체
                save_path = existing_doc.file_path
                shutil.copy2(file_path, save_path)
                
                self.db.commit()
                self.db.refresh(existing_doc)
                
                return existing_doc
        
        # 새 문서 업로드
        save_path = os.path.join(settings.UPLOAD_DIR, filename)
        shutil.copy2(file_path, save_path)
        
        # 데이터베이스에 문서 정보 저장
        document = Document(
            filename=filename,
            file_type=file_type,
            file_path=save_path,
            file_size=file_size,
            file_hash=file_hash,
            version=1,
            created_by=user_id,
            is_parsed=False,
            is_indexed=False,
            needs_reindex=False
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"새 문서 업로드 완료: {filename} v1")
        
        return document
    
    def parse_document(self, document_id: str) -> Document:
        """문서 파싱 (청크 해시 계산, 재파싱 감지)"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("문서를 찾을 수 없습니다.")
        
        if not ParserFactory.is_supported(document.file_path):
            raise ValueError(f"지원하지 않는 파일 형식입니다: {document.file_type}")
        
        # 재파싱인 경우 needs_reindex 플래그 설정 (기존 청크는 유지하여 비교 가능하도록)
        is_reparse = document.is_parsed
        if is_reparse:
            logger.info(f"재파싱 감지: {document.filename} - 증분 처리 예정")
            document.needs_reindex = True
        
        # 파서로 문서 파싱
        parser = ParserFactory.get_parser(document.file_path)
        parsed_doc: ParsedDocument = parser.parse(document.file_path)
        
        # 파싱 결과를 JSON으로 저장 (청크 포함)
        chunks_json = [
            {
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "content_hash": self.cdc_service.calculate_content_hash(chunk.content),
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "metadata": chunk.metadata if hasattr(chunk, 'metadata') and chunk.metadata else {}
            }
            for chunk in parsed_doc.chunks
        ]
        
        document.parsed_content = {
            "full_text": parsed_doc.full_text,
            "structure": parsed_doc.structure,
            "chunks": chunks_json,  # 파싱된 청크 정보 저장 (index_document에서 사용)
            "metadata": {
                "title": parsed_doc.metadata.title,
                "author": parsed_doc.metadata.author,
                "page_count": parsed_doc.metadata.page_count,
                "word_count": parsed_doc.metadata.word_count
            }
        }
        document.doc_metadata = {
            "title": parsed_doc.metadata.title,
            "author": parsed_doc.metadata.author,
            "page_count": parsed_doc.metadata.page_count,
            "word_count": parsed_doc.metadata.word_count
        }
        document.is_parsed = True
        
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(
            f"문서 파싱 완료: {document.filename} - {len(chunks_json)}개 청크 (DB 저장은 인덱싱 시)"
        )
        
        return document
    
    def index_document(self, document_id: str, user_id: str = None) -> Dict:
        """
        문서 인덱싱 (증분 임베딩 방식)
        
        변경된 청크만 임베딩을 생성하여 효율성 향상
        파싱 결과(JSON)에서 청크를 가져와 DB 청크와 비교 후 처리
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("문서를 찾을 수 없습니다.")
        
        if not document.is_parsed:
            raise ValueError("문서가 파싱되지 않았습니다. 먼저 파싱을 수행하세요.")
        
        # 파싱 결과에서 새 청크 가져오기
        parsed_content = document.parsed_content or {}
        new_chunks_json = parsed_content.get("chunks", [])
        
        if not new_chunks_json:
            raise ValueError("파싱된 청크가 없습니다.")
        
        # 새 청크 데이터 준비
        chunk_data = [
            {
                "content": chunk["content"],
                "chunk_index": chunk["chunk_index"],
                "content_hash": chunk["content_hash"],
                "metadata": {
                    "page_number": chunk.get("page_number"),
                    "section_title": chunk.get("section_title"),
                    **(chunk.get("metadata", {}))
                }
            }
            for chunk in new_chunks_json
        ]
        
        # 증분 인덱싱 처리
        if document.needs_reindex or document.version > 1:
            # 증분 방식: 변경된 청크만 처리
            logger.info(f"증분 인덱싱 시작: {document.filename} v{document.version}")
            
            stats = self.incremental_embedding_service.process_document_reindex(
                self.db,
                document_id,
                chunk_data,
                user_id or document.created_by
            )
            
            logger.info(
                f"증분 인덱싱 완료: {document.filename} - "
                f"추가={stats['added']}, 수정={stats['modified']}, 삭제={stats['deleted']}"
            )
            
            return stats
        
        else:
            # 전체 인덱싱 (최초 인덱싱)
            logger.info(f"전체 인덱싱 시작: {document.filename} v{document.version}")
            
            # 텍스트만 추출 (RAG 엔진용)
            texts = [chunk["content"] for chunk in new_chunks_json]
            metadatas = [chunk["metadata"] for chunk in new_chunks_json]
            
            vector_ids = self.rag_engine.index_document(document_id, chunk_data)
            
            # DB에 청크 저장
            for chunk_json, vector_id in zip(new_chunks_json, vector_ids):
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_json["chunk_index"],
                    content=chunk_json["content"],
                    content_hash=chunk_json["content_hash"],
                    embedding_id=vector_id,
                    chunk_metadata=chunk_json["metadata"]
                )
                self.db.add(db_chunk)
            
            document.is_indexed = True
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"전체 인덱싱 완료: {document.filename} - {len(new_chunks_json)}개 청크")
            
            return {
                "total_chunks": len(new_chunks_json),
                "added": len(new_chunks_json),
                "modified": 0,
                "deleted": 0,
                "skipped_duplicates": 0
            }
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """문서 조회"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def list_documents(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """문서 목록 조회"""
        query = self.db.query(Document)
        
        if user_id:
            query = query.filter(Document.created_by == user_id)
        
        return query.order_by(Document.upload_date.desc()).offset(skip).limit(limit).all()
    
    def delete_document(self, document_id: str) -> bool:
        """문서 삭제"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # 파일 삭제
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # 데이터베이스에서 삭제 (관계로 인해 청크도 자동 삭제)
        self.db.delete(document)
        self.db.commit()
        
        return True

