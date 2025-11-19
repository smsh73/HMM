# Python 3.11 환경 배포 완료

## ✅ 배포 완료 사항

1. **Python 3.11 가상환경 생성** ✅
2. **PyTorch CPU 버전 설치** ✅
3. **Transformers 설치** ✅
4. **모든 필수 패키지 설치** ✅
5. **데이터베이스 초기화** ✅
6. **백엔드 서버 실행** ✅

## 🚀 서버 접속 정보

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/api/docs
- **로그인**: admin / admin123

## 📦 설치된 주요 패키지

- **PyTorch 2.2.2** (CPU 버전)
- **Transformers 4.57.1**
- **NumPy 1.x** (PyTorch 호환)
- **FastAPI 0.121.2**
- **ChromaDB** (벡터 데이터베이스)
- **Sentence-Transformers** (임베딩)

## 🎯 CPU 기반 LLM/SLM 서빙 사용 방법

### 방법 1: 웹 UI 사용 (권장)

1. **브라우저에서 접속**
   ```
   http://localhost:3000
   ```

2. **로그인**
   - 사용자명: `admin`
   - 비밀번호: `admin123`

3. **모델 다운로드 및 서빙**
   - "모델 관리" 메뉴 클릭
   - HuggingFace에서 모델 검색
   - 모델 다운로드
   - "서빙 시작" 클릭

4. **채팅 테스트**
   - "AI 채팅" 메뉴 클릭
   - 메시지 입력 및 전송
   - CPU 기반 모델 응답 확인

### 방법 2: API 사용

```bash
# 1. 로그인하여 토큰 획득
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. 모델 서빙 시작
curl -X POST "http://localhost:8000/api/serving/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "microsoft/phi-2",
    "model_type": "transformers"
  }'

# 3. 채팅 테스트
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요",
    "use_rag": false,
    "use_main_system": true
  }'
```

## 📊 권장 모델 (CPU 환경)

### 1. microsoft/phi-2 (2.7B) ⭐ 추천
- **특징**: 가장 빠름, 영어 특화
- **메모리**: ~2GB
- **응답 시간**: 5~15초
- **용도**: 일반적인 질문 답변

### 2. google/gemma-2b-it (2B)
- **특징**: 경량, instruction-tuned
- **메모리**: ~2GB
- **응답 시간**: 5~15초
- **용도**: 지시사항 따르기

### 3. beomi/KoAlpaca-Polyglot-5.8B (5.8B)
- **특징**: 한글 특화
- **메모리**: ~6GB
- **응답 시간**: 15~30초
- **용도**: 한글 질문 답변

## 🔧 서버 관리

### 가상환경 활성화
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
source venv311/bin/activate
```

### 백엔드 서버 시작
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv311/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 서버 시작
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

### 서버 종료
```bash
# 백엔드 종료
pkill -f "uvicorn app.main:app"

# 프론트엔드 종료
pkill -f "node.*react"
```

## ⚠️ 주의사항

### CPU 기반 서빙 특성
- **응답 속도**: GPU 대비 느림 (5~30초)
- **메모리 사용**: 모델 크기에 따라 2~8GB
- **동시 요청**: 한 번에 하나의 모델만 서빙 가능

### 성능 최적화 팁
1. 경량 모델 사용 (phi-2, gemma-2b)
2. 토큰 수 제한 (`max_new_tokens=256`)
3. 다른 애플리케이션 종료하여 메모리 확보

## 🐛 문제 해결

### 모델 로딩 실패
```bash
# 인터넷 연결 확인
ping -c 3 huggingface.co

# 디스크 공간 확인
df -h

# 메모리 확인
free -h  # Linux
vm_stat  # macOS
```

### 서버 포트 충돌
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :8000
lsof -i :3000

# 프로세스 종료
kill -9 <PID>
```

### 패키지 재설치
```bash
source venv311/bin/activate
cd backend
pip install -r requirements.txt
```

## ✅ 다음 단계

1. ✅ Python 3.11 환경 설정 완료
2. ✅ PyTorch 설치 완료
3. ⏭️ 모델 다운로드 및 서빙 시작
4. ⏭️ 채팅 기능 테스트
5. ⏭️ RAG 기능 테스트 (문서 검색 + LLM)

**이제 CPU 기반 LLM/SLM 서빙이 완전히 준비되었습니다!** 🎉

