"""
애플리케이션 설정
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    PROJECT_NAME: str = "GenAI 문서 검색/요약 시스템"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 설정
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # 데이터베이스 설정
    # PostgreSQL (프로덕션)
    # DATABASE_URL: str = "postgresql://user:password@localhost:5432/hmm_db"
    # SQLite (개발/테스트용)
    DATABASE_URL: str = "sqlite:///./data/documents.db"
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"]
    
    # 로깅 설정
    LOG_DIR: str = "./data/logs"
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI/ML 설정
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    VECTOR_DB_PATH: str = "./data/vector_db"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2:7b"
    
    # 성능 설정
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_SEARCH_RESULTS: int = 10
    BATCH_SIZE: int = 32
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()

# 디렉토리 생성
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
os.makedirs(settings.LOG_DIR, exist_ok=True)
os.makedirs("./data", exist_ok=True)

