# 배포 상태 및 접속 정보

## 서버 상태

### 백엔드 서버
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/api/docs
- **상태**: 실행 중

### 프론트엔드 서버
- **URL**: http://localhost:3000
- **상태**: 실행 중

## CPU 기반 LLM/SLM 서빙

### 확인 사항
✅ PyTorch CPU 버전 설치 완료
✅ Transformers 설치 완료
✅ CPU 기반 모델 서빙 설정 완료

### 사용 가능한 모델

1. **microsoft/phi-2** (2.7B, 경량, 추천)
   - 영어 특화
   - 빠른 응답 속도
   - 메모리 사용량: ~2GB

2. **google/gemma-2b-it** (2B, 경량)
   - Instruction-tuned
   - 메모리 사용량: ~2GB

3. **beomi/KoAlpaca-Polyglot-5.8B** (5.8B, 한글 특화)
   - 한글 지원 우수
   - 메모리 사용량: ~6GB

4. **nlpai-lab/kullm-polyglot-5.8b-v2** (5.8B, 한글 특화)
   - 한글 지원 우수
   - 메모리 사용량: ~6GB

## 모델 서빙 방법

### 1. 웹 UI를 통한 서빙
1. http://localhost:3000 접속
2. 로그인 (admin/admin123)
3. "모델 관리" 메뉴 클릭
4. HuggingFace에서 모델 검색
5. 모델 다운로드
6. "서빙 시작" 클릭

### 2. API를 통한 서빙

```bash
# 1. 로그인하여 토큰 획득
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | jq -r '.access_token')

# 2. 모델 서빙 시작
curl -X POST "http://localhost:8000/api/serving/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "microsoft/phi-2",
    "model_type": "transformers"
  }'
```

## 테스트

### 채팅 테스트
1. http://localhost:3000 접속
2. "AI 채팅" 메뉴 클릭
3. 메시지 입력 및 전송
4. CPU 기반 모델로 응답 생성 확인

### API 테스트
```bash
# 채팅 API 호출
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요",
    "use_rag": false,
    "use_main_system": true
  }'
```

## 성능 참고사항

### CPU 기반 서빙 특성
- **모델 로딩**: 30초 ~ 2분 (모델 크기에 따라)
- **응답 생성**: 5~30초 (토큰 수에 따라)
- **메모리 사용**: 2~8GB (모델 크기에 따라)

### 최적화 팁
1. 경량 모델 사용 (phi-2, gemma-2b)
2. 토큰 수 제한 (max_new_tokens=256)
3. 한 번에 하나의 모델만 서빙

## 문제 해결

### 모델 로딩 실패
- 인터넷 연결 확인 (초기 다운로드 필요)
- 디스크 공간 확인 (모델당 2~10GB)
- 메모리 확인 (최소 8GB 권장)

### 응답 속도가 느림
- CPU 기반이므로 GPU 대비 느릴 수 있음
- 경량 모델 사용 권장
- 토큰 수 제한

### 메모리 부족
- 더 작은 모델 사용
- 다른 애플리케이션 종료
- max_new_tokens 감소

## 다음 단계

1. 모델 다운로드 및 서빙 시작
2. 채팅 기능 테스트
3. RAG 기능 테스트 (문서 검색 + LLM)
4. 성능 모니터링
