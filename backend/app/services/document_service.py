"""
문서 서비스
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path

from app.models.database import Document, DocumentChunk, User
from app.parsers.parser_factory import ParserFactory
from app.parsers.base import ParsedDocument
from app.ai.rag_engine import RAGSearchEngine
from app.core.config import settings


class DocumentService:
    """문서 관리 서비스"""
    
    def __init__(self, db: Session):
        """문서 서비스 초기화"""
        self.db = db
        self.rag_engine = RAGSearchEngine()
    
    def upload_document(
        self,
        file_path: str,
        filename: str,
        user_id: str
    ) -> Document:
        """문서 업로드"""
        # 파일 정보
        file_size = os.path.getsize(file_path)
        file_type = Path(filename).suffix.lower().replace(".", "")
        
        # 저장 경로 생성
        save_path = os.path.join(settings.UPLOAD_DIR, filename)
        shutil.copy2(file_path, save_path)
        
        # 데이터베이스에 문서 정보 저장
        document = Document(
            filename=filename,
            file_type=file_type,
            file_path=save_path,
            file_size=file_size,
            created_by=user_id,
            is_parsed=False,
            is_indexed=False
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def parse_document(self, document_id: str) -> Document:
        """문서 파싱"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("문서를 찾을 수 없습니다.")
        
        if not ParserFactory.is_supported(document.file_path):
            raise ValueError(f"지원하지 않는 파일 형식입니다: {document.file_type}")
        
        # 파서로 문서 파싱
        parser = ParserFactory.get_parser(document.file_path)
        parsed_doc: ParsedDocument = parser.parse(document.file_path)
        
        # 파싱 결과 저장
        document.parsed_content = {
            "full_text": parsed_doc.full_text,
            "structure": parsed_doc.structure,
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
        
        # 청크 저장
        for chunk in parsed_doc.chunks:
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                chunk_metadata={
                    "page_number": chunk.page_number,
                    "section_title": chunk.section_title,
                    **(chunk.metadata if hasattr(chunk, 'metadata') and chunk.metadata else {})
                }
            )
            self.db.add(db_chunk)
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def index_document(self, document_id: str) -> Document:
        """문서 인덱싱 (벡터화)"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("문서를 찾을 수 없습니다.")
        
        if not document.is_parsed:
            raise ValueError("문서가 파싱되지 않았습니다. 먼저 파싱을 수행하세요.")
        
        # 청크 조회
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
        
        if not chunks:
            raise ValueError("파싱된 청크가 없습니다.")
        
        # RAG 엔진에 인덱싱
        chunk_data = [
            {
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.chunk_metadata or {}
            }
            for chunk in chunks
        ]
        
        vector_ids = self.rag_engine.index_document(document_id, chunk_data)
        
        # 벡터 ID 저장
        for chunk, vector_id in zip(chunks, vector_ids):
            chunk.embedding_id = vector_id
        
        document.is_indexed = True
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
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

