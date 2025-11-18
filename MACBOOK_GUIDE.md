# 맥북 인텔 환경 사용 가이드

HMM GenAI 문서 검색/요약 시스템을 맥북 인텔 CPU 환경에서 사용하는 방법입니다.

## 시스템 요구사항

- **CPU**: 인텔 CPU (4코어 이상 권장)
- **메모리**: 8GB RAM 이상
- **디스크**: 20GB 이상 여유 공간
- **OS**: macOS 10.15 이상
- **Python**: 3.11
- **Node.js**: 20

## 1단계: 환경 설정

### Python 패키지 설치
```bash
cd backend
pip install -r requirements.txt
```

주요 패키지:
- `chromadb>=1.3.0` - 벡터 데이터베이스
- `rank-bm25>=0.2.0` - 키워드 검색
- `transformers>=4.35.0` - 로컬 SLM
- `torch==2.1.1` - CPU 전용 PyTorch
- `sentence-transformers>=2.2.2` - 임베딩 모델

### 프론트엔드 빌드
```bash
cd ../frontend
npm install
npm run build
```

## 2단계: 데이터베이스 초기화

```bash
cd ../backend
python -c "from app.core.database import init_db; init_db()"
```

기본 관리자 계정이 생성됩니다:
- **사용자명**: admin
- **비밀번호**: admin123

## 3단계: 서버 실행

### 통합 서버 실행 (권장)
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

브라우저에서 `http://localhost:5000` 접속

### 별도 서버 실행 (개발 시)
```bash
# 터미널 1: 백엔드
cd backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload

# 터미널 2: 프론트엔드
cd frontend
npm start
```

## 4단계: 로컬 SLM 설정

### 권장 모델 (경량 → 고성능 순)

#### 1. Microsoft Phi-2 (경량, 영어)
- 파라미터: 2.7B
- 메모리: ~6GB
- 속도: 빠름

```python
from app.ai.local_slm import create_local_slm

# 모델 생성 (첫 실행 시 자동 다운로드)
llm = create_local_slm("phi-2", device="cpu")

# 테스트
answer = await llm.generate("What is artificial intelligence?")
print(answer)
```

#### 2. Google Gemma 2B (경량, instruction-tuned)
- 파라미터: 2B
- 메모리: ~5GB
- 속도: 빠름

```python
llm = create_local_slm("gemma-2b", device="cpu")
```

#### 3. KoAlpaca (한글 특화)
- 파라미터: 5.8B
- 메모리: ~12GB
- 속도: 보통

```python
llm = create_local_slm("koalpaca", device="cpu")

# 한글 프롬프트
answer = await llm.generate("인공지능이란 무엇인가요?")
print(answer)
```

#### 4. KULLM (한글 특화)
- 파라미터: 5.8B
- 메모리: ~12GB
- 속도: 보통

```python
llm = create_local_slm("kullm", device="cpu")
```

### 첫 실행 시 주의사항

1. **모델 다운로드**: 첫 실행 시 Hugging Face Hub에서 모델을 자동 다운로드합니다 (수 GB).
2. **다운로드 위치**: `backend/data/huggingface_cache/`
3. **시간 소요**: 인터넷 속도에 따라 10~30분 소요
4. **이후 실행**: 캐시된 모델을 로드하므로 빠름 (오프라인 가능)

## 5단계: 기능 테스트

### 임베딩 생성
```python
from app.ai.embedding import EmbeddingGenerator

generator = EmbeddingGenerator()
embedding = generator.generate_embedding("선박 문서 검색 시스템")
print(f"임베딩 차원: {len(embedding)}")  # 384
```

