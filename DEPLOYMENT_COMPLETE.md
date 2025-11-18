# 배포 완료! 🎉

## 배포 상태

✅ **Python 가상환경**: 생성 완료
✅ **백엔드 의존성**: 설치 완료
✅ **데이터베이스**: 초기화 완료 (12개 테이블 생성)
✅ **관리자 계정**: 생성 완료 (admin / admin123)
✅ **프론트엔드 의존성**: 설치 완료

## 서버 실행 방법

### 1. 백엔드 서버 실행

**새 터미널 창에서 실행**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**성공 확인**:
- 터미널에 `INFO:     Uvicorn running on http://0.0.0.0:8000` 메시지 표시
- 브라우저에서 `http://localhost:8000/docs` 접속하여 API 문서 확인

### 2. 프론트엔드 실행

**새 터미널 창에서 실행**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- 브라우저가 자동으로 열리고 `http://localhost:3000` 접속
- 또는 수동으로 `http://localhost:3000` 접속

## 로그인 정보

- **URL**: http://localhost:3000
- **사용자명**: `admin`
- **비밀번호**: `admin123`

⚠️ **프로덕션 환경에서는 반드시 비밀번호를 변경하세요!**

## 주요 기능

### 1. 문서 관리
- Documents 페이지에서 문서 업로드
- 자동 파싱 및 인덱싱
- 다국어 문서 지원

### 2. 검색 기능
- Search 페이지에서 하이브리드 검색
- 벡터 검색 + 키워드 검색 (BM25)
- RAG 기반 답변 생성

### 3. 모델 관리
- HuggingFace Models: 모델 검색 및 다운로드
- Model Management: 모델 로드/언로드/교체
- 단일 모델 제한 (CPU 메모리 최적화)

### 4. AI 챗봇
- Chat 페이지에서 대화
- 로컬 LLM/SLM 사용

### 5. 검색 피드백
- 검색 결과에 대한 피드백 제공
- 통계 및 성능 분석

## Sample Docs 처리 (선택사항)

`sample docs` 폴더의 문서를 처리하려면:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
python scripts/process_sample_docs.py
```

## API 문서

백엔드 서버 실행 후:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 문제 해결

### 포트 충돌
```bash
# 포트 8000 확인
lsof -i :8000
kill -9 <PID>

# 포트 3000 확인
lsof -i :3000
kill -9 <PID>
```

### 서버 재시작
각 터미널에서 `Ctrl + C`로 서버 중지 후 다시 실행

### 로그 확인
```bash
# 백엔드 로그
tail -f backend/data/logs/app.log
tail -f backend/data/logs/error.log
```

## 다음 단계

1. ✅ 서버 실행 (위의 명령어 사용)
2. ✅ 웹 브라우저에서 로그인
3. ✅ Sample Docs 처리 (선택사항)
4. ✅ 모델 다운로드 및 서빙
5. ✅ 문서 업로드 및 검색 테스트

## 참고 문서

- `QUICK_START.md`: 빠른 시작 가이드
- `DEPLOYMENT_GUIDE.md`: 상세 배포 가이드
- `DEPLOYMENT_STATUS.md`: 배포 상태 및 문제 해결
- `IMPLEMENTATION_SUMMARY.md`: 구현 요약

## 축하합니다! 🎊

애플리케이션이 성공적으로 배포되었습니다. 이제 서버를 실행하고 사용을 시작하세요!

