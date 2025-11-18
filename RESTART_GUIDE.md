# 애플리케이션 재시작 가이드

## 서버 재시작 방법

### 방법 1: 자동 재시작 (권장)

터미널에서 다음 명령어를 실행하면 자동으로 재시작됩니다.

### 방법 2: 수동 재시작

#### 1단계: 기존 프로세스 종료

**터미널에서 실행**:
```bash
# 포트 8000 (백엔드) 프로세스 종료
lsof -i :8000
kill -9 <PID>

# 포트 3000 (프론트엔드) 프로세스 종료
lsof -i :3000
kill -9 <PID>
```

또는:
```bash
pkill -f "uvicorn app.main:app"
pkill -f "react-scripts start"
```

#### 2단계: 백엔드 서버 시작

**새 터미널 창 1**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**성공 확인**:
- 터미널에 `INFO:     Uvicorn running on http://0.0.0.0:8000` 메시지 표시
- 브라우저에서 http://localhost:8000/docs 접속하여 API 문서 확인

#### 3단계: 프론트엔드 서버 시작

**새 터미널 창 2**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- 터미널에 `Compiled successfully!` 메시지 표시
- 브라우저가 자동으로 열리고 http://localhost:3000 접속

## 빠른 재시작 스크립트

### 백엔드 재시작
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
pkill -f "uvicorn app.main:app"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 재시작
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
pkill -f "react-scripts start"
npm start
```

## 서버 상태 확인

### 백엔드 확인
```bash
curl http://localhost:8000/docs
# 또는 브라우저에서 http://localhost:8000/docs 접속
```

### 프론트엔드 확인
```bash
curl http://localhost:3000
# 또는 브라우저에서 http://localhost:3000 접속
```

### 포트 확인
```bash
# 포트 8000 확인
lsof -i :8000

# 포트 3000 확인
lsof -i :3000
```

## 로그인 정보

- **URL**: http://localhost:3000
- **사용자명**: admin
- **비밀번호**: admin123

## 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# 프로세스 확인
lsof -i :8000
lsof -i :3000

# 프로세스 종료
kill -9 <PID>
```

### 서버가 시작되지 않는 경우
1. 로그 확인 (터미널 출력)
2. 의존성 확인:
   ```bash
   # 백엔드
   cd backend
   source ../venv/bin/activate
   pip list | grep fastapi
   
   # 프론트엔드
   cd frontend
   npm list react-scripts
   ```

### 데이터베이스 오류
```bash
cd backend
source ../venv/bin/activate
python init_db.py
```

## 정상 동작 확인

### 백엔드
- ✅ http://localhost:8000/docs 접속 가능
- ✅ API 문서가 표시됨

### 프론트엔드
- ✅ http://localhost:3000 접속 가능
- ✅ 로그인 페이지가 표시됨
- ✅ admin/admin123으로 로그인 가능

## 서버 중지

각 터미널에서 `Ctrl + C`를 눌러 서버를 중지합니다.

