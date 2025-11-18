# 프론트엔드 접속 문제 해결

## 프론트엔드 서버 실행 방법

### 올바른 실행 방법

**새 터미널 창을 열고 다음 명령어를 실행하세요**:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

## 단계별 가이드

### 1단계: 디렉토리 이동
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
```

### 2단계: 현재 위치 확인
```bash
pwd
```
출력이 `/Users/seungminlee/Downloads/HMM 2/frontend`여야 합니다.

### 3단계: package.json 확인
```bash
ls package.json
```
파일이 있어야 합니다.

### 4단계: 서버 실행
```bash
npm start
```

## 예상 출력

정상적으로 실행되면:

```
Compiling...
Compiled successfully!

You can now view hmm-document-search-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.
```

그리고 브라우저가 자동으로 열립니다.

## 문제 해결

### 1. 포트 3000이 이미 사용 중인 경우

```bash
# 포트 3000 사용 중인 프로세스 확인
lsof -i :3000

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
PORT=3001 npm start
```

### 2. node_modules 문제

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"

# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# 다시 실행
npm start
```

### 3. 캐시 문제

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"

# npm 캐시 클리어
npm cache clean --force

# node_modules 재설치
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm start
```

### 4. React Scripts 오류

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"

# react-scripts 재설치
npm install react-scripts@5.0.1 --legacy-peer-deps
npm start
```

### 5. 환경 변수 설정

`.env` 파일 확인:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
cat .env
```

필요한 경우 `.env` 파일 생성:
```bash
cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
PORT=3000
EOF
```

## 백엔드 서버도 확인

프론트엔드와 함께 백엔드 서버도 실행되어야 합니다.

**백엔드 서버 실행** (새 터미널):
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**백엔드 확인**:
```bash
curl http://localhost:8000/docs
```
API 문서가 표시되면 정상입니다.

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

## 접속 확인

1. **백엔드**: http://localhost:8000/docs
2. **프론트엔드**: http://localhost:3000

## 로그인 정보

- **URL**: http://localhost:3000
- **사용자명**: admin
- **비밀번호**: admin123

## 추가 도움말

- `FRONTEND_START.md`: 프론트엔드 실행 가이드
- `DEPLOYMENT_COMPLETE.md`: 배포 완료 안내
- `QUICK_START.md`: 빠른 시작 가이드

