# 프론트엔드 서버 실행 확인 ✅

## 상태 확인

프론트엔드 서버가 정상적으로 실행 중입니다!

- **URL**: http://localhost:3000
- **상태**: 실행 중 (HTTP 200 응답 확인)

## 접속 방법

1. **웹 브라우저 열기**
2. **주소창에 입력**: `http://localhost:3000`
3. **엔터 키 입력**

## 로그인 정보

- **사용자명**: `admin`
- **비밀번호**: `admin123`

## 문제가 계속되는 경우

### 1. 브라우저 캐시 클리어
- Chrome/Edge: `Ctrl + Shift + Delete` (Mac: `Cmd + Shift + Delete`)
- 캐시 및 쿠키 삭제

### 2. 시크릿 모드에서 접속
- Chrome: `Ctrl + Shift + N` (Mac: `Cmd + Shift + N`)
- 주소: `http://localhost:3000`

### 3. 서버 재시작

**프론트엔드 서버 재시작**:
```bash
# 현재 실행 중인 서버 중지 (터미널에서 Ctrl + C)
# 그 다음 다시 실행
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**백엔드 서버 확인**:
```bash
# 백엔드가 실행 중인지 확인
curl http://localhost:8000/docs

# 실행 중이 아니면 시작
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 포트 확인

```bash
# 포트 3000 사용 중인 프로세스 확인
lsof -i :3000

# 포트 8000 사용 중인 프로세스 확인
lsof -i :8000
```

## 정상 동작 확인

프론트엔드가 정상적으로 로드되면:
- 로그인 페이지가 표시됩니다
- 또는 이미 로그인된 경우 대시보드가 표시됩니다

## 다음 단계

1. ✅ http://localhost:3000 접속
2. ✅ admin / admin123으로 로그인
3. ✅ Documents 페이지에서 문서 업로드
4. ✅ Search 페이지에서 검색 테스트
5. ✅ HuggingFace Models에서 모델 다운로드

## 추가 도움말

- `FRONTEND_START.md`: 프론트엔드 실행 가이드
- `DEPLOYMENT_COMPLETE.md`: 배포 완료 안내
- `QUICK_START.md`: 빠른 시작 가이드

