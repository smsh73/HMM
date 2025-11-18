# 로그인 문제 해결

## 문제

admin/admin123으로 로그인이 안 되는 문제가 있었습니다.

## 원인

비밀번호 해싱 방식 불일치:
- `auth_service.py`: bcrypt 사용
- `create_admin.py`: pbkdf2_sha256 사용

## 해결

`auth_service.py`의 비밀번호 해싱 방식을 `pbkdf2_sha256`으로 변경했습니다.

## 로그인 테스트

### 방법 1: API 테스트
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 방법 2: Python 스크립트
```bash
cd backend
source ../venv/bin/activate
python -c "
from app.services.auth_service import AuthService
from app.core.database import SessionLocal
db = SessionLocal()
auth = AuthService(db)
user = auth.authenticate_user('admin', 'admin123')
print('Login:', 'SUCCESS' if user else 'FAILED')
db.close()
"
```

### 방법 3: 웹 브라우저
1. http://localhost:3000 접속
2. 사용자명: `admin`
3. 비밀번호: `admin123`
4. 로그인 버튼 클릭

## 관리자 계정 정보

- **사용자명**: admin
- **비밀번호**: admin123
- **이메일**: admin@hmm.com
- **역할**: admin

## 문제가 계속되는 경우

### 1. 관리자 계정 재생성
```bash
cd backend
source ../venv/bin/activate
python scripts/create_admin.py
```

### 2. 비밀번호 재설정
```bash
cd backend
source ../venv/bin/activate
python -c "
from app.core.database import SessionLocal
from app.models.database import User
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')
db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    admin.password_hash = pwd_context.hash('admin123')
    db.commit()
    print('비밀번호 재설정 완료')
db.close()
"
```

### 3. 새 관리자 계정 생성
```bash
cd backend
source ../venv/bin/activate
python -c "
from app.core.database import SessionLocal
from app.models.database import User
from app.services.auth_service import AuthService
db = SessionLocal()
auth = AuthService(db)
try:
    user = auth.create_user('admin2', 'admin2@hmm.com', 'admin123', 'admin')
    print('새 관리자 계정 생성:', user.username)
except Exception as e:
    print('오류:', e)
db.close()
"
```

## 백엔드 서버 재시작

변경사항을 적용하려면 백엔드 서버를 재시작하세요:

```bash
# 현재 실행 중인 서버 중지 (Ctrl + C)
# 그 다음 다시 실행
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 확인

로그인이 성공하면:
- JWT 토큰이 반환됩니다
- 웹 UI에서 대시보드로 이동합니다
- API 요청 시 토큰을 사용할 수 있습니다

