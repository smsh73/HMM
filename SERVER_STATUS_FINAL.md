# 서버 실행 상태 최종 확인

## 현재 상태

서버들이 백그라운드에서 시작되었습니다. 완전히 준비되기까지 몇 초가 걸릴 수 있습니다.

## 확인 방법

### 1. 브라우저에서 직접 확인

**백엔드**:
- http://localhost:8000/docs
- API 문서가 표시되면 정상

**프론트엔드**:
- http://localhost:3000
- 로그인 페이지가 표시되면 정상

### 2. 터미널에서 확인

```bash
# 백엔드 확인
curl http://localhost:8000/docs

# 프론트엔드 확인
curl http://localhost:3000

# 포트 확인
lsof -i :8000
lsof -i :3000
```

## 서버가 실행되지 않는 경우

### 수동으로 실행 (권장)

백그라운드 실행 대신 터미널에서 직접 실행하면 로그를 실시간으로 확인할 수 있습니다.

#### 터미널 1: 백엔드
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 터미널 2: 프론트엔드
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

## 프로세스 확인

```bash
# 실행 중인 서버 확인
ps aux | grep -E "uvicorn|react-scripts" | grep -v grep

# 포트 사용 확인
lsof -i :8000
lsof -i :3000
```

## 서버 중지

```bash
# 백엔드 중지
pkill -f "uvicorn app.main:app"

# 프론트엔드 중지
pkill -f "react-scripts"
```

## 접속 정보

- **백엔드**: http://localhost:8000/docs
- **프론트엔드**: http://localhost:3000
- **로그인**: admin / admin123

## 다음 단계

1. 브라우저에서 http://localhost:3000 접속
2. 로그인 페이지 확인
3. admin / admin123으로 로그인
4. 기능 사용 시작

