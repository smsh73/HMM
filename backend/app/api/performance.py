"""
성능 모니터링 API 라우터
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.utils.performance import PerformanceMonitor
from app.models.database import User

router = APIRouter(prefix="/performance", tags=["성능 모니터링"])


@router.get("/system")
async def get_system_resources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """시스템 리소스 사용량 조회"""
    # 관리자만 조회 가능
    if current_user.role != "admin":
        return {"error": "권한이 없습니다."}
    
    return PerformanceMonitor.get_system_resources()


@router.get("/process")
async def get_process_resources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """프로세스 리소스 사용량 조회"""
    # 관리자만 조회 가능
    if current_user.role != "admin":
        return {"error": "권한이 없습니다."}
    
    return PerformanceMonitor.get_process_resources()

