# 서버 실행 상태 최종 확인

## 현재 상태

### 백엔드 서버
- **패키지 설치**: email-validator 설치 완료
- **상태**: 재시작 중
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 프론트엔드 서버
- **상태**: 시작 중 (컴파일 중)
- **URL**: http://localhost:3000

## 확인 방법

### 브라우저에서 확인

1. **백엔드 API 문서**: http://localhost:8000/docs
   - Swagger UI가 표시되면 정상

2. **프론트엔드**: http://localhost:3000
   - 로그인 페이지가 표시되면 정상

### 터미널에서 확인

```bash
# 백엔드 확인
curl http://localhost:8000/docs

# 프론트엔드 확인
curl http://localhost:3000

# 포트 확인
lsof -i :8000
lsof -i :3000
```

## 서버 수동 실행 (권장)

백그라운드 실행 대신 터미널에서 직접 실행하면 로그를 실시간으로 확인할 수 있습니다.

### 터미널 1: 백엔드
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**성공 확인**:
- `INFO:     Uvicorn running on http://0.0.0.0:8000` 메시지 표시
- http://localhost:8000/docs 접속 가능

### 터미널 2: 프론트엔드
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- `Compiled successfully!` 메시지 표시
- 브라우저가 자동으로 열림

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

## 프로세스 확인

```bash
# 실행 중인 서버 확인
ps aux | grep -E "uvicorn.*8000|react-scripts" | grep -v grep

# 포트 사용 확인
lsof -i :8000
lsof -i :3000
```

## 로그인 정보

- **URL**: http://localhost:3000
- **사용자명**: admin
- **비밀번호**: admin123

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
   pip install 'pydantic[email]'
   ```

3. **로그 확인**
   - 백엔드: `/tmp/backend.log`
   - 프론트엔드: `/tmp/frontend.log`

## 정상 동작 확인

✅ **백엔드**: http://localhost:8000/docs 접속 가능
✅ **프론트엔드**: http://localhost:3000 접속 가능
✅ **로그인**: admin / admin123

