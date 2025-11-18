# 서버 실행 안내

## 현재 상태

두 서버 모두 실행되지 않았습니다. 터미널에서 직접 실행해야 합니다.

## 서버 실행 방법

### 터미널 1: 백엔드 서버

**새 터미널 창을 열고**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**성공 확인**:
- 터미널에 `INFO:     Uvicorn running on http://0.0.0.0:8000` 메시지 표시
- 브라우저에서 http://localhost:8000/docs 접속하여 API 문서 확인

### 터미널 2: 프론트엔드 서버

**새 터미널 창을 열고**:
```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- 터미널에 `Compiled successfully!` 메시지 표시
- 브라우저가 자동으로 열리고 http://localhost:3000 접속

## 누락된 패키지 설치

서버 시작 시 오류가 발생하면:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/backend"
source ../venv/bin/activate

# 필수 패키지 설치
pip install 'pydantic[email]' psutil pdfplumber langdetect nltk python-docx openpyxl PyPDF2 chromadb rank-bm25 --no-cache-dir

# torch는 Python 3.13에서 설치되지 않을 수 있음 (선택사항)
# 필요시 Python 3.11 또는 3.12로 가상환경 재생성
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

## 로그인 정보

- **URL**: http://localhost:3000
- **사용자명**: admin
- **비밀번호**: admin123

## 문제 해결

### 서버가 시작되지 않는 경우

1. **의존성 확인**
   - 터미널에 표시된 오류 메시지 확인
   - 누락된 패키지 설치

2. **포트 충돌**
   ```bash
   lsof -i :8000
   lsof -i :3000
   kill -9 <PID>
   ```

3. **가상환경 확인**
   ```bash
   source venv/bin/activate
   which python
   python --version
   ```

## 정상 동작 확인

✅ **백엔드**: http://localhost:8000/docs 접속 가능
✅ **프론트엔드**: http://localhost:3000 접속 가능
✅ **로그인**: admin / admin123

## 참고

- `FINAL_SERVER_STATUS.md`: 서버 상태 상세 정보
- `RESTART_GUIDE.md`: 재시작 가이드

