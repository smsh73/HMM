# 서버 실행 상태 확인

## 현재 상태

### 백엔드 서버 (포트 8000)
- **상태**: 시작 중
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 프론트엔드 서버 (포트 3000)
- **상태**: 시작 중 (컴파일 중, 30초~1분 소요)
- **URL**: http://localhost:3000

## 서버 상태 확인 방법

### 1. 포트 확인
```bash
lsof -i :8000
lsof -i :3000
```

### 2. HTTP 요청 확인
```bash
# 백엔드
curl http://localhost:8000/docs

# 프론트엔드
curl http://localhost:3000
```

### 3. 프로세스 확인
```bash
ps aux | grep -E "uvicorn|react-scripts" | grep -v grep
```

## 서버 수동 실행

### 백엔드 서버
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 서버
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## 로그 확인

### 백엔드 로그
```bash
tail -f /tmp/backend.log
# 또는
tail -f backend/data/logs/app.log
```

### 프론트엔드 로그
```bash
tail -f /tmp/frontend.log
```

## 접속 확인

### 백엔드
브라우저에서 http://localhost:8000/docs 접속
- API 문서가 표시되면 정상

### 프론트엔드
브라우저에서 http://localhost:3000 접속
- 로그인 페이지가 표시되면 정상

## 문제 해결

### 서버가 시작되지 않는 경우

1. **포트 충돌 확인**
   ```bash
   lsof -i :8000
   lsof -i :3000
   kill -9 <PID>
   ```

2. **의존성 확인**
   ```bash
   # 백엔드
   cd backend
   source ../venv/bin/activate
   pip list | grep fastapi
   
   # 프론트엔드
   cd frontend
   npm list react-scripts
   ```

3. **로그 확인**
   - 백엔드: `/tmp/backend.log` 또는 `backend/data/logs/error.log`
   - 프론트엔드: `/tmp/frontend.log`

## 정상 동작 확인

✅ **백엔드**: http://localhost:8000/docs 접속 가능
✅ **프론트엔드**: http://localhost:3000 접속 가능
✅ **로그인**: admin / admin123

