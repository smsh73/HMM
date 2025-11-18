# 프론트엔드 실행 가이드

## 프론트엔드 서버 실행 방법

### 방법 1: 직접 실행 (권장)

**새 터미널 창을 열고 다음 명령어 실행**:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**예상 동작**:
- React 개발 서버가 시작됩니다
- 브라우저가 자동으로 열리고 `http://localhost:3000` 접속
- 터미널에 컴파일 상태가 표시됩니다

### 방법 2: 포트 지정 실행

포트 3000이 사용 중인 경우:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
PORT=3001 npm start
```

그러면 `http://localhost:3001`에서 접속 가능합니다.

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

`.env` 파일이 필요한 경우:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
PORT=3000
EOF
npm start
```

## 실행 확인

서버가 정상적으로 실행되면:

1. **터미널 출력 확인**:
   ```
   Compiled successfully!
   You can now view hmm-document-search-frontend in the browser.
   Local:            http://localhost:3000
   ```

2. **브라우저 접속**:
   - 자동으로 브라우저가 열립니다
   - 또는 수동으로 `http://localhost:3000` 접속

3. **로그인**:
   - 사용자명: `admin`
   - 비밀번호: `admin123`

## 백엔드 연결 확인

프론트엔드가 백엔드 API에 연결되는지 확인:

1. 브라우저 개발자 도구 열기 (F12)
2. Network 탭 확인
3. API 요청이 `http://localhost:8000`으로 전송되는지 확인

## 서버 중지

프론트엔드 서버를 중지하려면:
- 터미널에서 `Ctrl + C` 입력

## 로그 확인

프론트엔드 실행 중 오류가 발생하면:
- 터미널에 에러 메시지가 표시됩니다
- 브라우저 콘솔(F12)에서도 에러 확인 가능

## 추가 도움말

- 백엔드 서버가 실행 중인지 확인: `lsof -i :8000`
- 프론트엔드 서버가 실행 중인지 확인: `lsof -i :3000`
- 프로세스 확인: `ps aux | grep -E "react-scripts|npm"`

