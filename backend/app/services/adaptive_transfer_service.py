"""
적응적 전송 서비스
네트워크 상황에 따라 전송 방식을 조정
"""
from typing import Dict, Any, Optional
import asyncio
import httpx
import time
from app.core.logging import logger


class AdaptiveTransferService:
    """적응적 전송 서비스"""
    
    def __init__(self):
        """적응적 전송 서비스 초기화"""
        self.network_stats = {
            "bandwidth": 0.0,  # Mbps
            "latency": 0.0,  # ms
            "packet_loss": 0.0  # %
        }
    
    async def measure_network(self, target_url: str) -> Dict[str, float]:
        """
        네트워크 상태 측정
        
        Args:
            target_url: 대상 URL
            
        Returns:
            네트워크 통계
        """
        try:
            # 지연 시간 측정
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(f"{target_url}/health")
            latency = (time.time() - start_time) * 1000  # ms
            
            # 대역폭 측정 (간단한 방법)
            # 실제로는 더 정교한 측정 필요
            test_size = 1024 * 1024  # 1MB
            start_time = time.time()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{target_url}/health")
                # 실제로는 더 큰 데이터로 측정
            transfer_time = time.time() - start_time
            bandwidth = (test_size * 8) / (transfer_time * 1000000) if transfer_time > 0 else 0  # Mbps
            
            self.network_stats = {
                "bandwidth": bandwidth,
                "latency": latency,
                "packet_loss": 0.0  # 실제로는 패킷 손실 측정 필요
            }
            
            logger.info(
                f"네트워크 상태: 대역폭={bandwidth:.2f}Mbps, "
                f"지연시간={latency:.2f}ms"
            )
            
            return self.network_stats
        
        except Exception as e:
            logger.warning(f"네트워크 측정 실패: {e}")
            return self.network_stats
    
    def get_compression_level(self) -> int:
        """
        네트워크 상황에 따른 압축 레벨 결정
        
        Returns:
            압축 레벨 (1-9, 높을수록 압축률 높음)
        """
        bandwidth = self.network_stats["bandwidth"]
        
        if bandwidth < 1.0:  # 매우 낮은 대역폭
            return 9  # 최대 압축
        elif bandwidth < 5.0:  # 낮은 대역폭
            return 7
        elif bandwidth < 10.0:  # 중간 대역폭
            return 5
        else:  # 높은 대역폭
            return 3  # 낮은 압축 (속도 우선)
    
    def get_chunk_size(self) -> int:
        """
        네트워크 상황에 따른 청크 크기 결정
        
        Returns:
            청크 크기 (bytes)
        """
        bandwidth = self.network_stats["bandwidth"]
        latency = self.network_stats["latency"]
        
        # 낮은 대역폭이거나 높은 지연시간이면 작은 청크
        if bandwidth < 1.0 or latency > 1000:
            return 64 * 1024  # 64KB
        elif bandwidth < 5.0 or latency > 500:
            return 256 * 1024  # 256KB
        else:
            return 1024 * 1024  # 1MB
    
    def get_tcp_window_size(self) -> int:
        """
        TCP 윈도우 크기 조정
        
        Returns:
            TCP 윈도우 크기 (bytes)
        """
        bandwidth = self.network_stats["bandwidth"]
        latency = self.network_stats["latency"]
        
        # BDP (Bandwidth-Delay Product) 계산
        bdp = (bandwidth * 1000000 / 8) * (latency / 1000)  # bytes
        
        # TCP 윈도우 크기는 BDP의 2배 정도가 적절
        window_size = int(bdp * 2)
        
        # 최소/최대 제한
        window_size = max(65536, min(window_size, 16777216))  # 64KB ~ 16MB
        
        return window_size
    
    async def transfer_with_adaptation(
        self,
        file_path: str,
        target_url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        적응적 전송 수행
        
        Args:
            file_path: 전송할 파일 경로
            target_url: 대상 URL
            headers: HTTP 헤더
            
        Returns:
            전송 결과
        """
        # 네트워크 상태 측정
        await self.measure_network(target_url)
        
        # 전송 파라미터 결정
        compression_level = self.get_compression_level()
        chunk_size = self.get_chunk_size()
        
        logger.info(
            f"적응적 전송 시작: 압축레벨={compression_level}, "
            f"청크크기={chunk_size/1024:.0f}KB"
        )
        
        # TODO: 실제 청크 단위 전송 구현
        # 현재는 기본 전송 사용
        
        try:
            async with httpx.AsyncClient(
                http2=True,
                timeout=300.0,
                limits=httpx.Limits(max_keepalive_connections=5)
            ) as client:
                with open(file_path, "rb") as f:
                    files = {"file": (os.path.basename(file_path), f, "application/zip")}
                    response = await client.post(
                        target_url,
                        files=files,
                        headers=headers or {}
                    )
                    
                    if response.status_code == 200:
                        return {
                            "status": "success",
                            "message": "전송 완료",
                            "network_stats": self.network_stats
                        }
                    else:
                        raise Exception(f"전송 실패: {response.status_code}")
        
        except Exception as e:
            logger.error(f"적응적 전송 실패: {e}")
            raise

