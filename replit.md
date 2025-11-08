# HMM GenAI 문서 검색/요약 시스템

## 프로젝트 개요
HMM㈜의 선박 환경을 위한 온/오프라인 문서 검색 및 요약 시스템입니다. AI/ML 기반의 RAG (Retrieval-Augmented Generation) 시스템으로 문서 업로드, 파싱, 검색 및 요약 기능을 제공합니다.

## 기술 스택
- **Backend**: FastAPI (Python 3.11), SQLAlchemy, SQLite
- **Frontend**: React 18 + TypeScript, Material-UI, React Query
- **AI/ML**: LangChain, Sentence Transformers, FAISS, Ollama (선택사항)

## 프로젝트 구조
```
/
├── backend/           # FastAPI 백엔드 서버
│   ├── app/
│   │   ├── api/      # API 라우터
│   │   ├── ai/       # AI/ML 모듈 (임베딩, RAG, 벡터스토어)
│   │   ├── core/     # 핵심 설정 및 데이터베이스
│   │   ├── models/   # 데이터베이스 모델
│   │   ├── parsers/  # 문서 파서 (PDF, Word, Excel)
│   │   └── services/ # 비즈니스 로직
│   ├── data/         # 데이터 디렉토리 (SQLite DB, 업로드, 로그)
│   └── .env          # 환경 변수 설정
├── frontend/          # React + TypeScript 프론트엔드
│   ├── src/          # 소스 코드
│   └── build/        # 프로덕션 빌드 (백엔드가 제공)
└── docs/              # 프로젝트 문서
```

## 현재 상태 (Replit 환경)

### ✅ 설정 완료
- Python 3.11 및 Node.js 20 설치
- 백엔드/프론트엔드 의존성 설치
- SQLite 데이터베이스 초기화
- 기본 관리자 계정 생성 (username: admin, password: admin123)
- **통합 서버 설정**: 백엔드가 포트 5000에서 API와 프론트엔드 모두 제공
- 프론트엔드 프로덕션 빌드 완료
- CORS 설정 (모든 도메인 허용)

### ⚠️ 제한사항
- **AI/ML 라이브러리 미설치**: 디스크 용량 제약으로 대형 AI/ML 라이브러리 (PyTorch, FAISS, Sentence Transformers) 미설치
- **기능 제한**: 문서 검색, 요약, RAG 기능이 AI 라이브러리에 의존하므로 현재 비활성화됨
- **활성화된 API**: 인증(auth), 권한(permissions), 성능(performance) 엔드포인트만 활성화

### 🔧 활성화 방법
AI/ML 기능을 활성화하려면:
1. 충분한 디스크 공간 확보 (최소 5GB 권장)
2. 필요 라이브러리 설치:
   ```bash
   cd backend
   pip install sentence-transformers langchain faiss-cpu torch
   ```
3. `backend/app/api/router.py`에서 주석 처리된 라우터 활성화
4. 워크플로우 재시작

## 배포 아키텍처

### 통합 서버 구조
- **단일 포트**: 백엔드 서버가 포트 5000에서 실행
- **API 경로**: `/api/*` - FastAPI REST API
- **프론트엔드**: `/*` - React SPA (프로덕션 빌드)
- **정적 파일**: `/static/*` - 프론트엔드 JS/CSS
- **업로드 파일**: `/uploads/*` - 문서 파일

### 장점
- Replit 환경에서 단일 포트(5000)만 외부 노출
- CORS 문제 없음 (같은 도메인)
- 프록시 불필요
- 배포 간소화

## 로컬 개발 설정

### 통합 서버 실행 (권장)
```bash
# 프론트엔드 빌드
cd frontend
npm run build

# 백엔드 서버 실행 (포트 5000)
cd ../backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### 별도 서버 실행 (개발 시)
```bash
# 터미널 1: 백엔드
cd backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload

# 터미널 2: 프론트엔드
cd frontend
npm start
```

## 기본 계정 정보
- **사용자명**: admin
- **비밀번호**: admin123
- ⚠️ 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!

## API 문서
백엔드가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:5000/api/docs
- ReDoc: http://localhost:5000/api/redoc

## 주요 기능

### 현재 사용 가능
- ✅ 사용자 인증 및 권한 관리
- ✅ 성능 모니터링
- ✅ 기본 API 인프라
- ✅ React SPA 프론트엔드

### AI 라이브러리 설치 후 사용 가능
- 📄 문서 업로드 및 파싱 (PDF, Word, Excel)
- 🔍 RAG 기반 의미 검색
- 📝 LLM 기반 문서 요약
- 🔐 문서별 접근 권한 제어
- 🤖 Ollama/Hugging Face 모델 통합

## 환경 변수

### Backend (.env)
```
DATABASE_URL=sqlite:///./data/documents.db
SECRET_KEY=your-secret-key-change-in-production
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2:7b
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO
```

## 트러블슈팅

### bcrypt 경고
데이터베이스 초기화 시 bcrypt 버전 관련 경고가 표시될 수 있으나, 기능에는 영향 없음.

### AI 기능 사용 불가
디스크 용량 부족으로 AI/ML 라이브러리가 설치되지 않은 경우, 위의 "활성화 방법" 섹션 참조.

### 로그인 문제
- 계정: admin / admin123
- 프론트엔드와 백엔드가 같은 포트(5000)에서 제공되므로 CORS 문제 없음
- 브라우저 캐시를 지우고 다시 시도

## 배포 설정
- **배포 타겟**: VM (상태 유지가 필요한 앱)
- **빌드 명령**: `cd frontend && npm run build`
- **실행 명령**: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 5000`
- **포트**: 5000 (webview)

## 추가 리소스
- 프로젝트 README.md
- SETUP_GUIDE.md
- ARCHITECTURE.md
- TEST_GUIDE.md

## 업데이트 기록
- **2025-11-08**: Replit 환경 초기 설정 완료
  - Python 3.11 및 Node.js 20 설치
  - 기본 의존성 설치
  - 데이터베이스 초기화
  - 통합 서버 아키텍처 구현 (백엔드 포트 5000에서 API + 프론트엔드 제공)
  - 프론트엔드 프로덕션 빌드
  - 워크플로우 단일화
  - AI/ML 라이브러리는 디스크 용량 제약으로 보류
