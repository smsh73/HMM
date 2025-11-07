"""
데이터베이스 모델
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.sqlite import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    documents = relationship("Document", back_populates="creator")
    search_history = relationship("SearchHistory", back_populates="user")


class Document(Base):
    """문서 모델"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, xlsx, txt
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    parsed_content = Column(JSON)  # 파싱된 내용 구조
    metadata = Column(JSON)  # 문서 메타데이터
    created_by = Column(String, ForeignKey("users.id"))
    is_parsed = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    
    # 관계
    creator = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    permissions = relationship("Permission", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """문서 청크 모델"""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON)  # 청크 메타데이터 (페이지 번호, 섹션 등)
    embedding_id = Column(String)  # 벡터 DB의 ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    document = relationship("Document", back_populates="chunks")


class Permission(Base):
    """권한 모델"""
    __tablename__ = "permissions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # 사용자별 권한
    role = Column(String, nullable=True)  # 역할별 권한
    permission_type = Column(String, nullable=False)  # read, write, delete
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    document = relationship("Document", back_populates="permissions")


class SearchHistory(Base):
    """검색 기록 모델"""
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    query = Column(String, nullable=False)
    results_count = Column(Integer, default=0)
    search_date = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    user = relationship("User", back_populates="search_history")


class LLMProvider(Base):
    """LLM 프로바이더 설정 모델"""
    __tablename__ = "llm_providers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_name = Column(String, nullable=False, unique=True, index=True)  # openai, claude, gemini, perplexity, ollama
    api_key = Column(Text)  # 암호화된 API 키
    base_url = Column(String)  # API 베이스 URL (필요한 경우)
    model_name = Column(String)  # 기본 모델명
    is_active = Column(Boolean, default=True)
    is_main_system = Column(Boolean, default=False)  # 메인 시스템용 여부
    config = Column(JSON)  # 추가 설정
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LocalModel(Base):
    """로컬 모델 정보 모델"""
    __tablename__ = "local_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, nullable=False, unique=True, index=True)  # ollama 모델명
    model_type = Column(String, default="ollama")  # ollama, gpt4all 등
    model_size = Column(Integer)  # 모델 크기 (bytes)
    is_downloaded = Column(Boolean, default=False)
    download_progress = Column(Integer, default=0)  # 다운로드 진행률 (0-100)
    metadata = Column(JSON)  # 모델 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RAGSync(Base):
    """RAG 동기화 기록 모델"""
    __tablename__ = "rag_sync"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sync_type = Column(String, nullable=False)  # export, import
    source_system = Column(String)  # 메인 시스템 식별자
    target_system = Column(String)  # 선박 시스템 식별자
    vector_db_path = Column(String)  # 벡터 DB 경로
    metadata_path = Column(String)  # 메타데이터 경로
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    progress = Column(Integer, default=0)  # 동기화 진행률 (0-100)
    error_message = Column(Text)  # 오류 메시지
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
