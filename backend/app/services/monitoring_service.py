"""
시스템 관리 및 모니터링 서비스
중앙 관리 콘솔, 점진적 롤아웃, 원격 진단
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os

from app.models.database import SystemRole, DeltaPackage
from app.services.system_role_service import SystemRoleService
from app.core.config import settings
from app.core.logging import logger


class MonitoringService:
    """시스템 모니터링 서비스"""
    
    def __init__(self, db: Session):
        """모니터링 서비스 초기화"""
        self.db = db
        self.system_role_service = SystemRoleService(db)
    
    def get_all_systems_status(self) -> List[Dict[str, Any]]:
        """
        모든 시스템 상태 조회 (중앙 관리 콘솔용)
        
        Returns:
            시스템 상태 리스트
        """
        # TODO: 실제로는 다른 선박 시스템들의 상태를 수집
        # 현재는 로컬 시스템만 반환
        
        from app.services.offline_service import OfflineService
        offline_service = OfflineService(self.db)
        local_status = offline_service.get_system_status()
        
        system_role = self.system_role_service.get_system_role()
        
        return [{
            "system_id": system_role.system_name if system_role else "local",
            "role": system_role.role if system_role else "unknown",
            "status": local_status,
            "last_update": datetime.utcnow().isoformat()
        }]
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """
        배포 상태 조회
        
        Returns:
            배포 상태 정보
        """
        # 델타 패키지 배포 상태
        packages = self.db.query(DeltaPackage).filter(
            DeltaPackage.status.in_(["ready", "sending", "sent"])
        ).order_by(DeltaPackage.created_at.desc()).all()
        
        deployment_stats = {
            "total": len(packages),
            "ready": len([p for p in packages if p.status == "ready"]),
            "sending": len([p for p in packages if p.status == "sending"]),
            "sent": len([p for p in packages if p.status == "sent"]),
            "failed": len([p for p in packages if p.status == "failed"])
        }
        
        return deployment_stats


class GradualRolloutService:
    """점진적 롤아웃 서비스"""
    
    def __init__(self, db: Session):
        """점진적 롤아웃 서비스 초기화"""
        self.db = db
        self.rollout_stages = [0.10, 0.25, 0.50, 1.0]  # 10% → 25% → 50% → 100%
        self.rollout_config_file = os.path.join(settings.VECTOR_DB_PATH, "rollout_config.json")
    
    def start_rollout(
        self,
        package_id: str,
        target_systems: List[str]
    ) -> Dict[str, Any]:
        """
        점진적 롤아웃 시작
        
        Args:
            package_id: 배포할 패키지 ID
            target_systems: 대상 시스템 리스트
            
        Returns:
            롤아웃 정보
        """
        total_systems = len(target_systems)
        rollout_plan = {
            "package_id": package_id,
            "target_systems": target_systems,
            "total_systems": total_systems,
            "current_stage": 0,
            "current_percentage": 0.0,
            "deployed_systems": [],
            "failed_systems": [],
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # 롤아웃 계획 저장
        self._save_rollout_config(rollout_plan)
        
        # 첫 번째 단계 시작 (10%)
        self._deploy_stage(rollout_plan, 0)
        
        return rollout_plan
    
    def _deploy_stage(self, rollout_plan: Dict[str, Any], stage: int):
        """특정 단계 배포"""
        if stage >= len(self.rollout_stages):
            rollout_plan["status"] = "completed"
            return
        
        target_percentage = self.rollout_stages[stage]
        total_systems = rollout_plan["total_systems"]
        target_count = int(total_systems * target_percentage)
        
        # 아직 배포되지 않은 시스템 선택
        deployed = set(rollout_plan["deployed_systems"])
        available_systems = [
            s for s in rollout_plan["target_systems"]
            if s not in deployed
        ]
        
        systems_to_deploy = available_systems[:target_count - len(deployed)]
        
        # 배포 수행
        for system_id in systems_to_deploy:
            try:
                # TODO: 실제 배포 로직
                rollout_plan["deployed_systems"].append(system_id)
                logger.info(f"시스템 배포: {system_id}")
            except Exception as e:
                rollout_plan["failed_systems"].append({
                    "system_id": system_id,
                    "error": str(e)
                })
                logger.error(f"시스템 배포 실패: {system_id} - {e}")
        
        rollout_plan["current_stage"] = stage
        rollout_plan["current_percentage"] = target_percentage
        
        # 롤아웃 계획 업데이트
        self._save_rollout_config(rollout_plan)
        
        # 오류가 발생하면 롤백
        failure_rate = len(rollout_plan["failed_systems"]) / len(systems_to_deploy) if systems_to_deploy else 0
        if failure_rate > 0.1:  # 10% 이상 실패
            logger.warning(f"롤아웃 실패율이 높아 롤백합니다: {failure_rate:.2%}")
            self._rollback(rollout_plan)
            return
        
        # 다음 단계로 진행 (자동 또는 수동)
        # 실제로는 일정 시간 대기 후 다음 단계 진행
    
    def _rollback(self, rollout_plan: Dict[str, Any]):
        """롤백 수행"""
        logger.info(f"롤백 시작: {rollout_plan['package_id']}")
        
        # 배포된 시스템에 롤백 명령 전송
        for system_id in rollout_plan["deployed_systems"]:
            try:
                # TODO: 실제 롤백 로직
                logger.info(f"시스템 롤백: {system_id}")
            except Exception as e:
                logger.error(f"롤백 실패: {system_id} - {e}")
        
        rollout_plan["status"] = "rolled_back"
        self._save_rollout_config(rollout_plan)
    
    def _save_rollout_config(self, config: Dict[str, Any]):
        """롤아웃 설정 저장"""
        with open(self.rollout_config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def get_rollout_status(self) -> Optional[Dict[str, Any]]:
        """롤아웃 상태 조회"""
        if not os.path.exists(self.rollout_config_file):
            return None
        
        with open(self.rollout_config_file, "r", encoding="utf-8") as f:
            return json.load(f)


class RemoteDiagnosticsService:
    """원격 진단 서비스"""
    
    def __init__(self, db: Session):
        """원격 진단 서비스 초기화"""
        self.db = db
    
    def collect_logs(
        self,
        system_id: str,
        log_types: List[str] = ["application", "error", "access"]
    ) -> Dict[str, Any]:
        """
        로그 수집
        
        Args:
            system_id: 시스템 ID
            log_types: 수집할 로그 타입
            
        Returns:
            수집된 로그
        """
        # TODO: 실제로는 원격 시스템에서 로그 수집
        # 현재는 로컬 로그만 반환
        
        logs = {}
        log_dir = settings.LOG_DIR
        
        for log_type in log_types:
            log_file = os.path.join(log_dir, f"{log_type}.log")
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    logs[log_type] = f.read()
        
        return {
            "system_id": system_id,
            "logs": logs,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    def get_system_metrics(self, system_id: str) -> Dict[str, Any]:
        """
        시스템 메트릭 수집
        
        Args:
            system_id: 시스템 ID
            
        Returns:
            시스템 메트릭
        """
        import psutil
        
        return {
            "system_id": system_id,
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count()
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "used": psutil.disk_usage("/").used,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent
            },
            "network": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            },
            "timestamp": datetime.utcnow().isoformat()
        }

