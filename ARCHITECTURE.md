# GenAI 활용 문서 요약/검색 시스템 아키텍처 설계

## 1. 프로젝트 개요

### 1.1 목표
- 온/오프라인 환경에서 안정적으로 동작하는 문서 검색 및 요약 웹 애플리케이션
- 선박 PC 환경(저사양 하드웨어, 제한적 인터넷) 최적화

### 1.2 핵심 요구사항
- 로컬 LLM 기반 오프라인 동작
- RAG 기반 의미 검색
- 문서 단위 권한 관리
- 저사양 환경 성능 최적화

## 2. 시스템 아키텍처

### 2.1 전체 구조
```
┌─────────────────────────────────────────────────┐
│           Frontend (React + TypeScript)         │
│  - 문서 업로드/관리 UI                           │
│  - 검색 인터페이스                               │
│  - 문서 뷰어                                     │
│  - 권한 관리 대시보드                            │
│  - 성능 모니터링 패널                            │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/REST API
┌──────────────────┴──────────────────────────────┐
│         Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────┐  │
│  │  API Layer                                │  │
│  │  - 문서 업로드/파싱 API                    │  │
│  │  - 검색 API                                │  │
│  │  - 요약 API                                │  │
│  │  - 권한 관리 API                           │  │
│  └──────────────┬─────────────────────────────┘  │
│  ┌──────────────┴─────────────────────────────┐  │
│  │  Business Logic Layer                       │  │
│  │  - DocumentParser                           │  │
│  │  - RAGSearchEngine                          │  │
│  │  - DocumentSummarizer                       │  │
│  │  - AccessControlManager                     │  │
│  └──────────────┬─────────────────────────────┘  │
│  ┌──────────────┴─────────────────────────────┐  │
│  │  AI/ML Layer                                │  │
│  │  - Embedding Model (sentence-transformers)  │  │
│  │  - LLM (Ollama)                             │  │
│  │  - Vector DB (FAISS/ChromaDB)               │  │
│  └──────────────┬─────────────────────────────┘  │
│  ┌──────────────┴─────────────────────────────┐  │
│  │  Data Layer                                 │  │
│  │  - SQLite (메타데이터)                       │  │
│  │  - 파일 시스템 (원본 문서)                   │  │
│  │  - 벡터 DB (임베딩)                          │  │
│  └─────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

### 2.2 기술 스택 상세

#### Frontend
- React 18+ with TypeScript
- Material-UI (MUI) - 한국어 지원
- React Query - 서버 상태 관리 및 캐싱
- React Router - SPA 라우팅
- Axios - HTTP 클라이언트

#### Backend
- FastAPI - 비동기 웹 프레임워크
- SQLAlchemy - ORM
- Pydantic - 데이터 검증
- Uvicorn - ASGI 서버

#### AI/ML
- LangChain - RAG 프레임워크
- sentence-transformers - 한국어 임베딩 (klue/bert-base)
- FAISS - 벡터 검색
- Ollama - 로컬 LLM 실행
- Llama 2 7B / Mistral 7B - 경량 모델

#### 문서 처리
- PyPDF2 / pdfplumber - PDF 파싱
- python-docx - Word 문서
- openpyxl - Excel 처리
- pytesseract - OCR

#### 데이터베이스
- SQLite - 메타데이터 및 사용자 정보
- 파일 시스템 - 원본 문서 저장
- FAISS - 벡터 인덱스

## 3. 핵심 모듈 설계

### 3.1 문서 파싱 모듈 (DocumentParser)
**책임:**
- 다양한 문서 포맷 파싱 (PDF, Word, Excel)
- 문서 구조 추출 (제목, 본문, 표, 이미지)
- 메타데이터 추출
- 청크 분할 (RAG용)

**주요 클래스:**
- `DocumentParser`: 파서 인터페이스
- `PDFParser`, `WordParser`, `ExcelParser`: 포맷별 파서
- `DocumentChunker`: 문서 청크 분할
- `MetadataExtractor`: 메타데이터 추출

### 3.2 RAG 검색 엔진 (RAGSearchEngine)
**책임:**
- 문서 임베딩 생성 및 벡터화
- 의미 기반 검색
- 컨텍스트 기반 답변 생성
- 출처 추적

**주요 클래스:**
- `RAGSearchEngine`: 검색 엔진 메인
- `EmbeddingGenerator`: 임베딩 생성
- `VectorStore`: 벡터 DB 관리
- `Retriever`: 검색 결과 조회
- `AnswerGenerator`: 답변 생성

### 3.3 문서 요약 엔진 (DocumentSummarizer)
**책임:**
- 문서 타입별 맞춤형 요약
- 요약 품질 평가
- 키워드 추출

**주요 클래스:**
- `DocumentSummarizer`: 요약 엔진 메인
- `SummaryGenerator`: 요약 생성
- `QualityEvaluator`: 품질 평가

### 3.4 권한 관리 시스템 (AccessControlManager)
**책임:**
- 역할 기반 접근 제어 (RBAC)
- 문서/섹션 단위 권한 설정
- 실시간 권한 검증
- 접근 로그 관리

**주요 클래스:**
- `AccessControlManager`: 권한 관리 메인
- `PermissionChecker`: 권한 검증
- `ContentMasker`: 권한 없는 컨텐츠 마스킹
- `AuditLogger`: 접근 로그

### 3.5 성능 최적화 모듈 (PerformanceOptimizer)
**책임:**
- 리소스 모니터링
- 저사양 환경 최적화
- 캐시 관리
- 배치 처리

**주요 클래스:**
- `PerformanceOptimizer`: 최적화 메인
- `ResourceMonitor`: 리소스 모니터링
- `CacheManager`: 캐시 관리
- `BatchProcessor`: 배치 처리

## 4. 데이터 모델

### 4.1 데이터베이스 스키마

#### documents 테이블
- id: 문서 ID (UUID)
- filename: 파일명
- file_type: 파일 타입 (pdf, docx, xlsx)
- file_path: 파일 경로
- file_size: 파일 크기
- upload_date: 업로드 날짜
- parsed_content: 파싱된 내용 (JSON)
- metadata: 메타데이터 (JSON)
- created_by: 업로드 사용자 ID

#### document_chunks 테이블
- id: 청크 ID
- document_id: 문서 ID
- chunk_index: 청크 인덱스
- content: 청크 내용
- metadata: 청크 메타데이터 (JSON)
- embedding_id: 임베딩 벡터 ID

#### users 테이블
- id: 사용자 ID
- username: 사용자명
- email: 이메일
- password_hash: 비밀번호 해시
- role: 역할 (admin, user, viewer)
- created_at: 생성일

#### permissions 테이블
- id: 권한 ID
- document_id: 문서 ID
- user_id: 사용자 ID (nullable)
- role: 역할 (nullable)
- permission_type: 권한 타입 (read, write, delete)
- created_at: 생성일

#### search_history 테이블
- id: 검색 ID
- user_id: 사용자 ID
- query: 검색 쿼리
- results_count: 결과 수
- search_date: 검색 날짜

## 5. API 설계

### 5.1 문서 관리 API
- `POST /api/documents/upload`: 문서 업로드
- `GET /api/documents`: 문서 목록 조회
- `GET /api/documents/{id}`: 문서 상세 조회
- `DELETE /api/documents/{id}`: 문서 삭제
- `POST /api/documents/{id}/parse`: 문서 파싱

### 5.2 검색 API
- `POST /api/search`: 의미 기반 검색
- `GET /api/search/suggestions`: 검색 제안
- `GET /api/search/history`: 검색 기록

### 5.3 요약 API
- `POST /api/documents/{id}/summarize`: 문서 요약
- `GET /api/documents/{id}/summary`: 요약 조회

### 5.4 권한 관리 API
- `GET /api/permissions`: 권한 목록
- `POST /api/permissions`: 권한 설정
- `DELETE /api/permissions/{id}`: 권한 삭제
- `GET /api/permissions/check`: 권한 확인

### 5.5 인증 API
- `POST /api/auth/login`: 로그인
- `POST /api/auth/logout`: 로그아웃
- `GET /api/auth/me`: 현재 사용자 정보

## 6. 성능 최적화 전략

### 6.1 저사양 환경 대응
- 모델 양자화 (INT8)
- 점진적 로딩 (Lazy Loading)
- 배치 처리 최적화
- 메모리 효율적인 청크 처리

### 6.2 캐싱 전략
- 검색 결과 캐싱
- 임베딩 캐싱
- 요약 결과 캐싱
- 프론트엔드 React Query 캐싱

### 6.3 비동기 처리
- 문서 파싱 비동기 처리
- 배치 업로드 큐 관리
- 백그라운드 인덱싱

## 7. 보안 고려사항

### 7.1 인증/인가
- JWT 기반 인증
- 역할 기반 접근 제어
- 세션 관리

### 7.2 데이터 보안
- 파일 업로드 검증
- SQL Injection 방지
- XSS 방지
- 파일 경로 검증

## 8. 배포 전략

### 8.1 로컬 배포
- 단일 서버 배포
- SQLite 사용
- 파일 시스템 저장

### 8.2 확장 가능성
- Docker 컨테이너화
- PostgreSQL 마이그레이션
- 분산 벡터 DB

## 9. 개발 단계

### Phase 1: 프로젝트 초기 설정
- 프로젝트 구조 생성
- 개발 환경 설정
- 기본 템플릿 구성

### Phase 2: 문서 파싱 모듈
- 문서 파서 구현
- 업로드 API 개발
- 업로드 UI 개발

### Phase 3: RAG 검색 엔진
- 임베딩 및 벡터 DB 구축
- 검색 API 구현
- 검색 UI 개발

### Phase 4: 권한 관리 시스템
- 인증/권한 체계 구현
- 권한 관리 UI 개발

### Phase 5: 문서 요약 기능
- 요약 엔진 구현
- 요약 UI 개발

### Phase 6: UI/UX 통합
- 전체 UI 통합
- 사용자 경험 최적화

### Phase 7: 성능 최적화 및 테스트
- 저사양 환경 최적화
- 통합 테스트
- 성능 벤치마크

