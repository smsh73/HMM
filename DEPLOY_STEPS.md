# 배포 단계별 가이드

이 문서는 실제 배포를 위한 단계별 명령어를 제공합니다.

## 1단계: Python 가상환경 설정

```bash
cd "/Users/seungminlee/Downloads/HMM 2"
python3 -m venv venv
source venv/bin/activate
```

## 2단계: 백엔드 의존성 설치

```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

**예상 시간**: 5-10분 (인터넷 속도에 따라 다름)

## 3단계: 데이터베이스 초기화

```bash
python init_db.py
```

**출력 확인**:
- ✓ 데이터베이스 테이블 생성 완료
- ✓ 기본 관리자 계정 생성 완료

## 4단계: Sample Docs 처리 (선택사항)

```bash
python scripts/process_sample_docs.py
```

**예상 시간**: 문서 수에 따라 다름 (문서당 1-2분)

## 5단계: 백엔드 서버 실행

**새 터미널 창에서 실행**:

```bash
cd "/Users/seungminlee/Downloads/HMM 2"
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**성공 확인**:
- `INFO:     Uvicorn running on http://0.0.0.0:8000`
- 브라우저에서 `http://localhost:8000/docs` 접속하여 API 문서 확인

## 6단계: 프론트엔드 의존성 설치 (처음 한 번만)

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm install
```

**예상 시간**: 2-5분

## 7단계: 프론트엔드 실행

**새 터미널 창에서 실행**:

```bash
cd "/Users/seungminlee/Downloads/HMM 2/frontend"
npm start
```

**성공 확인**:
- 브라우저가 자동으로 열리고 `http://localhost:3000` 접속
- 또는 수동으로 `http://localhost:3000` 접속

## 8단계: 로그인 및 사용

1. 브라우저에서 `http://localhost:3000` 접속
2. 로그인:
   - 사용자명: `admin`
   - 비밀번호: `admin123`
3. 기능 사용 시작

## 서버 중지 방법

각 터미널에서 `Ctrl + C`를 눌러 서버를 중지합니다.

## 문제 해결

### 포트 8000이 이미 사용 중인 경우
```bash
lsof -i :8000
kill -9 <PID>
```

### 포트 3000이 이미 사용 중인 경우
```bash
lsof -i :3000
kill -9 <PID>
```

### 가상환경 활성화 오류
```bash
# 가상환경 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### 의존성 설치 오류
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-cache-dir
```

