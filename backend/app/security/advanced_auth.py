"""
고급 보안 및 권한 관리
RBAC + ABAC 하이브리드 모델
"""
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum

from app.models.database import User, Document, DocumentChunk
from app.core.logging import logger


class PermissionLevel(Enum):
    """권한 레벨"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class SecurityLevel(Enum):
    """보안 등급"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


class AdvancedAuthService:
    """
    고급 인증 및 권한 관리 서비스
    RBAC (Role-Based Access Control) + ABAC (Attribute-Based Access Control)
    """
    
    def __init__(self, db: Session):
        """고급 인증 서비스 초기화"""
        self.db = db
    
    def check_document_access(
        self,
        user: User,
        document_id: str,
        action: str = "read",
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        문서 접근 권한 확인 (RBAC + ABAC)
        
        Args:
            user: 사용자
            document_id: 문서 ID
            action: 수행할 작업 (read, write, delete)
            context: 컨텍스트 정보 (위치, 시간, IP 등)
            
        Returns:
            접근 허용 여부
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # RBAC: 역할 기반 권한 확인
        role_permission = self._check_role_permission(user.role, action)
        
        # ABAC: 속성 기반 권한 확인
        attribute_permission = self._check_attribute_permission(
            user, document, action, context or {}
        )
        
        # 둘 다 통과해야 접근 허용
        return role_permission and attribute_permission
    
    def _check_role_permission(self, role: str, action: str) -> bool:
        """RBAC: 역할 기반 권한 확인"""
        role_permissions = {
            "admin": ["read", "write", "delete", "admin"],
            "user": ["read"],
            "viewer": ["read"]
        }
        
        allowed_actions = role_permissions.get(role, [])
        return action in allowed_actions
    
    def _check_attribute_permission(
        self,
        user: User,
        document: Document,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """ABAC: 속성 기반 권한 확인"""
        # 문서 보안 등급 확인
        doc_security_level = document.doc_metadata.get("security_level", "internal")
        
        # 사용자 보안 클리어런스 확인
        user_clearance = getattr(user, "security_clearance", "internal")
        
        # 보안 등급 매핑
        security_levels = {
            "public": 0,
            "internal": 1,
            "confidential": 2,
            "secret": 3
        }
        
        doc_level = security_levels.get(doc_security_level, 1)
        user_level = security_levels.get(user_clearance, 1)
        
        # 사용자 클리어런스가 문서 보안 등급 이상이어야 함
        if user_level < doc_level:
            return False
        
        # 시간 기반 제한 (예: 특정 시간대만 접근 가능)
        current_hour = datetime.utcnow().hour
        if "allowed_hours" in context:
            allowed_hours = context["allowed_hours"]
            if current_hour not in allowed_hours:
                return False
        
        # 위치 기반 제한 (예: 특정 IP에서만 접근 가능)
        if "allowed_ips" in context:
            client_ip = context.get("client_ip")
            if client_ip not in context["allowed_ips"]:
                return False
        
        return True
    
    def check_chunk_access(
        self,
        user: User,
        chunk_id: str,
        action: str = "read"
    ) -> bool:
        """
        청크 접근 권한 확인 (문단 단위 권한)
        
        Args:
            user: 사용자
            chunk_id: 청크 ID
            action: 수행할 작업
            
        Returns:
            접근 허용 여부
        """
        chunk = self.db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            return False
        
        # 문서 접근 권한 먼저 확인
        if not self.check_document_access(user, chunk.document_id, action):
            return False
        
        # 청크별 권한 확인 (메타데이터에 권한 정보가 있는 경우)
        chunk_permissions = chunk.chunk_metadata.get("permissions", {})
        if chunk_permissions:
            user_roles = [user.role]
            if hasattr(user, "additional_roles"):
                user_roles.extend(user.additional_roles)
            
            allowed_roles = chunk_permissions.get("allowed_roles", [])
            if not any(role in allowed_roles for role in user_roles):
                return False
        
        return True
    
    def mask_sensitive_content(
        self,
        content: str,
        user: User,
        document: Document
    ) -> str:
        """
        민감한 내용 마스킹
        
        Args:
            content: 원본 내용
            user: 사용자
            document: 문서
            
        Returns:
            마스킹된 내용
        """
        # 보안 등급 확인
        doc_security_level = document.doc_metadata.get("security_level", "internal")
        user_clearance = getattr(user, "security_clearance", "internal")
        
        security_levels = {
            "public": 0,
            "internal": 1,
            "confidential": 2,
            "secret": 3
        }
        
        doc_level = security_levels.get(doc_security_level, 1)
        user_level = security_levels.get(user_clearance, 1)
        
        # 사용자 클리어런스가 낮으면 마스킹
        if user_level < doc_level:
            # 내용을 마스킹 (예: 일부만 표시)
            if len(content) > 50:
                return content[:20] + "..." + "[마스킹됨]" + "..." + content[-20:]
            else:
                return "[마스킹됨]"
        
        return content
    
    def log_access_attempt(
        self,
        user: User,
        resource_type: str,
        resource_id: str,
        action: str,
        allowed: bool,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        접근 시도 감사 로그 기록
        
        Args:
            user: 사용자
            resource_type: 리소스 타입 (document, chunk)
            resource_id: 리소스 ID
            action: 수행한 작업
            allowed: 허용 여부
            context: 컨텍스트 정보
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user.id,
            "user_role": user.role,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "allowed": allowed,
            "context": context or {}
        }
        
        # TODO: 감사 로그를 데이터베이스나 파일에 저장
        logger.info(f"접근 시도: {user.id} - {resource_type}/{resource_id} - {action} - {'허용' if allowed else '거부'}")


class EncryptionService:
    """암호화 서비스 (AES-256)"""
    
    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """
        데이터 암호화 (AES-256)
        
        Args:
            data: 암호화할 데이터
            key: 암호화 키 (32 bytes for AES-256)
            
        Returns:
            암호화된 데이터
        """
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        import base64
        import os
        
        # 키에서 Fernet 키 생성
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=os.urandom(16),
            iterations=100000,
            backend=default_backend()
        )
        key_material = kdf.derive(key)
        fernet_key = base64.urlsafe_b64encode(key_material)
        
        f = Fernet(fernet_key)
        encrypted = f.encrypt(data)
        
        return encrypted
    
    @staticmethod
    def decrypt(encrypted_data: bytes, key: bytes) -> bytes:
        """
        데이터 복호화
        
        Args:
            encrypted_data: 암호화된 데이터
            key: 복호화 키
            
        Returns:
            복호화된 데이터
        """
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        import base64
        import os
        
        # 키에서 Fernet 키 생성 (encrypt와 동일한 방식)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=os.urandom(16),  # 실제로는 저장된 salt 사용 필요
            iterations=100000,
            backend=default_backend()
        )
        key_material = kdf.derive(key)
        fernet_key = base64.urlsafe_b64encode(key_material)
        
        f = Fernet(fernet_key)
        decrypted = f.decrypt(encrypted_data)
        
        return decrypted

