"""
시스템 역할 관리 서비스
메인서버/선박클라이언트 역할 설정 및 관리
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.database import SystemRole
from app.core.logging import logger


class SystemRoleService:
    """시스템 역할 관리 서비스"""
    
    def __init__(self, db: Session):
        """시스템 역할 서비스 초기화"""
        self.db = db
    
    def get_system_role(self) -> Optional[SystemRole]:
        """현재 시스템 역할 조회"""
        # 시스템은 하나의 역할만 가질 수 있음
        return self.db.query(SystemRole).filter(
            SystemRole.is_active == True
        ).first()
    
    def set_system_role(
        self,
        role: str,
        system_name: Optional[str] = None,
        connection_ip: Optional[str] = None,
        connection_port: Optional[int] = None,
        connection_token: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> SystemRole:
        """
        시스템 역할 설정
        
        Args:
            role: 시스템 역할 ("main_server" 또는 "ship_client")
            system_name: 시스템 이름
            connection_ip: 연결 IP 주소 (선박클라이언트인 경우 메인서버 IP)
            connection_port: 연결 포트
            connection_token: 인증 토큰
            config: 추가 설정
            
        Returns:
            SystemRole 객체
        """
        # 기존 역할 비활성화
        existing_role = self.db.query(SystemRole).filter(
            SystemRole.is_active == True
        ).first()
        
        if existing_role:
            existing_role.is_active = False
            self.db.commit()
        
        # 새 역할 생성 또는 업데이트
        system_role = self.db.query(SystemRole).filter(
            SystemRole.role == role
        ).first()
        
        if system_role:
            # 기존 역할 업데이트
            system_role.is_active = True
            system_role.system_name = system_name or system_role.system_name
            system_role.connection_ip = connection_ip or system_role.connection_ip
            system_role.connection_port = connection_port or system_role.connection_port
            system_role.connection_token = connection_token or system_role.connection_token
            if config:
                system_role.config = {**(system_role.config or {}), **config}
            system_role.updated_at = datetime.utcnow()
        else:
            # 새 역할 생성
            system_role = SystemRole(
                role=role,
                system_name=system_name or f"{role}_system",
                connection_ip=connection_ip,
                connection_port=connection_port,
                connection_token=connection_token,
                is_active=True,
                config=config or {}
            )
            self.db.add(system_role)
        
        self.db.commit()
        self.db.refresh(system_role)
        
        logger.info(f"시스템 역할 설정: {role} - {system_name}")
        
        return system_role
    
    def is_main_server(self) -> bool:
        """메인서버인지 확인"""
        role = self.get_system_role()
        return role is not None and role.role == "main_server"
    
    def is_ship_client(self) -> bool:
        """선박클라이언트인지 확인"""
        role = self.get_system_role()
        return role is not None and role.role == "ship_client"
    
    def get_connection_info(self) -> Optional[Dict[str, Any]]:
        """연결 정보 조회"""
        role = self.get_system_role()
        if not role:
            return None
        
        return {
            "role": role.role,
            "system_name": role.system_name,
            "connection_ip": role.connection_ip,
            "connection_port": role.connection_port,
            "has_token": bool(role.connection_token)
        }
    
    def update_last_sync(self):
        """마지막 동기화 시간 업데이트"""
        role = self.get_system_role()
        if role:
            role.last_sync_at = datetime.utcnow()
            self.db.commit()

