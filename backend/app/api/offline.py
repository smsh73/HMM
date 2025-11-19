"""
오프라인 동작 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.offline_service import OfflineService
from app.models.database import User

router = APIRouter(prefix="/offline", tags=["오프라인 동작"])


@router.get("/status")
async def get_offline_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """오프라인 상태 및 시스템 상태 조회"""
    offline_service = OfflineService(db)
    status_info = offline_service.get_system_status()
    
    return status_info


@router.get("/logs")
async def get_offline_logs(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """오프라인 로그 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 조회할 수 있습니다."
        )
    
    offline_service = OfflineService(db)
    logs = offline_service.get_offline_logs(date)
    
    return {"logs": logs, "count": len(logs)}


@router.post("/sync")
async def sync_offline_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """오프라인 로그 동기화"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 동기화할 수 있습니다."
        )
    
    offline_service = OfflineService(db)
    result = offline_service.sync_offline_logs()
    
    return result

