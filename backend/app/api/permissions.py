"""
권한 관리 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.schemas import PermissionCreate, PermissionResponse
from app.services.permission_service import PermissionService
from app.models.database import User

router = APIRouter(prefix="/permissions", tags=["권한"])


@router.post("", response_model=PermissionResponse)
async def create_permission(
    permission_create: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """권한 설정"""
    # 관리자만 권한 설정 가능
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한 설정은 관리자만 가능합니다."
        )
    
    permission_service = PermissionService(db)
    
    try:
        permission = permission_service.set_permission(
            document_id=permission_create.document_id,
            user_id=permission_create.user_id,
            role=permission_create.role,
            permission_type=permission_create.permission_type
        )
        return permission
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/documents/{document_id}", response_model=List[PermissionResponse])
async def get_document_permissions(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서의 권한 목록 조회"""
    # 관리자만 조회 가능
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한 목록 조회는 관리자만 가능합니다."
        )
    
    permission_service = PermissionService(db)
    permissions = permission_service.get_document_permissions(document_id)
    return permissions


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """권한 삭제"""
    # 관리자만 삭제 가능
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한 삭제는 관리자만 가능합니다."
        )
    
    permission_service = PermissionService(db)
    success = permission_service.delete_permission(permission_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="권한을 찾을 수 없습니다."
        )
    
    return {"message": "권한이 삭제되었습니다."}

