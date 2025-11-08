"""
권한 관리 서비스
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.database import Permission, Document, User


class PermissionService:
    """권한 관리 서비스"""
    
    def __init__(self, db: Session):
        """권한 서비스 초기화"""
        self.db = db
    
    def set_permission(
        self,
        document_id: str,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        permission_type: str = "read"
    ) -> Permission:
        """권한 설정"""
        if not user_id and not role:
            raise ValueError("user_id 또는 role 중 하나는 필수입니다.")
        
        # 기존 권한 확인
        existing = self.db.query(Permission).filter(
            Permission.document_id == document_id,
            Permission.user_id == user_id,
            Permission.role == role
        ).first()
        
        if existing:
            existing.permission_type = permission_type
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # 새 권한 생성
        permission = Permission(
            document_id=document_id,
            user_id=user_id,
            role=role,
            permission_type=permission_type
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def check_permission(
        self,
        user_id: str,
        document_id: str,
        permission_type: str = "read"
    ) -> bool:
        """권한 확인"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # 관리자는 모든 권한
        if user.role == "admin":
            return True
        
        # 문서 소유자 확인
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if document and document.created_by == user_id:
            return True
        
        # 사용자별 권한 확인
        user_permission = self.db.query(Permission).filter(
            Permission.document_id == document_id,
            Permission.user_id == user_id,
            Permission.permission_type == permission_type
        ).first()
        
        if user_permission:
            return True
        
        # 역할별 권한 확인
        role_permission = self.db.query(Permission).filter(
            Permission.document_id == document_id,
            Permission.role == user.role,
            Permission.permission_type == permission_type
        ).first()
        
        return role_permission is not None
    
    def get_document_permissions(self, document_id: str) -> List[Permission]:
        """문서의 모든 권한 조회"""
        return self.db.query(Permission).filter(
            Permission.document_id == document_id
        ).all()
    
    def delete_permission(self, permission_id: str) -> bool:
        """권한 삭제"""
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            return False
        
        self.db.delete(permission)
        self.db.commit()
        
        return True

