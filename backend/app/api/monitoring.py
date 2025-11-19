"""
시스템 모니터링 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.monitoring_service import (
    MonitoringService,
    GradualRolloutService,
    RemoteDiagnosticsService
)
from app.models.database import User

router = APIRouter(prefix="/monitoring", tags=["시스템 모니터링"])


class RolloutRequest(BaseModel):
    package_id: str
    target_systems: List[str]


@router.get("/systems")
async def get_all_systems_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모든 시스템 상태 조회 (중앙 관리 콘솔)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 조회할 수 있습니다."
        )
    
    monitoring_service = MonitoringService(db)
    systems = monitoring_service.get_all_systems_status()
    
    return {"systems": systems}


@router.get("/deployment")
async def get_deployment_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """배포 상태 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 조회할 수 있습니다."
        )
    
    monitoring_service = MonitoringService(db)
    status_info = monitoring_service.get_deployment_status()
    
    return status_info


@router.post("/rollout/start")
async def start_rollout(
    request: RolloutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """점진적 롤아웃 시작"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 롤아웃을 시작할 수 있습니다."
        )
    
    rollout_service = GradualRolloutService(db)
    rollout_plan = rollout_service.start_rollout(
        package_id=request.package_id,
        target_systems=request.target_systems
    )
    
    return rollout_plan


@router.get("/rollout/status")
async def get_rollout_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """롤아웃 상태 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 조회할 수 있습니다."
        )
    
    rollout_service = GradualRolloutService(db)
    status_info = rollout_service.get_rollout_status()
    
    return status_info or {"status": "no_rollout"}


@router.get("/diagnostics/{system_id}/logs")
async def collect_logs(
    system_id: str,
    log_types: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """원격 시스템 로그 수집"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 로그를 수집할 수 있습니다."
        )
    
    diagnostics_service = RemoteDiagnosticsService(db)
    logs = diagnostics_service.collect_logs(
        system_id=system_id,
        log_types=log_types or ["application", "error"]
    )
    
    return logs


@router.get("/diagnostics/{system_id}/metrics")
async def get_system_metrics(
    system_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """원격 시스템 메트릭 수집"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 메트릭을 수집할 수 있습니다."
        )
    
    diagnostics_service = RemoteDiagnosticsService(db)
    metrics = diagnostics_service.get_system_metrics(system_id)
    
    return metrics

