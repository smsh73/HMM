"""
인증 서비스
"""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.database import User
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """인증 서비스"""
    
    def __init__(self, db: Session):
        """인증 서비스 초기화"""
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """비밀번호 해시 생성"""
        return pwd_context.hash(password)
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user"
    ) -> User:
        """사용자 생성"""
        # 중복 확인
        if self.db.query(User).filter(User.username == username).first():
            raise ValueError("이미 존재하는 사용자명입니다.")
        if self.db.query(User).filter(User.email == email).first():
            raise ValueError("이미 존재하는 이메일입니다.")
        
        user = User(
            username=username,
            email=email,
            password_hash=self.get_password_hash(password),
            role=role
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """사용자 인증"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
    
    def create_access_token(self, user_id: str) -> str:
        """JWT 토큰 생성"""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": user_id, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            return user_id
        except JWTError:
            return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """사용자 조회"""
        return self.db.query(User).filter(User.id == user_id).first()

