"""
오류 정정 서비스
Reed-Solomon 오류 정정 코드, 단편적 전송 및 재조립
"""
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from app.core.logging import logger


class ReedSolomonErrorCorrection:
    """
    Reed-Solomon 오류 정정 코드
    패킷 손실에 대비한 오류 정정
    """
    
    def __init__(self, data_shards: int = 10, parity_shards: int = 3):
        """
        Reed-Solomon 초기화
        
        Args:
            data_shards: 데이터 샤드 개수
            parity_shards: 패리티 샤드 개수 (오류 정정용)
        """
        self.data_shards = data_shards
        self.parity_shards = parity_shards
        self.total_shards = data_shards + parity_shards
    
    def encode(self, data: bytes) -> List[bytes]:
        """
        데이터 인코딩 (오류 정정 코드 추가)
        
        Args:
            data: 원본 데이터
            
        Returns:
            인코딩된 샤드 리스트
        """
        try:
            import reedsolo
            
            # 데이터를 샤드로 분할
            shard_size = len(data) // self.data_shards
            if len(data) % self.data_shards != 0:
                shard_size += 1
            
            # 데이터 패딩
            padded_data = data + b'\x00' * (shard_size * self.data_shards - len(data))
            
            # 샤드 분할
            data_shards = [
                padded_data[i * shard_size:(i + 1) * shard_size]
                for i in range(self.data_shards)
            ]
            
            # Reed-Solomon 인코딩
            rs = reedsolo.RSCodec(self.parity_shards)
            encoded_shards = rs.encode(data_shards)
            
            logger.info(
                f"Reed-Solomon 인코딩: {len(data)} bytes -> "
                f"{self.total_shards}개 샤드"
            )
            
            return encoded_shards
        
        except ImportError:
            logger.warning("reedsolo가 설치되지 않아 오류 정정을 건너뜁니다.")
            # 폴백: 단순 분할
            shard_size = len(data) // self.data_shards
            if len(data) % self.data_shards != 0:
                shard_size += 1
            padded_data = data + b'\x00' * (shard_size * self.data_shards - len(data))
            return [
                padded_data[i * shard_size:(i + 1) * shard_size]
                for i in range(self.total_shards)
            ]
    
    def decode(self, shards: List[Optional[bytes]], shard_indices: List[int]) -> bytes:
        """
        데이터 디코딩 (오류 정정)
        
        Args:
            shards: 수신된 샤드 리스트 (None은 손실된 샤드)
            shard_indices: 샤드 인덱스 리스트
            
        Returns:
            복원된 데이터
        """
        try:
            import reedsolo
            
            # 손실된 샤드 개수 확인
            lost_count = sum(1 for s in shards if s is None)
            
            if lost_count > self.parity_shards:
                raise ValueError(
                    f"손실된 샤드가 너무 많습니다: {lost_count} > {self.parity_shards}"
                )
            
            # Reed-Solomon 디코딩
            rs = reedsolo.RSCodec(self.parity_shards)
            decoded_shards = rs.decode(shards)
            
            # 데이터 재조립
            data = b''.join(decoded_shards[:self.data_shards])
            
            # 패딩 제거
            data = data.rstrip(b'\x00')
            
            logger.info(f"Reed-Solomon 디코딩: {lost_count}개 샤드 손실 복구")
            
            return data
        
        except ImportError:
            logger.warning("reedsolo가 설치되지 않아 오류 정정을 건너뜁니다.")
            # 폴백: 단순 재조립
            valid_shards = [s for s in shards if s is not None]
            return b''.join(valid_shards)


class FragmentedTransfer:
    """
    단편적 전송 및 재조립
    대용량 파일을 작은 조각으로 분할하여 전송
    """
    
    def __init__(self, fragment_size: int = 1024 * 1024):  # 1MB
        """
        단편적 전송 초기화
        
        Args:
            fragment_size: 조각 크기 (bytes)
        """
        self.fragment_size = fragment_size
    
    def fragment(self, data: bytes) -> List[Tuple[int, bytes]]:
        """
        데이터를 조각으로 분할
        
        Args:
            data: 원본 데이터
            
        Returns:
            (인덱스, 조각) 튜플 리스트
        """
        fragments = []
        total_fragments = (len(data) + self.fragment_size - 1) // self.fragment_size
        
        for i in range(total_fragments):
            start = i * self.fragment_size
            end = min(start + self.fragment_size, len(data))
            fragment = data[start:end]
            fragments.append((i, fragment))
        
        logger.info(f"데이터 분할: {len(data)} bytes -> {len(fragments)}개 조각")
        
        return fragments
    
    def reassemble(self, fragments: List[Tuple[int, bytes]]) -> bytes:
        """
        조각을 재조립
        
        Args:
            fragments: (인덱스, 조각) 튜플 리스트
            
        Returns:
            재조립된 데이터
        """
        # 인덱스 순으로 정렬
        fragments.sort(key=lambda x: x[0])
        
        # 재조립
        data = b''.join(fragment for _, fragment in fragments)
        
        logger.info(f"데이터 재조립: {len(fragments)}개 조각 -> {len(data)} bytes")
        
        return data
    
    def create_manifest(self, fragments: List[Tuple[int, bytes]]) -> Dict[str, Any]:
        """
        전송 매니페스트 생성
        
        Args:
            fragments: 조각 리스트
            
        Returns:
            매니페스트 정보
        """
        import hashlib
        
        fragment_hashes = []
        for idx, fragment in fragments:
            hash_value = hashlib.sha256(fragment).hexdigest()
            fragment_hashes.append({
                "index": idx,
                "hash": hash_value,
                "size": len(fragment)
            })
        
        return {
            "total_fragments": len(fragments),
            "fragment_size": self.fragment_size,
            "fragments": fragment_hashes
        }
    
    def verify_fragments(
        self,
        fragments: List[Tuple[int, bytes]],
        manifest: Dict[str, Any]
    ) -> bool:
        """
        조각 무결성 검증
        
        Args:
            fragments: 조각 리스트
            manifest: 매니페스트 정보
            
        Returns:
            검증 성공 여부
        """
        import hashlib
        
        if len(fragments) != manifest["total_fragments"]:
            return False
        
        for idx, fragment in fragments:
            expected_hash = next(
                (f["hash"] for f in manifest["fragments"] if f["index"] == idx),
                None
            )
            
            if expected_hash is None:
                return False
            
            actual_hash = hashlib.sha256(fragment).hexdigest()
            if actual_hash != expected_hash:
                return False
        
        return True

