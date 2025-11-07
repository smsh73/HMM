"""
로컬 모델 관리 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.model_service import ModelService
from app.models.database import User

router = APIRouter(prefix="/models", tags=["로컬 모델"])


@router.get("/available")
async def list_available_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용 가능한 모델 목록 조회 (Ollama)"""
    model_service = ModelService(db)
    models = await model_service.list_available_models()
    return {"models": models}


@router.get("/local")
async def get_local_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """로컬 모델 목록 조회"""
    model_service = ModelService(db)
    models = model_service.get_local_models()
    return {"models": models}


@router.post("/download/{model_name}")
async def download_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모델 다운로드"""
    model_service = ModelService(db)
    result = await model_service.download_model(model_name)
    return result


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """로컬 모델 삭제"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 삭제할 수 있습니다."
        )
    
    model_service = ModelService(db)
    success = model_service.delete_model(model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="모델을 찾을 수 없습니다."
        )
    
    return {"message": "모델이 삭제되었습니다."}

