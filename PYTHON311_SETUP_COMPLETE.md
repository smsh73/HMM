# Python 3.11 환경 설정 완료

## 설정 완료 사항

✅ Python 3.11 가상환경 생성
✅ 모든 필수 패키지 설치
✅ PyTorch CPU 버전 설치 완료
✅ Transformers 설치 완료
✅ 데이터베이스 초기화 완료
✅ 백엔드 서버 재시작 완료

## 가상환경 활성화

새 터미널에서 작업할 때마다 다음 명령어로 가상환경을 활성화하세요:

```bash
cd "/Users/seungminlee/Downloads/HMM 2"
source venv311/bin/activate
```

## 서버 시작

### 백엔드 서버
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv311/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 서버
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## 접속 정보

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/api/docs
- **로그인**: admin / admin123

## CPU 기반 LLM/SLM 서빙 테스트

### 1. 모델 다운로드 및 서빙

웹 UI를 통해:
1. http://localhost:3000 접속
2. 로그인 (admin/admin123)
3. "모델 관리" 메뉴 클릭
4. HuggingFace에서 모델 검색
5. 모델 다운로드
6. "서빙 시작" 클릭

### 2. API를 통한 테스트

```bash
# 로그인하여 토큰 획득
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 모델 서빙 시작
curl -X POST "http://localhost:8000/api/serving/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "microsoft/phi-2",
    "model_type": "transformers"
  }'
```

### 3. 채팅 테스트

1. http://localhost:3000 접속
2. "AI 채팅" 메뉴 클릭
3. 메시지 입력 및 전송
4. CPU 기반 모델로 응답 생성 확인

## 설치된 주요 패키지

- **PyTorch**: CPU 버전
- **Transformers**: 최신 버전
- **FastAPI**: 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **ChromaDB**: 벡터 데이터베이스
- **Sentence-Transformers**: 임베딩 생성

## 권장 모델 (CPU 환경)

1. **microsoft/phi-2** (2.7B)
   - 가장 빠름
   - 메모리: ~2GB
   - 응답 시간: 5~15초

2. **google/gemma-2b-it** (2B)
   - 경량
   - 메모리: ~2GB
   - 응답 시간: 5~15초

3. **beomi/KoAlpaca-Polyglot-5.8B** (5.8B)
   - 한글 특화
   - 메모리: ~6GB
   - 응답 시간: 15~30초

## 문제 해결

### 가상환경이 인식되지 않을 때
```bash
# 가상환경 재생성
cd "/Users/seungminlee/Downloads/HMM 2"
rm -rf venv311
python3.11 -m venv venv311
source venv311/bin/activate
```

### 패키지 재설치
```bash
source venv311/bin/activate
cd backend
pip install -r requirements.txt
pip install torch transformers accelerate
```

### 서버 포트 충돌
```bash
# 기존 프로세스 종료
pkill -f "uvicorn app.main:app"
pkill -f "node.*react"

# 서버 재시작
cd backend
source ../venv311/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 다음 단계

1. ✅ Python 3.11 환경 설정 완료
2. ✅ PyTorch 설치 완료
3. ⏭️ 모델 다운로드 및 서빙 시작
4. ⏭️ 채팅 기능 테스트
5. ⏭️ RAG 기능 테스트

이제 CPU 기반 LLM/SLM 서빙이 가능합니다!

