# PostgreSQL 설정 가이드

## 1. PostgreSQL 설치 (Homebrew)

```bash
# PostgreSQL 설치
brew install postgresql@14

# PostgreSQL 서비스 시작
brew services start postgresql@14

# PostgreSQL 버전 확인
psql --version
```

## 2. 데이터베이스 및 사용자 생성

```bash
# PostgreSQL 접속
psql postgres

# 데이터베이스 생성
CREATE DATABASE hmm_db;

# 사용자 생성
CREATE USER hmm_user WITH PASSWORD 'your_secure_password';

# 권한 부여
GRANT ALL PRIVILEGES ON DATABASE hmm_db TO hmm_user;

# PostgreSQL 종료
\q
```

## 3. 환경 변수 설정

`backend/.env` 파일 생성 또는 수정:

```bash
# PostgreSQL 연결 문자열
DATABASE_URL=postgresql://hmm_user:your_secure_password@localhost:5432/hmm_db

# 보안 설정
SECRET_KEY=your-very-secure-secret-key-here

# 기타 설정 (선택사항)
LOG_LEVEL=INFO
```

## 4. 데이터베이스 초기화

```bash
cd backend
python init_db.py
```

이 명령은:
- 모든 테이블 생성
- 기본 관리자 계정 생성 (admin / admin123)

## 5. Alembic 마이그레이션 (선택사항)

Alembic을 사용하여 스키마 변경을 관리하려면:

```bash
# Alembic 초기화 (처음 한 번만)
alembic init alembic

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 적용
alembic upgrade head
```

## 6. 연결 테스트

```bash
# PostgreSQL 접속 테스트
psql -U hmm_user -d hmm_db -h localhost

# 테이블 목록 확인
\dt

# 사용자 목록 확인
\du
```

## 7. 문제 해결

### PostgreSQL 서비스가 실행되지 않는 경우
```bash
# 서비스 상태 확인
brew services list

# 서비스 시작
brew services start postgresql@14

# 수동 시작
pg_ctl -D /usr/local/var/postgresql@14 start
```

### 연결 오류
- 방화벽 설정 확인
- PostgreSQL이 localhost:5432에서 실행 중인지 확인
- 사용자 권한 확인

### 데이터베이스가 존재하지 않는 경우
```bash
# 데이터베이스 재생성
psql postgres
DROP DATABASE IF EXISTS hmm_db;
CREATE DATABASE hmm_db;
GRANT ALL PRIVILEGES ON DATABASE hmm_db TO hmm_user;
\q
```

## 8. SQLite에서 PostgreSQL로 마이그레이션

기존 SQLite 데이터를 PostgreSQL로 마이그레이션하려면:

```bash
# SQLite 데이터 덤프 (선택사항)
sqlite3 data/documents.db .dump > dump.sql

# PostgreSQL로 데이터 이전 (수동 작업 필요)
# 또는 애플리케이션의 데이터 내보내기/가져오기 기능 사용
```

## 9. 백업 및 복원

### 백업
```bash
# 데이터베이스 백업
pg_dump -U hmm_user -d hmm_db > backup_$(date +%Y%m%d).sql
```

### 복원
```bash
# 데이터베이스 복원
psql -U hmm_user -d hmm_db < backup_20240101.sql
```

## 10. 프로덕션 설정

프로덕션 환경에서는 다음을 고려하세요:

1. **강력한 비밀번호 사용**
2. **SSL 연결 활성화**
3. **방화벽 규칙 설정**
4. **정기적인 백업**
5. **연결 풀링 설정**
6. **모니터링 설정**

### 프로덕션 환경 변수 예시
```bash
DATABASE_URL=postgresql://hmm_user:secure_password@db.example.com:5432/hmm_db?sslmode=require
```

