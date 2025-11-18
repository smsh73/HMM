# 프론트엔드 서버 상태

## 현재 상태

프론트엔드 서버가 실행 중입니다.

## 접속 방법

### 1. 브라우저에서 직접 접속

**주소**: http://localhost:3000

### 2. 서버 상태 확인

터미널에서 다음 명령어로 확인:
```bash
curl http://localhost:3000
```

또는 브라우저에서:
- http://localhost:3000
- http://127.0.0.1:3000

## 서버가 시작되지 않는 경우

### 프론트엔드 서버 재시작

**새 터미널 창에서**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

### 포트 확인

```bash
# 포트 3000 사용 중인 프로세스
lsof -i :3000

# 프로세스 종료 후 재시작
kill -9 <PID>
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## 백엔드 서버도 확인

프론트엔드가 백엔드 API에 연결되려면 백엔드 서버도 실행되어야 합니다.

**백엔드 서버 실행** (새 터미널):
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**백엔드 확인**:
- http://localhost:8000/docs

## 두 서버 모두 실행 확인

### 터미널 1: 백엔드
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 터미널 2: 프론트엔드
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## 로그인

서버가 정상적으로 실행되면:

1. 브라우저에서 http://localhost:3000 접속
2. 로그인 페이지가 표시됩니다
3. 로그인 정보:
   - 사용자명: `admin`
   - 비밀번호: `admin123`

## 문제 해결

### 브라우저 캐시 클리어
- Chrome/Edge: `Ctrl + Shift + Delete` (Mac: `Cmd + Shift + Delete`)
- 캐시 및 쿠키 삭제

### 시크릿 모드에서 접속
- Chrome: `Ctrl + Shift + N` (Mac: `Cmd + Shift + N`)
- 주소: http://localhost:3000

### 서버 로그 확인
프론트엔드 서버를 실행한 터미널에서 오류 메시지를 확인하세요.

## 추가 도움말

- `FRONTEND_TROUBLESHOOTING.md`: 상세 문제 해결 가이드
- `FRONTEND_START.md`: 프론트엔드 실행 가이드

