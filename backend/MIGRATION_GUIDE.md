# 데이터베이스 마이그레이션 가이드

## 마이그레이션 상태

✅ **Alembic 초기화**: 완료
✅ **초기 마이그레이션 생성**: 완료
✅ **마이그레이션 적용**: 완료

## 마이그레이션 명령어

### 현재 상태 확인
```bash
cd backend
source ../venv/bin/activate
alembic current
```

### 마이그레이션 히스토리 확인
```bash
alembic history
```

### 새 마이그레이션 생성
```bash
# 자동 생성 (모델 변경 감지)
alembic revision --autogenerate -m "마이그레이션 설명"

# 수동 생성
alembic revision -m "마이그레이션 설명"
```

### 마이그레이션 적용
```bash
# 최신 마이그레이션까지 적용
alembic upgrade head

# 특정 리비전까지 적용
alembic upgrade <revision>

# 다음 마이그레이션 하나만 적용
alembic upgrade +1
```

### 마이그레이션 롤백
```bash
# 이전 마이그레이션으로 롤백
alembic downgrade -1

# 특정 리비전으로 롤백
alembic downgrade <revision>

# 모든 마이그레이션 롤백
alembic downgrade base
```

## 모델 변경 시 마이그레이션 프로세스

### 1. 모델 수정
`backend/app/models/database.py`에서 모델을 수정합니다.

### 2. 마이그레이션 생성
```bash
cd backend
source ../venv/bin/activate
alembic revision --autogenerate -m "모델 변경 설명"
```

### 3. 마이그레이션 파일 검토
생성된 마이그레이션 파일을 확인하고 필요시 수정합니다:
- `backend/alembic/versions/xxxxx_마이그레이션_설명.py`

### 4. 마이그레이션 적용
```bash
alembic upgrade head
```

## 생성된 마이그레이션 파일

현재 생성된 마이그레이션:
- `alembic/versions/e039a76cfcf2_initial_migration_with_all_models.py`

이 마이그레이션은 다음 테이블을 생성합니다:
- users
- documents
- document_chunks
- document_versions
- permissions
- search_history
- search_feedback
- llm_providers
- local_models
- rag_sync
- chat_conversations
- chat_messages

## 주의사항

### SQLite 사용 시
- SQLite는 일부 ALTER TABLE 작업을 지원하지 않습니다
- 테이블 구조 변경이 필요한 경우 테이블 재생성이 필요할 수 있습니다

### PostgreSQL 사용 시
- `.env` 파일에 `DATABASE_URL` 설정:
  ```
  DATABASE_URL=postgresql://user:password@localhost:5432/hmm_db
  ```
- 마이그레이션은 PostgreSQL의 모든 기능을 지원합니다

### 프로덕션 환경
- 마이그레이션 적용 전 백업 필수
- 테스트 환경에서 먼저 테스트
- 다운타임 계획 수립

## 문제 해결

### 마이그레이션 충돌
```bash
# 현재 상태 확인
alembic current

# 충돌 해결 후
alembic upgrade head
```

### 마이그레이션 파일 수정
마이그레이션 파일을 직접 수정한 후:
```bash
alembic upgrade head
```

### 마이그레이션 재생성
기존 마이그레이션을 삭제하고 재생성:
```bash
# 마이그레이션 파일 삭제
rm alembic/versions/*.py

# 새로 생성
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 참고

- Alembic 문서: https://alembic.sqlalchemy.org/
- SQLAlchemy 문서: https://docs.sqlalchemy.org/

