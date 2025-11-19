# 서버 상태 확인

## 현재 서버 상태

### 백엔드 서버 ✅
- **상태**: 실행 중
- **포트**: 8000
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/api/docs
- **헬스 체크**: http://localhost:8000/health
- **환경**: Python 3.13 (venv)

### 프론트엔드 서버
- **상태**: 시작 중
- **포트**: 3000
- **URL**: http://localhost:3000

## 서버 확인 명령어

### 백엔드 상태 확인
```bash
curl http://localhost:8000/health
```

### 프론트엔드 상태 확인
```bash
curl http://localhost:3000
```

### 프로세스 확인
```bash
ps aux | grep -E "(uvicorn|node.*react)"
```

### 포트 확인
```bash
lsof -i :8000
lsof -i :3000
```

## 서버 재시작 (필요시)

### 백엔드 재시작
```bash
# 기존 프로세스 종료
pkill -f "uvicorn app.main:app"

# Python 3.11 환경으로 재시작 (권장)
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv311/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 재시작
```bash
# 기존 프로세스 종료
pkill -f "node.*react"

# 재시작
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## 접속 정보

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/api/docs
- **로그인**: admin / admin123
