"""
문서 관리 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import tempfile

from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_user
from app.api.schemas import DocumentResponse
from app.services.document_service import DocumentService
from app.services.permission_service import PermissionService
from app.models.database import User

router = APIRouter(prefix="/documents", tags=["문서"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서 업로드"""
    # 파일 확장자 확인
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )
        
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # 문서 서비스로 업로드
        doc_service = DocumentService(db)
        document = doc_service.upload_document(
            file_path=tmp_path,
            filename=file.filename,
            user_id=current_user.id
        )
        
        return document
    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서 목록 조회"""
    doc_service = DocumentService(db)
    documents = doc_service.list_documents(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서 상세 조회"""
    doc_service = DocumentService(db)
    permission_service = PermissionService(db)
    
    document = doc_service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다."
        )
    
    # 권한 확인
    if not permission_service.check_permission(current_user.id, document_id, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 문서에 대한 접근 권한이 없습니다."
        )
    
    return document


@router.post("/{document_id}/parse", response_model=DocumentResponse)
async def parse_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서 파싱"""
    doc_service = DocumentService(db)
    permission_service = PermissionService(db)
    
    # 권한 확인
    if not permission_service.check_permission(current_user.id, document_id, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 문서를 파싱할 권한이 없습니다."
        )
    
    try:
        document = doc_service.parse_document(document_id)
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{document_id}/index", response_model=DocumentResponse)
async def index_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서 인덱싱"""
    doc_service = DocumentService(db)
    permission_service = PermissionService(db)
    
    # 권한 확인
    if not permission_service.check_permission(current_user.id, document_id, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 문서를 인덱싱할 권한이 없습니다."
        )
    
    try:
        document = doc_service.index_document(document_id)
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서 삭제"""
    doc_service = DocumentService(db)
    permission_service = PermissionService(db)
    
    # 권한 확인
    if not permission_service.check_permission(current_user.id, document_id, "delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 문서를 삭제할 권한이 없습니다."
        )
    
    success = doc_service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다."
        )
    
    return {"message": "문서가 삭제되었습니다."}

