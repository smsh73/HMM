"""
PostgreSQL 데이터베이스 초기화 스크립트
PostgreSQL 연결을 테스트하고 테이블을 생성합니다.
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from app.core.database import Base, SessionLocal
from app.models.database import (
    User, Document, DocumentChunk, Permission, SearchHistory,
    SearchFeedback, LLMProvider, LocalModel, RAGSync,
    DocumentVersion, ChatConversation, ChatMessage
)
from app.services.auth_service import AuthService
from app.core.config import settings


def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            if "postgresql" in settings.DATABASE_URL.lower():
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✓ PostgreSQL 연결 성공")
                print(f"  버전: {version.split(',')[0]}")
            else:
                print(f"✓ SQLite 연결 성공")
        return True
    except OperationalError as e:
        print(f"✗ 데이터베이스 연결 실패: {e}")
        print(f"  연결 문자열: {settings.DATABASE_URL}")
        return False
    except Exception as e:
        print(f"✗ 연결 테스트 오류: {e}")
        return False


def init_database():
    """데이터베이스 테이블 생성"""
    print("\n" + "="*60)
    print("데이터베이스 테이블 생성 중...")
    print("="*60)
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        
        # 생성된 테이블 목록 확인
        with engine.connect() as conn:
            if "postgresql" in settings.DATABASE_URL.lower():
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
            else:
                result = conn.execute(text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name
                """))
            
            tables = [row[0] for row in result]
            print(f"\n✓ 테이블 생성 완료 ({len(tables)}개)")
            print("생성된 테이블:")
            for table in tables:
                print(f"  - {table}")
        
        return True
    except Exception as e:
        print(f"✗ 테이블 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


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


def main():
    """메인 함수"""
    print("="*60)
    print("데이터베이스 초기화 스크립트")
    print("="*60)
    print(f"\n데이터베이스 URL: {settings.DATABASE_URL}")
    
    # 1. 연결 테스트
    if not test_connection():
        print("\n✗ 데이터베이스 연결에 실패했습니다.")
        print("\n해결 방법:")
        if "postgresql" in settings.DATABASE_URL.lower():
            print("1. PostgreSQL이 실행 중인지 확인: brew services list")
            print("2. 데이터베이스와 사용자가 생성되었는지 확인")
            print("3. .env 파일의 DATABASE_URL 설정 확인")
        else:
            print("1. data 디렉토리가 존재하는지 확인")
        sys.exit(1)
    
    # 2. 테이블 생성
    if not init_database():
        print("\n✗ 테이블 생성에 실패했습니다.")
        sys.exit(1)
    
    # 3. 관리자 계정 생성
    admin = create_default_admin()
    
    # 완료 메시지
    print("\n" + "="*60)
    print("데이터베이스 초기화 완료!")
    print("="*60)
    print("\n다음 단계:")
    print("1. 백엔드 서버 실행: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("2. 프론트엔드 실행: npm start (frontend 디렉토리에서)")
    print("3. 웹 브라우저에서 http://localhost:3000 접속")
    print("4. 관리자 계정으로 로그인: admin / admin123")
    print("\n")


if __name__ == "__main__":
    main()

