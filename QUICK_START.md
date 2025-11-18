# 빠른 시작 가이드

이 가이드는 맥북에서 GenAI 문서 검색/요약 시스템을 빠르게 시작하는 방법을 설명합니다.

## 사전 준비 (5분)

### 1. Python 및 Node.js 확인
```bash
python3 --version  # Python 3.9 이상 필요
node --version     # Node.js 16 이상 필요
```

### 2. 프로젝트 디렉토리로 이동
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
```

## 빠른 설치 (10분)

### 1. Python 가상환경 설정
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 2. 백엔드 의존성 설치
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

**참고**: 일부 패키지(특히 PyTorch)는 다운로드에 시간이 걸릴 수 있습니다.

### 3. 프론트엔드 의존성 설치
```bash
cd ../frontend
npm install
```

## 데이터베이스 초기화 (2분)

```bash
cd ../backend
python init_db.py
```

이 명령은:
- 모든 데이터베이스 테이블 생성
- 기본 관리자 계정 생성 (admin / admin123)

## Sample Docs 처리 (5분)

```bash
python scripts/process_sample_docs.py
```

이 스크립트는 `sample docs` 폴더의 모든 문서를:
- 다국어 전처리
- 청킹
- 벡터 임베딩 생성
- Hybrid RAG 인덱싱

## 애플리케이션 실행 (1분)

### 터미널 1: 백엔드 실행
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

백엔드가 `http://localhost:8000`에서 실행됩니다.

### 터미널 2: 프론트엔드 실행
```bash
cd frontend
npm start
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

## 첫 사용 (2분)

1. 브라우저에서 `http://localhost:3000` 접속
2. 로그인:
   - 사용자명: `admin`
   - 비밀번호: `admin123`
3. 주요 기능 사용:
   - **Documents**: 문서 관리
   - **Search**: 하이브리드 검색
   - **Chat**: AI 챗봇
   - **HuggingFace Models**: 모델 다운로드
   - **Model Management**: 모델 서빙 관리

## 다음 단계

### 모델 다운로드 및 서빙
1. HuggingFace Models 페이지에서 모델 검색
2. 원하는 모델 다운로드 (예: `microsoft/phi-2`)
3. Model Management 페이지에서 모델 로드

### 문서 업로드
1. Documents 페이지에서 문서 업로드
2. 자동으로 파싱 및 인덱싱됨
3. 검색 가능해짐

### 검색 사용
1. Search 페이지에서 검색
2. 하이브리드 검색 결과 확인
3. 피드백 제공 (관련성, 평점)

## 문제 해결

### 포트 충돌
```bash
# 포트 8000 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

### 의존성 설치 오류
```bash
# pip 업그레이드
pip install --upgrade pip setuptools wheel

# 개별 패키지 설치
pip install fastapi uvicorn sqlalchemy
```

### 모델 다운로드 실패
- 인터넷 연결 확인
- HuggingFace 토큰 설정 (선택사항):
  ```bash
  export HF_TOKEN=your_token
  ```

## 자세한 가이드

- **배포 가이드**: `DEPLOYMENT_GUIDE.md`
- **PostgreSQL 설정**: `backend/scripts/setup_postgresql.md`
- **구현 요약**: `IMPLEMENTATION_SUMMARY.md`
- **아키텍처**: `ARCHITECTURE.md`

## 지원

문제가 발생하면:
1. 로그 확인: `backend/data/logs/app.log`
2. 오류 로그: `backend/data/logs/error.log`
3. API 문서: `http://localhost:8000/docs`

