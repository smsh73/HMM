# 설치 및 실행 가이드

## 사전 요구사항

### 필수 소프트웨어
- Python 3.9 이상
- Node.js 18 이상 및 npm
- Ollama (로컬 LLM 실행 엔진)

### 선택적 소프트웨어
- Tesseract OCR (이미지 텍스트 추출용)

## 1. 백엔드 설정

### 1.1 Python 가상 환경 생성 및 활성화

```bash
cd backend
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 1.2 의존성 설치

```bash
pip install -r requirements.txt
```

### 1.3 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 설정합니다:

```env
# 데이터베이스
DATABASE_URL=sqlite:///./data/documents.db

# JWT 시크릿 키 (프로덕션에서는 반드시 변경)
SECRET_KEY=your-secret-key-change-in-production

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2:7b

# 임베딩 모델
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### 1.4 데이터베이스 초기화

```bash
python init_db.py
```

이 스크립트는:
- 데이터베이스 테이블을 생성합니다
- 기본 관리자 계정을 생성합니다 (username: admin, password: admin123)

### 1.5 Ollama 설치 및 모델 다운로드

#### Ollama 설치
- macOS: `brew install ollama`
- Linux: https://ollama.ai/download 에서 설치 스크립트 실행
- Windows: https://ollama.ai/download 에서 설치 파일 다운로드

#### Ollama 서버 실행
```bash
ollama serve
```

#### LLM 모델 다운로드
```bash
# Llama 2 7B 모델 다운로드
ollama pull llama2:7b

# 또는 Mistral 7B 모델
ollama pull mistral:7b
```

### 1.6 백엔드 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 2. 프론트엔드 설정

### 2.1 의존성 설치

```bash
cd frontend
npm install
```

### 2.2 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 설정합니다:

```env
REACT_APP_API_URL=http://localhost:8000
```

### 2.3 개발 서버 실행

```bash
npm start
```

프론트엔드는 http://localhost:3000 에서 실행됩니다.

## 3. 시스템 사용 방법

### 3.1 로그인

1. 브라우저에서 http://localhost:3000 접속
2. 기본 관리자 계정으로 로그인:
   - 사용자명: admin
   - 비밀번호: admin123

### 3.2 문서 업로드 및 처리

1. **문서 업로드**
   - 문서 관리 페이지에서 파일 업로드
   - 지원 형식: PDF, Word (.docx, .doc), Excel (.xlsx, .xls), 텍스트 (.txt)

2. **문서 파싱**
   - 업로드된 문서를 선택하여 "파싱" 버튼 클릭
   - 문서 내용이 추출되어 데이터베이스에 저장됩니다

3. **문서 인덱싱**
   - 파싱된 문서를 선택하여 "인덱싱" 버튼 클릭
   - 문서가 벡터화되어 검색 가능한 상태가 됩니다

### 3.3 문서 검색

1. 검색 페이지에서 검색어 입력
2. "답변 생성" 옵션을 선택하면 LLM 기반 답변도 생성됩니다
3. 검색 결과에서 관련 문서와 출처를 확인할 수 있습니다

### 3.4 문서 요약

1. 문서 상세 페이지에서 "요약" 버튼 클릭
2. 요약 타입 선택:
   - 핵심 요약: 간결한 핵심 내용
   - 상세 요약: 주요 섹션 포함 상세 내용
   - 키워드: 핵심 키워드 추출

### 3.5 권한 관리

1. 관리자 계정으로 로그인
2. 권한 관리 페이지에서 문서별 접근 권한 설정
3. 사용자별 또는 역할별 권한을 설정할 수 있습니다

## 4. 저사양 환경 최적화

### 4.1 모델 최적화

저사양 PC에서 실행하는 경우, 더 작은 모델을 사용하거나 설정을 조정할 수 있습니다:

```env
# 더 작은 임베딩 모델 사용
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 더 작은 LLM 모델 사용
OLLAMA_MODEL=llama2:7b-chat-q4_0  # 양자화된 모델
```

### 4.2 배치 크기 조정

`backend/app/core/config.py`에서 다음 설정을 조정합니다:

```python
BATCH_SIZE = 16  # 기본값: 32
CHUNK_SIZE = 500  # 기본값: 1000
MAX_SEARCH_RESULTS = 5  # 기본값: 10
```

### 4.3 메모리 최적화

- 문서를 한 번에 하나씩 처리
- 배치 업로드 시 큐를 사용하여 순차 처리
- 불필요한 캐시 정리

## 5. 문제 해결

### 5.1 Ollama 연결 오류

- Ollama 서버가 실행 중인지 확인: `curl http://localhost:11434/api/tags`
- 모델이 다운로드되었는지 확인: `ollama list`
- 환경 변수 `OLLAMA_BASE_URL` 확인

### 5.2 임베딩 모델 다운로드 오류

- 인터넷 연결 확인 (최초 다운로드 시 필요)
- 모델 이름 확인: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- 수동 다운로드: Python에서 `SentenceTransformer('모델명')` 실행

### 5.3 메모리 부족 오류

- 배치 크기 감소
- 더 작은 모델 사용
- 문서 청크 크기 감소

### 5.4 데이터베이스 오류

- 데이터베이스 파일 권한 확인
- `init_db.py` 재실행
- 데이터베이스 파일 삭제 후 재생성

## 6. 프로덕션 배포

### 6.1 보안 설정

1. **JWT 시크릿 키 변경**
   ```env
   SECRET_KEY=강력한-랜덤-문자열
   ```

2. **기본 관리자 비밀번호 변경**
   - 로그인 후 비밀번호 변경
   - 또는 데이터베이스에서 직접 수정

3. **HTTPS 설정** (가능한 경우)
   - Nginx 리버스 프록시 설정
   - SSL 인증서 설치

### 6.2 성능 최적화

1. **데이터베이스 최적화**
   - SQLite 대신 PostgreSQL 사용 고려
   - 인덱스 최적화

2. **캐싱 전략**
   - 검색 결과 캐싱
   - 요약 결과 캐싱

3. **비동기 처리**
   - 문서 파싱/인덱싱을 백그라운드 작업으로 처리
   - Celery 또는 FastAPI BackgroundTasks 사용

## 7. 추가 리소스

- FastAPI 문서: https://fastapi.tiangolo.com/
- React 문서: https://react.dev/
- LangChain 문서: https://python.langchain.com/
- Ollama 문서: https://ollama.ai/

## 8. 지원 및 문의

문제가 발생하거나 질문이 있으시면 프로젝트 관리자에게 문의하세요.

