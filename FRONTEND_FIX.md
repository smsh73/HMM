# 프론트엔드 실행 오류 해결

## 문제

홈 디렉토리(`~`)에서 `npm start`를 실행하여 오류가 발생했습니다.

## 해결 방법

프론트엔드 디렉토리로 이동한 후 실행해야 합니다.

### 올바른 실행 방법

```bash
# 1. 프론트엔드 디렉토리로 이동
cd "/Users/seungminlee/Downloads/HMM 2/frontend"

# 2. npm start 실행
npm start
```

### 한 줄로 실행

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend" && npm start
```

## 단계별 가이드

### 1단계: 디렉토리 이동
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
```

### 2단계: 현재 위치 확인
```bash
pwd
# 출력: /Users/seungminlee/Downloads/HMM 2/frontend
```

### 3단계: package.json 확인
```bash
ls package.json
# package.json 파일이 있어야 합니다
```

### 4단계: 서버 실행
```bash
npm start
```

## 예상 출력

정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:

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

## 문제가 계속되는 경우

### node_modules 확인
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
ls node_modules
# node_modules 디렉토리가 있어야 합니다
```

### 재설치
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm start
```

## 백엔드 서버도 확인

프론트엔드와 함께 백엔드 서버도 실행되어야 합니다.

**새 터미널 창에서 백엔드 실행**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 정리

1. ✅ **프론트엔드**: `cd "/Users/seungminlee/Downloads/HMM 2/frontend" && npm start`
2. ✅ **백엔드**: `cd "/Users/seungminlee/Downloads/HMM 2/backend" && source ../venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
3. ✅ **브라우저**: http://localhost:3000 접속
4. ✅ **로그인**: admin / admin123