### 하이브리드 검색
```python
from app.ai.hybrid_search import HybridSearchEngine

# 엔진 초기화
engine = HybridSearchEngine(
    collection_name="test_docs",
    vector_weight=0.7,
    keyword_weight=0.3
)

# 문서 추가
texts = [
    "HMM 선박에서는 문서 검색 시스템이 필요합니다.",
    "AI 모델은 문서 요약과 검색에 활용됩니다."
]
metadatas = [
    {"category": "shipping", "doc_id": "doc_1"},
    {"category": "AI", "doc_id": "doc_2"}
]

doc_ids = engine.add_documents(texts, metadatas)

# 검색
results = engine.search("선박 문서 시스템", top_k=3, search_mode="hybrid")

for doc_id, score, metadata in results:
    print(f"Score: {score:.3f}, Doc: {metadata['doc_id']}")
```

### RAG 챗봇
```python
from app.ai.hybrid_rag_engine import HybridRAGEngine
from app.ai.local_slm import create_local_slm

# RAG 엔진 초기화
rag_engine = HybridRAGEngine(collection_name="documents")

# 로컬 SLM 생성 (한글)
llm = create_local_slm("koalpaca", device="cpu")

# 문서 검색
results = rag_engine.semantic_search("선박 안전 규정", top_k=3)

# 답변 생성
answer = await rag_engine.generate_answer(
    query="선박 안전 규정에 대해 설명해주세요",
    context_results=results,
    llm_provider=llm
)

print(f"답변: {answer.answer}")
print(f"신뢰도: {answer.confidence:.2f}")
```

## 6단계: 한글 문서 처리

### 지원 형식
- PDF (한글 포함)
- Word (DOCX)
- Excel (XLSX)
- 텍스트 파일 (UTF-8)

### 문서 업로드 및 인덱싱
```python
from app.services.document_service import DocumentService
from app.core.database import SessionLocal

# DB 세션 생성
db = SessionLocal()
service = DocumentService(db)

# 문서 업로드
document = service.upload_document(
    file_path="sample.pdf",
    filename="선박_안전_매뉴얼.pdf",
    user_id="admin"
)

# 파싱
document = service.parse_document(document.id)

# 인덱싱 (Chroma + BM25)
stats = service.index_document(document.id)

print(f"인덱싱 완료: {stats['total_chunks']}개 청크")
```

## 성능 최적화

### CPU 최적화 설정
```python
import os

# OpenMP 스레드 수 제한 (CPU 코어 수에 맞춤)
os.environ["OMP_NUM_THREADS"] = "4"

# MKL 스레드 수 제한
os.environ["MKL_NUM_THREADS"] = "4"
```

### 메모리 절약
```python
# 경량 모델 사용
llm = create_local_slm("phi-2", device="cpu")  # ~6GB

# HNSW 파라미터 조정 (기본값이 이미 최적화됨)
engine = HybridSearchEngine(
    collection_name="documents",
    # M=16 (낮을수록 메모리 절약)
    # ef_construction=100 (기본값)
)
```

## 문제 해결

### 1. 모델 로딩 느림
- **원인**: CPU 전용 환경에서 모델 로딩은 느립니다
- **해결**: 첫 로딩 후 캐시되므로 재시작 시 빠름
- **예상 시간**: 첫 로딩 10~30초, 이후 5초 이내

### 2. 메모리 부족
- **원인**: 5.8B 모델은 ~12GB 메모리 필요
- **해결**: 경량 모델 사용 (phi-2, gemma-2b)

### 3. 한글 토큰화 오류
- **원인**: 모델이 한글을 지원하지 않음
- **해결**: 한글 모델 사용 (koalpaca, kullm)

### 4. Chroma 재시작 오류
- **원인**: 컬렉션 초기화 문제
- **해결**: 
```python
engine.reset()  # 컬렉션 초기화
```

## API 문서

서버 실행 후 다음 URL에서 API 문서 확인:
- Swagger UI: http://localhost:5000/api/docs
- ReDoc: http://localhost:5000/api/redoc

## 참고 자료

- Chroma 문서: https://docs.trychroma.com/
- Hugging Face Transformers: https://huggingface.co/docs/transformers/
- Sentence Transformers: https://www.sbert.net/
- BM25 알고리즘: https://pypi.org/project/rank-bm25/
