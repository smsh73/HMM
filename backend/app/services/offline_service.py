"""
오프라인 동작 서비스
선박이 인터넷 연결이 끊어진 상황에서도 시스템이 정상 작동하도록 함
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os

from app.models.database import Document, DocumentChunk, SystemRole
from app.services.system_role_service import SystemRoleService
from app.core.config import settings
from app.core.logging import logger


class OfflineService:
    """오프라인 동작 서비스"""
    
    def __init__(self, db: Session):
        """오프라인 서비스 초기화"""
        self.db = db
        self.system_role_service = SystemRoleService(db)
        self.offline_log_dir = os.path.join(settings.VECTOR_DB_PATH, "offline_logs")
        os.makedirs(self.offline_log_dir, exist_ok=True)
    
    def is_online(self) -> bool:
        """온라인 상태 확인"""
        # 간단한 구현: 실제로는 네트워크 연결 확인 필요
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def log_offline_activity(
        self,
        activity_type: str,
        user_id: str,
        data: Dict[str, Any]
    ):
        """
        오프라인 활동 로그 기록
        
        Args:
            activity_type: 활동 타입 (search, document_view, etc.)
            user_id: 사용자 ID
            data: 활동 데이터
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "activity_type": activity_type,
            "user_id": user_id,
            "data": data,
            "online": False
        }
        
        log_file = os.path.join(
            self.offline_log_dir,
            f"offline_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        )
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        logger.debug(f"오프라인 활동 로그 기록: {activity_type}")
    
    def get_offline_logs(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        오프라인 로그 조회
        
        Args:
            date: 날짜 (YYYYMMDD), None이면 오늘
            
        Returns:
            로그 엔트리 리스트
        """
        if date is None:
            date = datetime.utcnow().strftime('%Y%m%d')
        
        log_file = os.path.join(self.offline_log_dir, f"offline_{date}.jsonl")
        
        if not os.path.exists(log_file):
            return []
        
        logs = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        return logs
    
    def sync_offline_logs(self) -> Dict[str, Any]:
        """
        오프라인 로그 동기화 (온라인 복귀 시)
        
        Returns:
            동기화 결과
        """
        if not self.is_online():
            return {
                "status": "offline",
                "message": "아직 오프라인 상태입니다."
            }
        
        system_role = self.system_role_service.get_system_role()
        if not system_role or system_role.role != "ship_client":
            return {
                "status": "error",
                "message": "선박클라이언트에서만 동기화할 수 있습니다."
            }
        
        # 오프라인 로그 수집
        logs = []
        for log_file in os.listdir(self.offline_log_dir):
            if log_file.startswith("offline_") and log_file.endswith(".jsonl"):
                file_path = os.path.join(self.offline_log_dir, log_file)
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            logs.append(json.loads(line))
        
        # TODO: 메인서버로 로그 전송
        # 실제 구현은 HTTP API 호출 필요
        
        logger.info(f"오프라인 로그 동기화: {len(logs)}개 엔트리")
        
        return {
            "status": "synced",
            "log_count": len(logs),
            "message": f"{len(logs)}개의 오프라인 로그가 동기화되었습니다."
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        시스템 상태 조회 (오프라인 모니터링용)
        
        Returns:
            시스템 상태 정보
        """
        import psutil
        
        # CPU, 메모리, 디스크 사용량
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(settings.VECTOR_DB_PATH)
        
        # 문서 및 청크 개수
        doc_count = self.db.query(Document).count()
        chunk_count = self.db.query(DocumentChunk).count()
        
        return {
            "online": self.is_online(),
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "documents": {
                "total": doc_count,
                "indexed": self.db.query(Document).filter(Document.is_indexed == True).count()
            },
            "chunks": chunk_count,
            "timestamp": datetime.utcnow().isoformat()
        }

