"""
시스템 역할 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.system_role_service import SystemRoleService
from app.models.database import User

router = APIRouter(prefix="/system-role", tags=["시스템 역할"])


class SystemRoleRequest(BaseModel):
    role: str  # main_server, ship_client
    system_name: Optional[str] = None
    connection_ip: Optional[str] = None
    connection_port: Optional[int] = None
    connection_token: Optional[str] = None
    config: Optional[dict] = None


@router.get("/")
async def get_system_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 시스템 역할 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 조회할 수 있습니다."
        )
    
    service = SystemRoleService(db)
    role = service.get_system_role()
    
    if not role:
        return {"role": None, "message": "시스템 역할이 설정되지 않았습니다."}
    
    return {
        "role": role.role,
        "system_name": role.system_name,
        "connection_ip": role.connection_ip,
        "connection_port": role.connection_port,
        "has_token": bool(role.connection_token),
        "is_active": role.is_active,
        "last_sync_at": role.last_sync_at.isoformat() if role.last_sync_at else None,
        "config": role.config
    }


@router.post("/")
async def set_system_role(
    request: SystemRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """시스템 역할 설정"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 설정할 수 있습니다."
        )
    
    if request.role not in ["main_server", "ship_client"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="역할은 'main_server' 또는 'ship_client'여야 합니다."
        )
    
    service = SystemRoleService(db)
    role = service.set_system_role(
        role=request.role,
        system_name=request.system_name,
        connection_ip=request.connection_ip,
        connection_port=request.connection_port,
        connection_token=request.connection_token,
        config=request.config
    )
    
    return {
        "role": role.role,
        "system_name": role.system_name,
        "message": f"시스템 역할이 '{role.role}'로 설정되었습니다."
    }

