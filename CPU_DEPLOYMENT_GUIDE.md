# CPU 기반 LLM/SLM 서빙 배포 가이드

## CPU 기반 서빙 가능 여부

**네, 가능합니다!** 현재 구현된 시스템은 CPU 기반으로 동작하도록 설계되었습니다.

### 구현 확인 사항

1. **LocalSLMProvider**: `device='cpu'` 기본 설정
2. **ModelServingService**: CPU 기반 모델 로드
3. **최적화 설정**:
   - `torch_dtype=torch.float32` (CPU용)
   - `low_cpu_mem_usage=True` (메모리 절약)
   - `device=-1` (CPU 모드)

### 지원 모델

- **microsoft/phi-2** (2.7B, 경량, 추천)
- **google/gemma-2b-it** (2B, 경량)
- **beomi/KoAlpaca-Polyglot-5.8B** (5.8B, 한글 특화)
- **nlpai-lab/kullm-polyglot-5.8b-v2** (5.8B, 한글 특화)

## 배포 단계

### 1. 환경 확인

```bash
# Python 버전 확인 (3.8 이상 필요)
python3 --version

# 가상환경 활성화
cd "/Users/seungminlee/Downloads/HMM 2"
source venv/bin/activate
```

### 2. 필수 패키지 설치

```bash
cd backend

# 기본 패키지 설치
pip install -r requirements.txt

# CPU 전용 PyTorch 설치 (macOS)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Transformers 설치
pip install transformers accelerate
```

### 3. 데이터베이스 초기화

```bash
# 데이터베이스 초기화
python init_db.py

# 또는 Alembic 마이그레이션
alembic upgrade head
```

### 4. 환경 변수 설정 (선택사항)

```bash
# .env 파일 생성 (필요시)
cat > .env << EOF
DATABASE_URL=sqlite:///./data/documents.db
SECRET_KEY=your-secret-key-change-in-production
VECTOR_DB_PATH=./data/vector_db
EOF
```

### 5. 서버 시작

```bash
# 백엔드 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드 서버 시작 (새 터미널)
cd frontend
npm install
npm start
```

## 모델 다운로드 및 서빙

### 방법 1: API를 통한 모델 다운로드

1. 브라우저에서 `http://localhost:3000` 접속
2. 로그인 (admin/admin123)
3. "모델 관리" 메뉴로 이동
4. HuggingFace에서 모델 검색 및 다운로드
5. 다운로드 완료 후 "서빙 시작" 클릭

### 방법 2: 직접 모델 다운로드

```bash
# Python 스크립트로 모델 다운로드
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='microsoft/phi-2',
    local_dir='./data/huggingface_cache/microsoft_phi-2',
    local_dir_use_symlinks=False
)
"
```

### 방법 3: API 호출로 모델 서빙 시작

```bash
# 모델 서빙 시작
curl -X POST "http://localhost:8000/api/serving/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "microsoft/phi-2",
    "model_type": "transformers"
  }'
```

## 성능 최적화 팁

### 1. 경량 모델 사용
- **phi-2** (2.7B): 가장 빠름, 영어 특화
- **gemma-2b** (2B): 경량, instruction-tuned

### 2. 메모리 최적화
- 모델 로드 시 `low_cpu_mem_usage=True` 사용
- 한 번에 하나의 모델만 서빙

### 3. 토큰 수 제한
- `max_new_tokens=256` (기본 512에서 감소)
- 짧은 응답 생성으로 속도 향상

## 테스트

### 1. 모델 서빙 상태 확인

```bash
curl http://localhost:8000/api/serving/current
```

### 2. 채팅 테스트

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요",
    "use_rag": false,
    "use_main_system": true
  }'
```

## 문제 해결

### 1. 메모리 부족
- 더 작은 모델 사용 (phi-2, gemma-2b)
- `max_new_tokens` 감소
- 다른 애플리케이션 종료

### 2. 모델 로딩 실패
- 인터넷 연결 확인 (초기 다운로드 필요)
- 디스크 공간 확인
- HuggingFace 토큰 설정 (필요시)

### 3. 속도가 느림
- CPU 기반이므로 GPU 대비 느릴 수 있음
- 경량 모델 사용 권장
- 토큰 수 제한

## 예상 성능

### CPU 환경 (MacBook)
- **모델 로딩**: 30초 ~ 2분 (모델 크기에 따라)
- **응답 생성**: 5~30초 (토큰 수에 따라)
- **메모리 사용**: 2~8GB (모델 크기에 따라)

### 권장 사양
- **CPU**: 4코어 이상
- **RAM**: 8GB 이상 (16GB 권장)
- **디스크**: 10GB 이상 (모델 저장용)

