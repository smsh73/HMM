# GenAI 활용 문서 요약/검색 시스템

HMM㈜의 선박 환경을 위한 온/오프라인 문서 검색 및 요약 시스템입니다.

## 프로젝트 구조

```
HMM/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 라우터
│   │   ├── core/           # 핵심 설정
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── services/       # 비즈니스 로직
│   │   ├── parsers/        # 문서 파서
│   │   ├── ai/             # AI/ML 모듈
│   │   └── utils/          # 유틸리티
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React + TypeScript 프론트엔드
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── services/       # API 서비스
│   │   ├── hooks/          # 커스텀 훅
│   │   ├── store/          # 상태 관리
│   │   └── utils/          # 유틸리티
│   ├── package.json
│   └── tsconfig.json
├── docs/                   # 문서
├── ARCHITECTURE.md         # 아키텍처 설계 문서
└── SETUP_GUIDE.md          # 설치 및 실행 가이드
```

## 기술 스택

### Backend
- FastAPI
- SQLAlchemy
- LangChain
- sentence-transformers
- FAISS
- Ollama

### Frontend
- React 18+
- TypeScript
- Material-UI
- React Query
- React Router

## 빠른 시작

자세한 설치 및 실행 방법은 `SETUP_GUIDE.md`를 참조하세요.

### 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

## 주요 기능

1. **문서 업로드 및 파싱**: PDF, Word, Excel 지원
2. **RAG 기반 검색**: 의미 기반 문서 검색
3. **문서 요약**: LLM 기반 자동 요약
4. **권한 관리**: 문서 단위 접근 제어
5. **성능 모니터링**: 리소스 사용량 추적

## 개발 단계

현재 프로젝트는 Phase 1 (프로젝트 초기 설정) 단계입니다.

## 라이선스

HMM㈜ 내부 사용

