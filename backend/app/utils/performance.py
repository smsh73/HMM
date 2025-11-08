"""
성능 모니터링 및 최적화 유틸리티
"""
import psutil
import os
from typing import Dict, Any
from datetime import datetime


class PerformanceMonitor:
    """성능 모니터"""
    
    @staticmethod
    def get_system_resources() -> Dict[str, Any]:
        """시스템 리소스 사용량 조회"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        }
    
    @staticmethod
    def get_process_resources() -> Dict[str, Any]:
        """현재 프로세스 리소스 사용량 조회"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory": {
                "rss": memory_info.rss,  # 물리 메모리
                "vms": memory_info.vms,   # 가상 메모리
            },
            "num_threads": process.num_threads(),
            "open_files": len(process.open_files())
        }


class PerformanceOptimizer:
    """성능 최적화"""
    
    @staticmethod
    def optimize_for_low_spec(config: Dict[str, Any]) -> Dict[str, Any]:
        """저사양 환경 최적화 설정"""
        optimized = config.copy()
        
        # 배치 크기 감소
        if "BATCH_SIZE" in optimized:
            optimized["BATCH_SIZE"] = min(optimized["BATCH_SIZE"], 16)
        
        # 청크 크기 조정
        if "CHUNK_SIZE" in optimized:
            optimized["CHUNK_SIZE"] = min(optimized["CHUNK_SIZE"], 500)
        
        # 검색 결과 수 제한
        if "MAX_SEARCH_RESULTS" in optimized:
            optimized["MAX_SEARCH_RESULTS"] = min(optimized["MAX_SEARCH_RESULTS"], 5)
        
        return optimized

