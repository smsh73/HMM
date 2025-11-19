"""
데이터베이스 모델
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Boolean
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
    file_hash = Column(String, nullable=True, index=True)  # SHA-256 해시 (변경 감지용)
    previous_hash = Column(String, nullable=True)  # 이전 버전 해시
    version = Column(Integer, default=1)  # 문서 버전
    upload_date = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    parsed_content = Column(JSON)  # 파싱된 내용 구조
    doc_metadata = Column(JSON)  # 문서 메타데이터 (metadata는 SQLAlchemy 예약어)
    created_by = Column(String, ForeignKey("users.id"))
    is_parsed = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    needs_reindex = Column(Boolean, default=False)  # 증분 인덱싱 플래그
    
    # 관계
    creator = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    permissions = relationship("Permission", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """문서 버전 이력 모델 (CDC용)"""
    __tablename__ = "document_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    version = Column(Integer, nullable=False)
    file_hash = Column(String, nullable=False)  # 해당 버전의 SHA-256 해시
    file_path = Column(String)  # 버전별 파일 경로 (옵션)
    change_type = Column(String, default="modified")  # created, modified, deleted
    changed_chunks = Column(JSON)  # 변경된 청크 ID 리스트
    delta_size = Column(Integer, default=0)  # 증분 데이터 크기
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"))
    
    # 관계
    document = relationship("Document", back_populates="versions")


class DocumentChunk(Base):
    """문서 청크 모델"""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON)  # 청크 메타데이터 (페이지 번호, 섹션 등)
    embedding_id = Column(String)  # 벡터 DB의 ID
    content_hash = Column(String)  # 청크 콘텐츠 해시 (변경 감지용)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    feedbacks = relationship("SearchFeedback", back_populates="search")


class SearchFeedback(Base):
    """검색 피드백 모델"""
    __tablename__ = "search_feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    search_id = Column(String, ForeignKey("search_history.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    query = Column(String, nullable=False)  # 검색 쿼리 (검색 성능 분석용)
    result_id = Column(String, nullable=False)  # 피드백 대상 결과 ID
    feedback_type = Column(String, nullable=False)  # relevant, irrelevant, helpful, not_helpful
    rating = Column(Integer)  # 평점 (1-5)
    comment = Column(Text)  # 코멘트
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    search = relationship("SearchHistory", back_populates="feedbacks")


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
    model_type = Column(String, default="ollama")  # ollama, gpt4all, transformers 등
    model_size = Column(Integer)  # 모델 크기 (bytes)
    is_downloaded = Column(Boolean, default=False)
    is_serving = Column(Boolean, default=False)  # 서빙 중 여부
    download_progress = Column(Integer, default=0)  # 다운로드 진행률 (0-100)
    model_metadata = Column(JSON)  # 모델 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemRole(Base):
    """시스템 역할 모델 (메인서버/선박클라이언트)"""
    __tablename__ = "system_roles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False, unique=True)  # main_server, ship_client
    system_name = Column(String)  # 시스템 이름
    connection_ip = Column(String)  # 연결 IP 주소
    connection_port = Column(Integer)  # 연결 포트
    connection_token = Column(String)  # 인증 토큰
    is_active = Column(Boolean, default=True)  # 활성화 여부
    last_sync_at = Column(DateTime)  # 마지막 동기화 시간
    config = Column(JSON)  # 추가 설정
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeltaPackage(Base):
    """델타 패키지 모델"""
    __tablename__ = "delta_packages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    package_type = Column(String, nullable=False)  # document_add, document_update, document_delete
    source_system = Column(String)  # 출발 시스템
    target_system = Column(String)  # 대상 시스템
    document_ids = Column(JSON)  # 변경된 문서 ID 리스트
    chunk_ids = Column(JSON)  # 변경된 청크 ID 리스트
    file_path = Column(String)  # 델타 파일 경로
    file_size = Column(Integer)  # 파일 크기 (bytes)
    checksum = Column(String)  # 파일 체크섬
    status = Column(String, default="pending")  # pending, ready, sending, sent, failed
    send_type = Column(String)  # immediate, scheduled
    scheduled_at = Column(DateTime)  # 스케줄 전송 시간
    sent_at = Column(DateTime)  # 전송 완료 시간
    package_metadata = Column(JSON)  # 패키지 메타데이터 (metadata는 SQLAlchemy 예약어)
    created_at = Column(DateTime, default=datetime.utcnow)


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


class ChatConversation(Base):
    """채팅 대화 모델"""
    __tablename__ = "chat_conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String)  # 대화 제목 (첫 메시지 기반)
    use_rag = Column(Boolean, default=False)
    use_main_system = Column(Boolean, default=True)
    provider_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """채팅 메시지 모델"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("chat_conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON)  # RAG 출처 정보
    provider = Column(String)  # 사용된 프로바이더
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    conversation = relationship("ChatConversation", back_populates="messages")
