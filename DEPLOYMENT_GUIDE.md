# 맥북 배포 가이드

이 가이드는 맥북에서 GenAI 문서 검색/요약 시스템을 배포하는 방법을 설명합니다.

## 사전 요구사항

### 1. 시스템 요구사항
- macOS (Intel 또는 Apple Silicon)
- Python 3.9 이상
- Node.js 16 이상
- PostgreSQL 14 이상 (선택사항, SQLite도 가능)

### 2. 필수 소프트웨어 설치

#### Homebrew 설치 (없는 경우)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Python 설치 확인
```bash
python3 --version
# Python 3.9 이상이어야 함
```

#### Node.js 설치
```bash
brew install node
node --version
```

#### PostgreSQL 설치 (선택사항)
```bash
brew install postgresql@14
brew services start postgresql@14
```

## 1단계: 프로젝트 설정

### 1.1 프로젝트 디렉토리로 이동
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
```

### 1.2 Python 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 1.3 백엔드 의존성 설치
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.4 프론트엔드 의존성 설치
```bash
cd ../frontend
npm install
```

## 2단계: 데이터베이스 설정

### 2.1 SQLite 사용 (기본, 개발용)
SQLite는 별도 설정 없이 사용 가능합니다. 데이터베이스 파일은 `backend/data/documents.db`에 자동 생성됩니다.

### 2.2 PostgreSQL 사용 (프로덕션 권장)

#### 데이터베이스 생성
```bash
# PostgreSQL 접속
psql postgres

# 데이터베이스 및 사용자 생성
CREATE DATABASE hmm_db;
CREATE USER hmm_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE hmm_db TO hmm_user;
\q
```

#### 환경 변수 설정
`backend/.env` 파일 생성:
```bash
cd backend
cat > .env << EOF
DATABASE_URL=postgresql://hmm_user:your_password@localhost:5432/hmm_db
SECRET_KEY=your-secret-key-change-in-production
EOF
```

## 3단계: 데이터베이스 초기화

```bash
cd backend
python init_db.py
```

## 4단계: 모델 다운로드

### 4.1 임베딩 모델 (자동 다운로드)
임베딩 모델은 첫 실행 시 자동으로 다운로드됩니다.

### 4.2 LLM 모델 다운로드 (선택사항)

#### HuggingFace 모델 다운로드
웹 UI를 통해 다운로드하거나:
```bash
# Python 스크립트로 다운로드
python -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='microsoft/phi-2', local_dir='./data/huggingface_cache/models--microsoft--phi-2')
"
```

## 5단계: Sample Docs 처리

```bash
cd backend
python scripts/process_sample_docs.py
```

이 스크립트는 `sample docs` 폴더의 모든 문서를:
1. 파싱 (다국어 전처리)
2. 청킹 (언어 인식 스마트 청킹)
3. 벡터 임베딩 생성
4. Hybrid RAG 인덱싱

## 6단계: 애플리케이션 실행

### 6.1 백엔드 실행
```bash
cd backend
source ../venv/bin/activate  # 가상환경 활성화
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

백엔드는 `http://localhost:8000`에서 실행됩니다.
API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

### 6.2 프론트엔드 실행 (새 터미널)
```bash
cd frontend
npm start
```

프론트엔드는 `http://localhost:3000`에서 실행됩니다.

## 7단계: 초기 사용자 생성

### 7.1 관리자 사용자 생성
```bash
cd backend
python -c "
from app.core.database import SessionLocal, init_db
from app.models.database import User
from passlib.context import CryptContext

init_db()
db = SessionLocal()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

admin = User(
    username='admin',
    email='admin@example.com',
    password_hash=pwd_context.hash('admin123'),
    role='admin'
)
db.add(admin)
db.commit()
print('관리자 사용자 생성 완료: admin / admin123')
db.close()
"
```

### 7.2 웹 UI 로그인
1. 브라우저에서 `http://localhost:3000` 접속
2. 사용자명: `admin`, 비밀번호: `admin123`으로 로그인

## 주요 기능 사용법

### 모델 관리
1. **모델 다운로드**: HuggingFace Models 페이지에서 모델 검색 및 다운로드
2. **모델 서빙**: Model Management 페이지에서 모델 로드/언로드/교체
   - 한 번에 하나의 모델만 서빙 가능 (CPU 메모리 제한)
   - 모델 교체 시 자동으로 기존 모델 언로드

### 문서 관리
1. **문서 업로드**: Documents 페이지에서 문서 업로드
2. **자동 처리**: 업로드된 문서는 자동으로 파싱 및 인덱싱
3. **Sample Docs 처리**: `scripts/process_sample_docs.py` 실행

### 검색 기능
1. **하이브리드 검색**: 벡터 검색 + 키워드 검색 (BM25)
2. **RAG 답변 생성**: 검색 결과 기반 LLM 답변 생성
3. **피드백 제공**: 검색 결과에 대한 피드백 제공 (관련성, 평점 등)

## 문제 해결

### 포트 충돌
```bash
# 포트 8000 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

### 데이터베이스 연결 오류
- PostgreSQL 사용 시: 서비스가 실행 중인지 확인
  ```bash
  brew services list
  brew services start postgresql@14
  ```

### 모델 다운로드 실패
- 인터넷 연결 확인
- HuggingFace 토큰 설정 (선택사항)
  ```bash
  export HF_TOKEN=your_token
  ```

### 메모리 부족
- 모델은 한 번에 하나만 로드되도록 제한됨
- 더 작은 모델 사용 권장 (phi-2, gemma-2b 등)

## 프로덕션 배포

### 환경 변수 설정
`.env` 파일에 다음 설정 추가:
```bash
# 보안
SECRET_KEY=your-very-secure-secret-key-here

# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/hmm_db

# CORS (프로덕션 도메인)
CORS_ORIGINS=["https://yourdomain.com"]
```

### 백엔드 프로덕션 실행
```bash
# Gunicorn 사용 (권장)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 프론트엔드 빌드
```bash
cd frontend
npm run build
# build 폴더의 내용을 웹 서버에 배포
```

## 성능 최적화

### CPU 기반 최적화
- 모든 모델은 CPU에서 실행되도록 설정됨
- 배치 크기 조정: `settings.BATCH_SIZE` (기본값: 32)
- 청크 크기 조정: `settings.CHUNK_SIZE` (기본값: 1000)

### 벡터 DB 최적화
- Chroma는 자동으로 인덱싱 최적화
- HNSW 인덱스 사용 (빠른 유사도 검색)

## 모니터링

### 로그 확인
```bash
# 애플리케이션 로그
tail -f backend/data/logs/app.log

# 오류 로그
tail -f backend/data/logs/error.log
```

### 성능 모니터링
- Performance 페이지에서 시스템 리소스 모니터링
- API 응답 시간, 메모리 사용량 등 확인

## 추가 리소스

- API 문서: `http://localhost:8000/docs`
- 아키텍처 문서: `ARCHITECTURE.md`
- 설정 가이드: `SETUP_GUIDE.md`
- PostgreSQL 가이드: `POSTGRESQL_REPLICATION_GUIDE.md`

