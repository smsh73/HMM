"""
API 스키마 (Pydantic 모델)
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# 인증 스키마
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 문서 스키마
class DocumentUpload(BaseModel):
    filename: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    is_parsed: bool
    is_indexed: bool
    doc_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# 검색 스키마
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    generate_answer: Optional[bool] = False
    filter_dict: Optional[Dict[str, Any]] = None
    use_main_system: Optional[bool] = True
    provider_name: Optional[str] = None
    
    class Config:
        # 입력 검증
        min_length = {"query": 1}
        max_length = {"query": 1000}


class SearchResultResponse(BaseModel):
    content: str
    score: float
    document_id: str
    chunk_index: int
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultResponse]
    answer: Optional[Dict[str, Any]] = None
    total_results: int


# 요약 스키마
class SummaryRequest(BaseModel):
    summary_type: Optional[str] = "core"  # core, detailed, keywords
    use_main_system: Optional[bool] = True
    provider_name: Optional[str] = None


class SummaryResponse(BaseModel):
    document_id: str
    summary_type: str
    content: str
    keywords: List[str]
    quality_score: float
    original_length: int
    summary_length: int


# 권한 스키마
class PermissionCreate(BaseModel):
    document_id: str
    user_id: Optional[str] = None
    role: Optional[str] = None
    permission_type: str = "read"


class PermissionResponse(BaseModel):
    id: str
    document_id: str
    user_id: Optional[str]
    role: Optional[str]
    permission_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

