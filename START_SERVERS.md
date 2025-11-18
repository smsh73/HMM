# 서버 실행 최종 안내

## 서버 실행 방법

두 서버를 터미널에서 직접 실행하세요.

### 터미널 1: 백엔드 서버

```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**성공 확인**:
- `INFO:     Uvicorn running on http://0.0.0.0:8000` 메시지
- http://localhost:8000/docs 접속 가능

### 터미널 2: 프론트엔드 서버

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- `Compiled successfully!` 메시지
- 브라우저 자동 열림

## 접속 정보

- **백엔드**: http://localhost:8000/docs
- **프론트엔드**: http://localhost:3000
- **로그인**: admin / admin123

## 문제 해결

서버 시작 시 오류가 발생하면 터미널에 표시된 오류 메시지를 확인하고 필요한 패키지를 설치하세요.

