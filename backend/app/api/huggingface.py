"""
Hugging Face 모델 API 라우터
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.huggingface_service import HuggingFaceService
from app.models.database import User

router = APIRouter(prefix="/huggingface", tags=["Hugging Face"])


@router.get("/models/search")
async def search_models(
    q: str = Query("", description="검색어"),
    task: Optional[str] = Query(None, description="태스크 (text-generation, text2text-generation 등)"),
    library: Optional[str] = Query(None, description="라이브러리 (transformers, onnx 등)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Hugging Face 모델 검색"""
    hf_service = HuggingFaceService(db)
    models = await hf_service.search_models(
        query=q,
        task=task,
        library=library,
        limit=limit
    )
    return {"models": models}


@router.post("/models/{model_id}/download")
async def download_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Hugging Face 모델 다운로드"""
    hf_service = HuggingFaceService(db)
    result = await hf_service.download_model(model_id)
    return result


@router.get("/models/downloaded")
async def get_downloaded_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """다운로드된 Hugging Face 모델 목록"""
    hf_service = HuggingFaceService(db)
    models = hf_service.get_downloaded_models()
    return {"models": models}

