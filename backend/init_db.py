"""
데이터베이스 초기화 스크립트
"""
import sys
from app.core.database import engine, Base, SessionLocal
# 모든 모델을 import하여 테이블 생성 보장
from app.models.database import (
    User, Document, DocumentChunk, Permission, SearchHistory,
    SearchFeedback, LLMProvider, LocalModel, RAGSync,
    DocumentVersion, ChatConversation, ChatMessage
)
from app.services.auth_service import AuthService
from app.core.config import settings


def init_database():
    """데이터베이스 테이블 생성"""
    print("="*60)
    print("데이터베이스 테이블 생성 중...")
    print("="*60)
    print(f"데이터베이스 URL: {settings.DATABASE_URL}")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ 데이터베이스 테이블 생성 완료")
        
        # 생성된 테이블 확인
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"생성된 테이블 수: {len(tables)}")
        for table in sorted(tables):
            print(f"  - {table}")
    except Exception as e:
        print(f"✗ 테이블 생성 오류: {e}")
        raise


def create_default_admin():
    """기본 관리자 계정 생성"""
    print("\n" + "="*60)
    print("기본 관리자 계정 생성 중...")
    print("="*60)
    
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # 관리자 계정 확인
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("✓ 기본 관리자 계정이 이미 존재합니다.")
            print(f"  사용자명: {admin.username}")
            print(f"  이메일: {admin.email}")
            return admin
        
        # 관리자 계정 생성
        admin = auth_service.create_user(
            username="admin",
            email="admin@hmm.com",
            password="admin123",  # 프로덕션에서는 반드시 변경
            role="admin"
        )
        print("✓ 기본 관리자 계정 생성 완료")
        print(f"  사용자명: admin")
        print(f"  비밀번호: admin123")
        print("  ⚠️  프로덕션 환경에서는 반드시 비밀번호를 변경하세요!")
        return admin
    except Exception as e:
        print(f"✗ 관리자 계정 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("데이터베이스 초기화 스크립트")
    print("="*60)
    
    try:
        init_database()
        create_default_admin()
        
        print("\n" + "="*60)
        print("데이터베이스 초기화 완료!")
        print("="*60)
    except Exception as e:
        print(f"\n✗ 초기화 실패: {e}")
        sys.exit(1)

