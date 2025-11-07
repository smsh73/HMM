# LLM 이원화 시스템 구현 가이드

## 개요

시스템은 두 가지 LLM 환경을 지원합니다:

1. **메인 시스템**: OpenAI, Claude, Gemini, Perplexity API 사용
2. **선박용 시스템**: 노트북에서 경량 모델을 운영하는 on-device LLM 환경

## 주요 기능

### 1. LLM 프로바이더 관리

#### 지원 프로바이더
- **OpenAI**: GPT-3.5, GPT-4 등
- **Claude (Anthropic)**: Claude 3 Sonnet 등
- **Gemini (Google)**: Gemini Pro 등
- **Perplexity**: Llama 3 Sonar 등
- **Ollama**: 로컬 LLM (Llama 2, Mistral 등)

#### API 키 관리
- 관리자 화면에서 API 키 설정 및 관리
- API 키는 암호화되어 데이터베이스에 저장
- 프로바이더별 활성/비활성 설정 가능
- 메인 시스템용/선박 시스템용 구분

### 2. 경량 모델 관리

#### 모델 브라우징
- Ollama에서 사용 가능한 모델 목록 조회
- 모델 크기 및 정보 표시

#### 모델 다운로드
- 관리자 화면에서 모델 다운로드 시작
- 다운로드 진행률 실시간 표시
- 다운로드 완료 후 자동 인덱싱

#### 모델 삭제
- 불필요한 모델 삭제 기능
- Ollama 및 데이터베이스에서 동시 삭제

### 3. RAG 동기화

#### 내보내기 (메인 시스템 → 선박 시스템)
- 벡터 DB 파일 (FAISS 인덱스, 메타데이터) 내보내기
- 문서 메타데이터 JSON 내보내기
- 타겟 시스템 식별자 지정

#### 가져오기 (선박 시스템 ← 메인 시스템)
- 내보낸 RAG 데이터 가져오기
- 벡터 DB 파일 복사 및 인덱스 재구성
- 동기화 기록 관리

#### 동기화 방법
1. **파일 시스템 기반 동기화** (현재 구현)
   - 메인 시스템에서 RAG 데이터를 파일로 내보내기
   - USB 또는 네트워크를 통해 선박 시스템으로 전송
   - 선박 시스템에서 파일 경로 지정하여 가져오기

2. **네트워크 동기화** (향후 구현 가능)
   - HTTP API를 통한 직접 동기화
   - 선박 시스템이 메인 시스템에 연결되어 있을 때 자동 동기화

## 사용 방법

### 1. LLM 프로바이더 설정

1. 관리자 계정으로 로그인
2. "LLM 설정" 메뉴 접근
3. "프로바이더 추가" 버튼 클릭
4. 프로바이더 선택 및 API 키 입력
5. 메인 시스템용/선박 시스템용 선택
6. 저장

### 2. 경량 모델 다운로드

1. "모델 관리" 메뉴 접근
2. "사용 가능한 모델" 섹션에서 원하는 모델 선택
3. "다운로드" 버튼 클릭
4. 다운로드 진행률 확인
5. 다운로드 완료 후 사용 가능

### 3. RAG 동기화

#### 내보내기 (메인 시스템)
1. "RAG 동기화" 메뉴 접근
2. "내보내기" 버튼 클릭
3. 타겟 시스템 식별자 입력 (예: ship-001)
4. 내보내기 실행
5. 내보낸 파일 경로 확인 (일반적으로 `data/vector_db/exports/{sync_id}/`)

#### 가져오기 (선박 시스템)
1. 메인 시스템에서 내보낸 파일을 선박 시스템으로 복사
2. "RAG 동기화" 메뉴 접근
3. "가져오기" 버튼 클릭
4. 내보낸 파일 경로 입력
5. 가져오기 실행

## 기술 구현

### 백엔드

#### LLM 프로바이더 추상화
- `app/ai/llm_providers.py`: 프로바이더 인터페이스 및 구현
- `app/services/llm_service.py`: LLM 서비스 (프로바이더 선택 및 관리)
- `app/services/provider_service.py`: 프로바이더 CRUD 서비스

#### API 키 암호화
- `cryptography` 라이브러리 사용
- Fernet 대칭키 암호화
- 환경 변수 `ENCRYPTION_KEY`로 암호화 키 관리

#### 모델 관리
- `app/services/model_service.py`: Ollama 모델 관리
- `app/api/models.py`: 모델 관리 API

#### RAG 동기화
- `app/services/rag_sync_service.py`: RAG 동기화 로직
- `app/api/rag_sync.py`: RAG 동기화 API

### 프론트엔드

#### 관리자 페이지
- `LLMSettingsPage.tsx`: LLM 프로바이더 설정
- `ModelManagementPage.tsx`: 경량 모델 관리
- `RAGSyncPage.tsx`: RAG 동기화

## 데이터베이스 스키마

### llm_providers 테이블
- `id`: 프로바이더 ID
- `provider_name`: 프로바이더명 (openai, claude, gemini, perplexity, ollama)
- `api_key`: 암호화된 API 키
- `base_url`: API 베이스 URL
- `model_name`: 기본 모델명
- `is_active`: 활성 여부
- `is_main_system`: 메인 시스템용 여부
- `config`: 추가 설정 (JSON)

### local_models 테이블
- `id`: 모델 ID
- `model_name`: 모델명
- `model_type`: 모델 타입 (ollama 등)
- `model_size`: 모델 크기
- `is_downloaded`: 다운로드 완료 여부
- `download_progress`: 다운로드 진행률

### rag_sync 테이블
- `id`: 동기화 ID
- `sync_type`: 동기화 타입 (export, import)
- `source_system`: 소스 시스템 식별자
- `target_system`: 타겟 시스템 식별자
- `vector_db_path`: 벡터 DB 경로
- `metadata_path`: 메타데이터 경로
- `status`: 상태 (pending, in_progress, completed, failed)
- `progress`: 진행률
- `error_message`: 오류 메시지

## 보안 고려사항

1. **API 키 암호화**: 모든 API 키는 암호화되어 저장
2. **관리자 전용**: LLM 설정, 모델 관리, RAG 동기화는 관리자만 접근 가능
3. **환경 변수**: 암호화 키는 환경 변수로 관리

## 향후 개선 사항

1. **네트워크 동기화**: HTTP API를 통한 직접 동기화
2. **자동 동기화**: 주기적 자동 동기화 스케줄링
3. **동기화 압축**: 대용량 데이터 압축 지원
4. **증분 동기화**: 변경된 부분만 동기화
5. **동기화 검증**: 동기화 데이터 무결성 검증

