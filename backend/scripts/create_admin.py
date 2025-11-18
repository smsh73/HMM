"""
관리자 계정 생성 스크립트 (bcrypt 문제 해결용)
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.database import User
from passlib.context import CryptContext

# pbkdf2_sha256 사용 (bcrypt 대신)
pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')

def create_admin():
    """관리자 계정 생성"""
    db = SessionLocal()
    try:
        # 기존 관리자 확인
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("✓ 관리자 계정이 이미 존재합니다.")
            print(f"  사용자명: {admin.username}")
            print(f"  이메일: {admin.email}")
            return admin
        
        # 관리자 계정 생성
        admin = User(
            username="admin",
            email="admin@hmm.com",
            password_hash=pwd_context.hash("admin123"),
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✓ 관리자 계정 생성 완료")
        print(f"  사용자명: admin")
        print(f"  비밀번호: admin123")
        print("  ⚠️  프로덕션 환경에서는 반드시 비밀번호를 변경하세요!")
        return admin
    except Exception as e:
        print(f"✗ 관리자 계정 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("관리자 계정 생성 스크립트")
    print("="*60)
    create_admin()

