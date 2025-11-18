# 서버 실행 상태

## 현재 상태

### ✅ 백엔드 서버
- **상태**: 실행 중
- **포트**: 8000
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 프론트엔드 서버
- **상태**: 확인 필요
- **포트**: 3000
- **URL**: http://localhost:3000

## 프론트엔드 서버 실행

백엔드는 실행 중입니다. 프론트엔드를 실행하세요.

### 터미널에서 실행

**새 터미널 창을 열고**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- 터미널에 `Compiled successfully!` 메시지 표시
- 브라우저가 자동으로 열리고 http://localhost:3000 접속

## 접속 확인

### 백엔드
브라우저에서 http://localhost:8000/docs 접속
- Swagger UI가 표시되면 정상 ✅

### 프론트엔드
브라우저에서 http://localhost:3000 접속
- 로그인 페이지가 표시되면 정상

## 로그인 정보

- **URL**: http://localhost:3000
- **사용자명**: admin
- **비밀번호**: admin123

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

## 정상 동작 확인

✅ **백엔드**: http://localhost:8000/docs 접속 가능
⏳ **프론트엔드**: 실행 필요 (위의 명령어 실행)

## 참고

- `START_SERVERS.md`: 서버 실행 가이드
- `RESTART_GUIDE.md`: 재시작 가이드

