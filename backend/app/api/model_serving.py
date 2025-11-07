"""
모델 서빙 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.model_serving_service import ModelServingService
from app.models.database import User

router = APIRouter(prefix="/serving", tags=["모델 서빙"])


class StartServingRequest(BaseModel):
    model_id: str
    model_type: str = "ollama"


class TestModelRequest(BaseModel):
    model_id: str
    prompt: str = "Hello"


@router.post("/start")
async def start_serving(
    request: StartServingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모델 서빙 시작"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 모델 서빙을 시작할 수 있습니다."
        )
    
    serving_service = ModelServingService(db)
    result = await serving_service.start_serving(
        model_id=request.model_id,
        model_type=request.model_type
    )
    return result


@router.post("/stop/{model_id}")
async def stop_serving(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모델 서빙 중지"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 모델 서빙을 중지할 수 있습니다."
        )
    
    serving_service = ModelServingService(db)
    result = await serving_service.stop_serving(model_id)
    return result


@router.get("/status")
async def get_serving_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """서빙 중인 모델 상태 조회"""
    serving_service = ModelServingService(db)
    statuses = await serving_service.get_serving_status()
    return {"models": statuses}


@router.post("/test")
async def test_model(
    request: TestModelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모델 테스트"""
    serving_service = ModelServingService(db)
    result = await serving_service.test_model(
        model_id=request.model_id,
        prompt=request.prompt
    )
    return result

