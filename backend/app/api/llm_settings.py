"""
LLM 설정 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.provider_service import ProviderService
from app.models.database import User

router = APIRouter(prefix="/llm", tags=["LLM 설정"])


class ProviderCreate(BaseModel):
    provider_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    is_main_system: bool = True
    config: Optional[dict] = None


class ProviderUpdate(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    is_main_system: Optional[bool] = None
    config: Optional[dict] = None


@router.get("/providers")
async def get_providers(
    is_main_system: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로바이더 목록 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 접근할 수 있습니다."
        )
    
    provider_service = ProviderService(db)
    return {"providers": provider_service.get_providers(is_main_system=is_main_system)}


@router.post("/providers", status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로바이더 생성"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 접근할 수 있습니다."
        )
    
    provider_service = ProviderService(db)
    provider = provider_service.create_or_update_provider(
        provider_name=provider_data.provider_name,
        api_key=provider_data.api_key,
        base_url=provider_data.base_url,
        model_name=provider_data.model_name,
        is_main_system=provider_data.is_main_system,
        config=provider_data.config
    )
    
    return {
        "id": provider.id,
        "provider_name": provider.provider_name,
        "is_main_system": provider.is_main_system,
        "is_active": provider.is_active
    }


@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    provider_data: ProviderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로바이더 업데이트"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 접근할 수 있습니다."
        )
    
    provider_service = ProviderService(db)
    provider = provider_service.get_provider(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로바이더를 찾을 수 없습니다."
        )
    
    provider_service.create_or_update_provider(
        provider_name=provider.provider_name,
        api_key=provider_data.api_key,
        base_url=provider_data.base_url,
        model_name=provider_data.model_name,
        is_main_system=provider_data.is_main_system if provider_data.is_main_system is not None else provider.is_main_system,
        config=provider_data.config
    )
    
    return {"message": "프로바이더가 업데이트되었습니다."}


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로바이더 삭제"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 접근할 수 있습니다."
        )
    
    provider_service = ProviderService(db)
    success = provider_service.delete_provider(provider_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로바이더를 찾을 수 없습니다."
        )
    
    return {"message": "프로바이더가 삭제되었습니다."}


@router.post("/providers/{provider_id}/toggle")
async def toggle_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로바이더 활성/비활성 토글"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 접근할 수 있습니다."
        )
    
    provider_service = ProviderService(db)
    success = provider_service.toggle_provider_status(provider_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로바이더를 찾을 수 없습니다."
        )
    
    return {"message": "프로바이더 상태가 변경되었습니다."}

