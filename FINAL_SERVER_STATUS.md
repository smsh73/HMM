# 서버 실행 상태 최종 확인

## 현재 상태

### 백엔드 서버
- **패키지 설치**: 진행 중
- **상태**: 시작 중
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 프론트엔드 서버
- **상태**: 시작 중 (컴파일 중)
- **URL**: http://localhost:3000

## 서버 실행 방법 (권장)

백그라운드 실행 대신 터미널에서 직접 실행하는 것을 권장합니다.

### 터미널 1: 백엔드 서버

```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**성공 확인**:
- 터미널에 `INFO:     Uvicorn running on http://0.0.0.0:8000` 메시지 표시
- 브라우저에서 http://localhost:8000/docs 접속하여 API 문서 확인

### 터미널 2: 프론트엔드 서버

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- 터미널에 `Compiled successfully!` 메시지 표시
- 브라우저가 자동으로 열리고 http://localhost:3000 접속

## 누락된 패키지 설치

필요한 패키지가 누락된 경우:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
pip install -r requirements.txt --no-cache-dir
```

또는 개별 설치:
```bash
pip install 'pydantic[email]' psutil pdfplumber langdetect nltk python-docx openpyxl PyPDF2 chromadb rank-bm25 sentence-transformers --no-cache-dir
```

## 서버 상태 확인

### 브라우저에서 확인

1. **백엔드**: http://localhost:8000/docs
2. **프론트엔드**: http://localhost:3000

### 터미널에서 확인

```bash
# 포트 확인
lsof -i :8000
lsof -i :3000

# HTTP 요청 확인
curl http://localhost:8000/docs
curl http://localhost:3000
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

## 로그인 정보

- **URL**: http://localhost:3000
- **사용자명**: admin
- **비밀번호**: admin123

## 문제 해결

### 서버가 시작되지 않는 경우

1. **의존성 재설치**
   ```bash
   cd backend
   source ../venv/bin/activate
   pip install -r requirements.txt --no-cache-dir
   ```

2. **포트 충돌 확인**
   ```bash
   lsof -i :8000
   lsof -i :3000
   kill -9 <PID>
   ```

3. **로그 확인**
   - 백엔드: `/tmp/backend.log`
   - 프론트엔드: `/tmp/frontend.log`

## 정상 동작 확인

✅ **백엔드**: http://localhost:8000/docs 접속 가능
✅ **프론트엔드**: http://localhost:3000 접속 가능
✅ **로그인**: admin / admin123

