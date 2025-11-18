# 배포 상태

## 완료된 작업 ✅

1. **Python 가상환경 생성**: `venv` 디렉토리 생성 완료
2. **백엔드 의존성 설치**: 대부분의 패키지 설치 완료
3. **데이터베이스 초기화**: 모든 테이블 생성 완료 (12개 테이블)
4. **프론트엔드 의존성 설치**: npm 패키지 설치 완료

## 알려진 문제 및 해결 방법

### 1. 관리자 계정 생성 오류

**문제**: bcrypt와 passlib의 호환성 문제로 관리자 계정 자동 생성 실패

**해결 방법 1: API를 통한 사용자 생성**
```bash
# 백엔드 서버가 실행된 후
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@hmm.com",
    "password": "admin123",
    "role": "admin"
  }'
```

**해결 방법 2: Python 스크립트로 직접 생성**
```python
# backend/scripts/create_admin.py
from app.core.database import SessionLocal
from app.models.database import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')

db = SessionLocal()
admin = User(
    username="admin",
    email="admin@hmm.com",
    password_hash=pwd_context.hash("admin123"),
    role="admin"
)
db.add(admin)
db.commit()
print("관리자 계정 생성 완료")
db.close()
```

### 2. PyTorch 설치 문제

**문제**: Python 3.13에서 PyTorch가 아직 완전히 지원되지 않을 수 있음

**해결 방법**: 
- CPU 기반 모델 사용 시 PyTorch 없이도 일부 기능 사용 가능
- 필요시 Python 3.11 또는 3.12로 가상환경 재생성

### 3. 일부 패키지 누락 가능성

필요한 패키지가 누락된 경우:
```bash
cd backend
source ../venv/bin/activate
pip install <패키지명> --no-cache-dir
```

## 서버 실행 방법

### 백엔드 서버 실행
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**확인**: 브라우저에서 `http://localhost:8000/docs` 접속하여 API 문서 확인

### 프론트엔드 실행
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**확인**: 브라우저에서 `http://localhost:3000` 접속

## 다음 단계

1. **백엔드 서버 실행 확인**
   - `http://localhost:8000/docs` 접속
   - API 문서가 표시되면 정상

2. **관리자 계정 생성**
   - 위의 해결 방법 중 하나 사용

3. **Sample Docs 처리** (선택사항)
   ```bash
   cd backend
   source ../venv/bin/activate
   python scripts/process_sample_docs.py
   ```

4. **프론트엔드 접속 및 로그인**
   - `http://localhost:3000` 접속
   - 생성한 관리자 계정으로 로그인

## 생성된 테이블 목록

다음 12개 테이블이 생성되었습니다:
- `users`: 사용자 정보
- `documents`: 문서 정보
- `document_chunks`: 문서 청크
- `document_versions`: 문서 버전
- `permissions`: 권한 정보
- `search_history`: 검색 기록
- `search_feedback`: 검색 피드백
- `llm_providers`: LLM 프로바이더 설정
- `local_models`: 로컬 모델 정보
- `rag_sync`: RAG 동기화 기록
- `chat_conversations`: 채팅 대화
- `chat_messages`: 채팅 메시지

## 로그 확인

### 백엔드 로그
```bash
tail -f backend/data/logs/app.log
tail -f backend/data/logs/error.log
```

### 서버 상태 확인
```bash
# 포트 8000 사용 중인 프로세스 확인
lsof -i :8000

# 포트 3000 사용 중인 프로세스 확인
lsof -i :3000
```

## 문제 해결

### 서버가 시작되지 않는 경우
1. 포트 충돌 확인
2. 의존성 설치 확인: `pip list`
3. 로그 파일 확인: `backend/data/logs/error.log`

### 프론트엔드가 시작되지 않는 경우
1. Node.js 버전 확인: `node --version` (16 이상)
2. `node_modules` 삭제 후 재설치:
   ```bash
   rm -rf node_modules package-lock.json
   npm install --legacy-peer-deps
   ```

## 참고 문서

- `QUICK_START.md`: 빠른 시작 가이드
- `DEPLOYMENT_GUIDE.md`: 상세 배포 가이드
- `DEPLOY_STEPS.md`: 단계별 명령어
- `IMPLEMENTATION_SUMMARY.md`: 구현 요약

