"""
파일 전송 서비스
HTTP/2를 통한 델타 파일 전송
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
import httpx
import asyncio

from app.models.database import DeltaPackage, SystemRole
from app.services.system_role_service import SystemRoleService
from app.core.logging import logger


class FileTransferService:
    """파일 전송 서비스"""
    
    def __init__(self, db: Session):
        """파일 전송 서비스 초기화"""
        self.db = db
        self.system_role_service = SystemRoleService(db)
    
    async def send_delta_package(
        self,
        package_id: str,
        send_type: str = "immediate"
    ) -> Dict[str, Any]:
        """
        델타 패키지 전송
        
        Args:
            package_id: 패키지 ID
            send_type: 전송 타입 (immediate, scheduled)
            
        Returns:
            전송 결과
        """
        # 패키지 조회
        package = self.db.query(DeltaPackage).filter(
            DeltaPackage.id == package_id
        ).first()
        
        if not package:
            raise ValueError("패키지를 찾을 수 없습니다.")
        
        if not os.path.exists(package.file_path):
            raise ValueError("패키지 파일을 찾을 수 없습니다.")
        
        # 시스템 역할 확인
        system_role = self.system_role_service.get_system_role()
        if not system_role or system_role.role != "main_server":
            raise ValueError("메인서버에서만 전송할 수 있습니다.")
        
        if send_type == "scheduled":
            # 스케줄 전송은 큐에 추가
            package.send_type = "scheduled"
            package.status = "pending"
            self.db.commit()
            return {
                "package_id": package_id,
                "status": "scheduled",
                "message": "스케줄 전송이 등록되었습니다."
            }
        
        # 즉시 전송
        try:
            package.status = "sending"
            self.db.commit()
            
            # 선박 클라이언트 연결 정보
            target_url = f"http://{system_role.connection_ip}:{system_role.connection_port or 8000}"
            
            # 적응적 전송 서비스 사용
            adaptive_service = AdaptiveTransferService()
            
            # HTTP/2 클라이언트로 파일 전송
            async with httpx.AsyncClient(http2=True, timeout=300.0) as client:
                with open(package.file_path, "rb") as f:
                    files = {"file": (os.path.basename(package.file_path), f, "application/zip")}
                    data = {
                        "package_id": package_id,
                        "checksum": package.checksum,
                        "file_size": package.file_size
                    }
                    
                    # 인증 토큰 추가
                    headers = {}
                    if system_role.connection_token:
                        headers["Authorization"] = f"Bearer {system_role.connection_token}"
                    
                    response = await client.post(
                        f"{target_url}/api/delta-sync/receive",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        package.status = "sent"
                        package.sent_at = datetime.utcnow()
                        self.db.commit()
                        
                        logger.info(f"델타 패키지 전송 완료: {package_id}")
                        
                        return {
                            "package_id": package_id,
                            "status": "sent",
                            "message": "전송이 완료되었습니다."
                        }
                    else:
                        raise Exception(f"전송 실패: {response.status_code} - {response.text}")
        
        except Exception as e:
            package.status = "failed"
            package.error_message = str(e)
            self.db.commit()
            logger.error(f"델타 패키지 전송 실패: {package_id} - {e}")
            raise
    
    async def receive_delta_package(
        self,
        file_path: str,
        package_id: str,
        checksum: str,
        file_size: int
    ) -> Dict[str, Any]:
        """
        델타 패키지 수신
        
        Args:
            file_path: 수신된 파일 경로
            package_id: 패키지 ID
            checksum: 파일 체크섬
            file_size: 파일 크기
            
        Returns:
            수신 결과
        """
        # 시스템 역할 확인
        system_role = self.system_role_service.get_system_role()
        if not system_role or system_role.role != "ship_client":
            raise ValueError("선박클라이언트에서만 수신할 수 있습니다.")
        
        # 파일 검증
        if not os.path.exists(file_path):
            raise ValueError("수신된 파일을 찾을 수 없습니다.")
        
        actual_size = os.path.getsize(file_path)
        if actual_size != file_size:
            raise ValueError(f"파일 크기 불일치: 예상={file_size}, 실제={actual_size}")
        
        # 체크섬 검증
        from app.services.delta_service import DeltaService
        delta_service = DeltaService(self.db)
        actual_checksum = delta_service._calculate_checksum(file_path)
        
        if actual_checksum != checksum:
            raise ValueError(f"체크섬 불일치: 예상={checksum}, 실제={actual_checksum}")
        
        # 델타 패키지 설치
        from app.services.delta_install_service import DeltaInstallService
        install_service = DeltaInstallService(self.db)
        install_result = install_service.install_delta_package(file_path)
        
        logger.info(f"델타 패키지 수신 및 설치 완료: {package_id}")
        
        return {
            "package_id": package_id,
            "status": "received",
            "message": "수신이 완료되었습니다."
        }

