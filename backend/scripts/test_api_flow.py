"""
API 플로우 테스트 스크립트
스키마 -> 기능 함수 -> API 전체 플로우 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from typing import Dict, Any


class APITester:
    """API 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
    
    def print_step(self, step: int, description: str):
        """단계 출력"""
        print(f"\n{'='*60}")
        print(f"단계 {step}: {description}")
        print('='*60)
    
    def test_auth(self) -> bool:
        """인증 테스트"""
        self.print_step(1, "인증 테스트")
        
        # 로그인
        print("\n1-1. 로그인...")
        response = requests.post(
            f"{self.api_base}/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print(f"✓ 로그인 성공")
            print(f"  토큰: {self.token[:50]}...")
            
            # 사용자 정보 조회
            print("\n1-2. 사용자 정보 조회...")
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_base}/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data["id"]
                print(f"✓ 사용자 정보 조회 성공")
                print(f"  사용자명: {user_data['username']}")
                print(f"  역할: {user_data['role']}")
                return True
            else:
                print(f"✗ 사용자 정보 조회 실패: {response.status_code}")
                return False
        else:
            print(f"✗ 로그인 실패: {response.status_code}")
            print(f"  응답: {response.text}")
            return False
    
    def test_documents(self) -> bool:
        """문서 관리 테스트"""
        self.print_step(2, "문서 관리 테스트")
        
        if not self.token:
            print("✗ 인증 토큰이 없습니다.")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 문서 목록 조회
        print("\n2-1. 문서 목록 조회...")
        response = requests.get(f"{self.api_base}/documents", headers=headers)
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✓ 문서 목록 조회 성공: {len(documents)}개 문서")
            
            if documents:
                doc = documents[0]
                print(f"  첫 번째 문서: {doc['filename']}")
                print(f"  파싱 상태: {'완료' if doc['is_parsed'] else '미완료'}")
                print(f"  인덱싱 상태: {'완료' if doc['is_indexed'] else '미완료'}")
                return True
            else:
                print("  ⚠ 문서가 없습니다.")
                return False
        else:
            print(f"✗ 문서 목록 조회 실패: {response.status_code}")
            return False
    
    def test_search(self) -> bool:
        """검색 테스트"""
        self.print_step(3, "검색 테스트")
        
        if not self.token:
            print("✗ 인증 토큰이 없습니다.")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 의미 기반 검색
        print("\n3-1. 의미 기반 검색...")
        search_data = {
            "query": "안전 규정",
            "top_k": 3,
            "generate_answer": False
        }
        response = requests.post(
            f"{self.api_base}/search",
            headers=headers,
            json=search_data
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✓ 검색 성공: {results['total_results']}개 결과")
            
            for i, result in enumerate(results['results'][:3], 1):
                print(f"\n  결과 {i}:")
                print(f"    점수: {result['score']:.3f}")
                print(f"    내용: {result['content'][:100]}...")
            return True
        else:
            print(f"✗ 검색 실패: {response.status_code}")
            print(f"  응답: {response.text}")
            return False
    
    def test_search_with_answer(self) -> bool:
        """답변 생성 검색 테스트"""
        self.print_step(4, "RAG 기반 답변 생성 테스트")
        
        if not self.token:
            print("✗ 인증 토큰이 없습니다.")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # RAG 기반 답변 생성
        print("\n4-1. RAG 기반 답변 생성...")
        search_data = {
            "query": "선박 엔진 유지보수 방법",
            "top_k": 3,
            "generate_answer": True,
            "use_main_system": False  # Ollama 사용
        }
        
        print("  검색 중... (시간이 걸릴 수 있습니다)")
        response = requests.post(
            f"{self.api_base}/search",
            headers=headers,
            json=search_data,
            timeout=60
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✓ 검색 및 답변 생성 성공")
            
            if results.get('answer'):
                answer = results['answer']
                print(f"\n  생성된 답변:")
                print(f"  {answer['answer'][:200]}...")
                print(f"  신뢰도: {answer['confidence']:.2%}")
                print(f"  출처 수: {len(answer['sources'])}개")
            return True
        else:
            print(f"✗ 답변 생성 실패: {response.status_code}")
            print(f"  응답: {response.text}")
            return False
    
    def test_chat(self) -> bool:
        """채팅 테스트"""
        self.print_step(5, "AI 채팅 테스트")
        
        if not self.token:
            print("✗ 인증 토큰이 없습니다.")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 채팅 전송
        print("\n5-1. 채팅 메시지 전송...")
        chat_data = {
            "message": "안전 규정에 대해 알려주세요",
            "use_rag": True,
            "use_main_system": False
        }
        
        print("  AI가 답변을 생성하는 중... (시간이 걸릴 수 있습니다)")
        response = requests.post(
            f"{self.api_base}/chat/",
            headers=headers,
            json=chat_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 채팅 성공")
            print(f"  대화 ID: {result['conversation_id']}")
            print(f"  답변: {result['response'][:200]}...")
            
            # 대화 목록 조회
            print("\n5-2. 대화 목록 조회...")
            response = requests.get(
                f"{self.api_base}/chat/conversations",
                headers=headers
            )
            
            if response.status_code == 200:
                conversations = response.json()["conversations"]
                print(f"✓ 대화 목록 조회 성공: {len(conversations)}개 대화")
                return True
            else:
                print(f"✗ 대화 목록 조회 실패: {response.status_code}")
                return False
        else:
            print(f"✗ 채팅 실패: {response.status_code}")
            print(f"  응답: {response.text}")
            return False
    
    def test_llm_providers(self) -> bool:
        """LLM 프로바이더 테스트"""
        self.print_step(6, "LLM 프로바이더 관리 테스트")
        
        if not self.token:
            print("✗ 인증 토큰이 없습니다.")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 프로바이더 목록 조회
        print("\n6-1. 프로바이더 목록 조회...")
        response = requests.get(
            f"{self.api_base}/llm/providers",
            headers=headers
        )
        
        if response.status_code == 200:
            providers = response.json()["providers"]
            print(f"✓ 프로바이더 목록 조회 성공: {len(providers)}개")
            
            for provider in providers:
                print(f"  - {provider['provider_name']}: {'활성' if provider['is_active'] else '비활성'}")
            return True
        else:
            print(f"✗ 프로바이더 목록 조회 실패: {response.status_code}")
            return False
    
    def test_models(self) -> bool:
        """모델 관리 테스트"""
        self.print_step(7, "모델 관리 테스트")
        
        if not self.token:
            print("✗ 인증 토큰이 없습니다.")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 로컬 모델 목록 조회
        print("\n7-1. 로컬 모델 목록 조회...")
        response = requests.get(
            f"{self.api_base}/models/local",
            headers=headers
        )
        
        if response.status_code == 200:
            models = response.json()["models"]
            print(f"✓ 로컬 모델 목록 조회 성공: {len(models)}개")
            
            for model in models:
                status = "다운로드 완료" if model['is_downloaded'] else "다운로드 중"
                print(f"  - {model['model_name']}: {status}")
            return True
        else:
            print(f"✗ 로컬 모델 목록 조회 실패: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "="*60)
        print("API 플로우 테스트 시작")
        print("="*60)
        print(f"\n테스트 서버: {self.base_url}")
        print("주의: 서버가 실행 중이어야 합니다!")
        
        results = []
        
        # 테스트 실행
        results.append(("인증", self.test_auth()))
        results.append(("문서 관리", self.test_documents()))
        results.append(("검색", self.test_search()))
        results.append(("RAG 답변 생성", self.test_search_with_answer()))
        results.append(("AI 채팅", self.test_chat()))
        results.append(("LLM 프로바이더", self.test_llm_providers()))
        results.append(("모델 관리", self.test_models()))
        
        # 결과 요약
        print("\n" + "="*60)
        print("테스트 결과 요약")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✓ 통과" if result else "✗ 실패"
            print(f"  {name}: {status}")
        
        print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 모든 테스트 통과!")
        else:
            print(f"\n⚠ {total - passed}개 테스트 실패")


if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = APITester(base_url=base_url)
    tester.run_all_tests()

