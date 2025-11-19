# 서버 시작 가이드

## 현재 상태

✅ 백엔드 서버: http://localhost:8000 (실행 중)
✅ 프론트엔드 서버: http://localhost:3000 (실행 중)

## CPU 기반 LLM/SLM 서빙 확인

### PyTorch 설치
Python 3.13에서는 PyTorch 설치가 제한적일 수 있습니다. 다음 방법을 시도하세요:

```bash
# 방법 1: 최신 PyTorch 설치
pip install torch torchvision torchaudio

# 방법 2: CPU 전용 (Python 3.13 미지원 시)
# Python 3.11 또는 3.12 사용 권장
```

### 모델 서빙 테스트

1. **웹 UI 접속**
   - http://localhost:3000
   - 로그인: admin / admin123

2. **모델 관리**
   - "모델 관리" 메뉴 클릭
   - HuggingFace에서 모델 검색
   - 모델 다운로드 및 서빙 시작

3. **채팅 테스트**
   - "AI 채팅" 메뉴 클릭
   - 메시지 입력 및 전송
   - CPU 기반 모델 응답 확인

## 서버 재시작 (필요시)

### 백엔드 재시작
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 재시작
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## CPU 기반 서빙 특징

### 장점
- ✅ GPU 없이도 동작
- ✅ 모든 MacBook에서 실행 가능
- ✅ 추가 하드웨어 불필요

### 제한사항
- ⚠️ GPU 대비 느린 응답 속도 (5~30초)
- ⚠️ 메모리 사용량 높음 (2~8GB)
- ⚠️ 큰 모델(5B+)은 느릴 수 있음

### 권장 모델
1. **microsoft/phi-2** (2.7B) - 가장 빠름
2. **google/gemma-2b-it** (2B) - 경량
3. **beomi/KoAlpaca-Polyglot-5.8B** (5.8B) - 한글 특화 (느림)

## 문제 해결

### PyTorch 설치 실패
- Python 3.11 또는 3.12 사용 권장
- 또는 conda 환경 사용

### 모델 로딩 실패
- 인터넷 연결 확인
- 디스크 공간 확인 (모델당 2~10GB)
- 메모리 확인 (최소 8GB)

### 응답 속도가 느림
- 경량 모델 사용 (phi-2, gemma-2b)
- 토큰 수 제한
- CPU 기반 특성상 정상
