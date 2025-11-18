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
- **AI/ML 라이브러리 설치 완료**:
  - PyTorch 2.0.1 (CPU 전용, 184MB - CUDA 버전 대비 약 700MB 절약)
  - Transformers 4.44.0
  - Sentence Transformers 5.1.2
  - LangChain (최신 버전)
  - FAISS-CPU (AVX2 지원)
- **AI API 엔드포인트 활성화**: 30개 AI 관련 API 라우터 활성화
  - 엔드포인트: documents, search, summary, llm_settings, models, rag_sync, huggingface, model_serving, chat
  - 주의: 엔드포인트는 활성화되었으나 end-to-end 워크플로우 테스트는 필요

### 📊 시스템 상태
- **디스크 사용량**: 약 21GB 사용 가능
- **임베딩 모델**: paraphrase-multilingual-MiniLM-L12-v2 (384 차원)
- **벡터 스토어**: FAISS (AVX2 최적화)
- **API 엔드포인트**: 47개 (30개 AI 엔드포인트 포함)

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

### ✅ 검증 완료
- 👤 사용자 인증 및 권한 관리
- 📊 성능 모니터링
- 🔌 30개 AI API 엔드포인트 활성화 (라우터 등록 완료)
- 🧠 임베딩 생성 모듈 (SentenceTransformer, 384차원)
- 📁 FAISS 벡터 인덱스 초기화 (AVX2 최적화)

### 🔄 추가 테스트 필요
다음 기능들은 API가 활성화되었으나 end-to-end 워크플로우 검증이 필요합니다:
- 📄 문서 업로드 및 파싱 (PDF, Word, Excel)
- 🔍 RAG 기반 의미 검색
- 📝 LLM 기반 문서 요약
- 🤖 Ollama/Hugging Face 모델 통합
- 💬 채팅 인터페이스
- ⚙️ LLM 프로바이더 관리
- 🔐 문서별 접근 권한 제어

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

### 로그인 문제
- 계정: admin / admin123
- 프론트엔드와 백엔드가 같은 포트(5000)에서 제공되므로 CORS 문제 없음
- 브라우저 캐시를 지우고 다시 시도

### AI 모델 로딩 시간
- 임베딩 모델(paraphrase-multilingual-MiniLM-L12-v2) 첫 로드 시 약 5-10초 소요
- FAISS 인덱스는 AVX2 최적화로 빠른 검색 성능 제공

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

## POC 개발 로드맵 (4단계)

### 1단계: CDC + 증분 임베딩 ⚠️ (제한사항 있음)
**목표**: 변경된 문서만 재처리하여 리소스 절약

**구현 완료**:
- ✅ 파일 레벨 CDC (SHA-256 해시 기반 변경 감지)
- ✅ 데이터베이스 스키마 확장 (file_hash, content_hash, DocumentVersion)
- ✅ 기본 증분 처리 프레임워크

**제한사항 및 폴백 전략**:
- ⚠️ **청크 레벨 증분 동기화 미구현**: 
  - 문제: 삽입/삭제 시 위치 변경으로 정확한 청크 매칭 어려움
  - 문제: 중복 콘텐츠 청크의 정확한 추적 복잡
  - 필요: 복잡한 sequence alignment 알고리즘 (Myers, Needleman-Wunsch 등)
- ✅ **현재 전략**: 파일 레벨 CDC + 전체 청크 재인덱싱
  - 파일 해시로 변경 감지 → 변경된 문서만 처리 (리소스 절약)
  - 청크는 전체 재생성 및 재임베딩 (안정성 보장)
  - 대부분 문서는 작아서 전체 재인덱싱이 충분히 빠름

**운영 영향**:
- 문서 업데이트 시 전체 임베딩 재생성 필요 (수십~수백 청크)
- 대용량 문서(수천 청크) 업데이트 시 시간 소요
- 임베딩 ID 연속성 미보장 (메타데이터/권한 연결 고려 필요)

### 2단계: Chroma + HNSW + 하이브리드 검색 ✅ (완료)
**목표**: 고성능 벡터 검색 및 키워드 결합 검색

**구현 완료**:
- ✅ Chroma 벡터 DB 통합 (FAISS 대체)
  - ChromaDB 1.3+ 사용
  - PersistentClient로 자동 영속성
  - 재시작 시 자동 로드
- ✅ HNSW 인덱싱 알고리즘 적용
  - M=16 (메모리 최적화)
  - ef_construction=100 (빌드 품질)
  - ef_search=50 (검색 정확도)
  - 코사인 유사도 사용
- ✅ BM25 키워드 검색
  - rank-bm25 라이브러리
  - 한글/영문 토큰화
  - TF-IDF 확률론적 변형
- ✅ 하이브리드 검색 엔진
  - RRF (Reciprocal Rank Fusion) 방식
  - 벡터 0.7 + 키워드 0.3 가중치
  - 검색 모드: hybrid, vector, keyword
- ✅ 문서 서비스 Chroma 통합
  - DocumentService에 Hybrid RAG 적용
  - 기존 FAISS 대신 Chroma 사용
- ✅ 로컬 SLM (Small Language Model)
  - Hugging Face transformers 기반
  - CPU 전용 최적화 (맥북 인텔 환경)
  - 권장 모델: Microsoft Phi-2, Google Gemma 2B
  - 한글 모델: KoAlpaca, KULLM
  - 로컬 실행 (인터넷 불필요)

### 3단계: 오프라인 모드 📅 (계획)
**목표**: 완전한 로컬 동작 (인터넷 불필요)

**계획**:
- Ollama 로컬 LLM 통합
- 로컬 RAG 시스템 구축
- 온라인 복귀 시 자동 동기화
- 네트워크 상태 감지 및 폴백

### 4단계: 고급 보안 (RBAC + ABAC) 📅 (계획)
**목표**: 엔터프라이즈급 권한 관리

**계획**:
- RBAC + ABAC 하이브리드 모델
- 문서/섹션/문단 레벨 권한 제어
- MTLS 양방향 인증
- 상세 감사 로그

## 업데이트 기록
- **2025-11-08**: Replit 환경 초기 설정 완료
  - Python 3.11 및 Node.js 20 설치
  - 기본 의존성 설치
  - 데이터베이스 초기화
  - 통합 서버 아키텍처 구현 (백엔드 포트 5000에서 API + 프론트엔드 제공)
  - 프론트엔드 프로덕션 빌드
  - 워크플로우 단일화
  - AI/ML 라이브러리는 디스크 용량 제약으로 보류
- **2025-11-08 (오후)**: AI/ML 기능 활성화 완료
  - PyTorch 2.0.1 CPU 버전 설치 (호환성 문제 해결)
  - Transformers 4.44.0 및 Sentence Transformers 5.1.2 설치
  - LangChain 및 FAISS-CPU (AVX2) 설치
  - 30개 AI API 엔드포인트 활성화
  - 더미 API 라우터 제거
  - 기능 검증 완료:
    - SentenceTransformer 임베딩 생성 (384차원, 3개 텍스트 0.36초)
    - FAISS 벡터 인덱스 생성 및 로딩 (AVX2 최적화)
    - 모델 로딩 시간: 약 5초
- **2025-11-18**: POC 1단계 완료 및 2단계 시작
  - 1단계 CDC 시스템 구현 (파일 레벨)
  - 청크 레벨 증분 임베딩 제한사항 문서화
  - 2단계 Chroma + HNSW 구현 시작
