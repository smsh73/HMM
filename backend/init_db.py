"""
데이터베이스 초기화 스크립트
"""
from app.core.database import engine, Base
from app.models.database import User, Document, DocumentChunk, Permission, SearchHistory
from app.services.auth_service import AuthService
from sqlalchemy.orm import Session
from app.core.database import SessionLocal


def init_database():
    """데이터베이스 테이블 생성"""
    print("데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블 생성 완료")


def create_default_admin():
    """기본 관리자 계정 생성"""
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # 관리자 계정 확인
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("기본 관리자 계정이 이미 존재합니다.")
            return
        
        # 관리자 계정 생성
        admin = auth_service.create_user(
            username="admin",
            email="admin@hmm.com",
            password="admin123",  # 프로덕션에서는 반드시 변경
            role="admin"
        )
        print(f"기본 관리자 계정 생성 완료: admin / admin123")
        print("⚠️  프로덕션 환경에서는 반드시 비밀번호를 변경하세요!")
    except Exception as e:
        print(f"관리자 계정 생성 오류: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    create_default_admin()

