#!/bin/bash

# 통합 테스트 실행 스크립트
# 스키마 -> 기능 함수 -> API -> 화면 동작 전체 테스트

echo "=========================================="
echo "HMM GenAI 시스템 통합 테스트"
echo "=========================================="

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 데이터베이스 초기화 및 테스트 데이터 생성
echo -e "\n${YELLOW}[1단계] 테스트 데이터 생성${NC}"
cd "$(dirname "$0")/.."
python scripts/create_test_data.py

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 테스트 데이터 생성 실패${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 테스트 데이터 생성 완료${NC}"

# 2. 서버 실행 확인
echo -e "\n${YELLOW}[2단계] 서버 실행 확인${NC}"
SERVER_URL="http://localhost:8000"

if curl -s "$SERVER_URL/health" > /dev/null; then
    echo -e "${GREEN}✓ 서버가 실행 중입니다${NC}"
else
    echo -e "${RED}✗ 서버가 실행되지 않았습니다${NC}"
    echo "서버를 시작하려면: cd backend && uvicorn app.main:app --reload"
    exit 1
fi

# 3. API 플로우 테스트
echo -e "\n${YELLOW}[3단계] API 플로우 테스트${NC}"
python scripts/test_api_flow.py "$SERVER_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ API 테스트 실패${NC}"
    exit 1
fi

echo -e "\n${GREEN}=========================================="
echo "통합 테스트 완료!"
echo "==========================================${NC}"
echo ""
echo "다음 단계:"
echo "1. 프론트엔드 실행: cd frontend && npm start"
echo "2. 브라우저에서 http://localhost:3000 접속"
echo "3. 테스트 계정으로 로그인:"
echo "   - 관리자: admin / admin123"
echo "   - 사용자: user1 / user123"

