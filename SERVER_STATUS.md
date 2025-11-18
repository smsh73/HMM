# 서버 재시작 완료

## 서버 실행 상태

백엔드와 프론트엔드 서버를 재시작했습니다.

## 접속 정보

### 백엔드 서버
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **상태**: 실행 중

### 프론트엔드 서버
- **URL**: http://localhost:3000
- **상태**: 시작 중 (컴파일 완료까지 30초~1분 소요)

## 접속 방법

### 1. 브라우저에서 직접 접속

**프론트엔드**:
1. 브라우저를 엽니다
2. 주소창에 입력: `http://localhost:3000`
3. 엔터 키를 누릅니다

**백엔드 API 문서**:
1. 브라우저를 엽니다
2. 주소창에 입력: `http://localhost:8000/docs`
3. 엔터 키를 누릅니다

### 2. 로그인

프론트엔드가 로드되면:
- **사용자명**: `admin`
- **비밀번호**: `admin123`

## 서버 상태 확인

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

## 프론트엔드가 아직 로드되지 않는 경우

프론트엔드는 컴파일하는 데 시간이 걸립니다 (30초~1분).

### 확인 방법

프론트엔드를 실행한 터미널에서:
- `Compiling...` 메시지가 보이면 컴파일 중입니다
- `Compiled successfully!` 메시지가 보이면 준비 완료입니다

### 수동으로 실행

**새 터미널 창에서**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## 백엔드 수동 실행

**새 터미널 창에서**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

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
각 터미널에서 `Ctrl + C`로 중지 후 다시 실행

## 다음 단계

1. ✅ 백엔드 서버 실행 확인: http://localhost:8000/docs
2. ✅ 프론트엔드 서버 실행 확인: http://localhost:3000
3. ✅ 로그인: admin / admin123
4. ✅ 기능 사용 시작

## 참고 문서

- `RESTART_GUIDE.md`: 재시작 가이드
- `DEPLOYMENT_COMPLETE.md`: 배포 완료 안내
- `QUICK_START.md`: 빠른 시작 가이드

