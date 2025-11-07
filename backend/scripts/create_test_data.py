"""
테스트 데이터 생성 스크립트
스키마 -> 기능 함수 -> API -> 화면 동작 테스트를 위한 샘플 데이터 생성
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.database import (
    User, Document, DocumentChunk, Permission, 
    LLMProvider, LocalModel, ChatConversation, ChatMessage
)
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.provider_service import ProviderService
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
import tempfile
from datetime import datetime

# 파서는 선택적으로 import (패키지가 없을 수 있음)
try:
    from app.parsers.parser_factory import ParserFactory
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    print("⚠ 파서 모듈을 사용할 수 없습니다. 문서 파싱은 건너뜁니다.")


def create_test_data():
    """테스트 데이터 생성"""
    print("=" * 60)
    print("테스트 데이터 생성 시작")
    print("=" * 60)
    
    # 데이터베이스 테이블 생성
    print("\n1. 데이터베이스 테이블 생성...")
    Base.metadata.create_all(bind=engine)
    print("✓ 테이블 생성 완료")
    
    db = SessionLocal()
    
    try:
        # 1. 사용자 생성
        print("\n2. 테스트 사용자 생성...")
        auth_service = AuthService(db)
        
        # 관리자 계정
        try:
            admin = auth_service.create_user(
                username="admin",
                email="admin@hmm.com",
                password="admin123",
                role="admin"
            )
            print(f"✓ 관리자 계정 생성: {admin.username}")
        except:
            admin = db.query(User).filter(User.username == "admin").first()
            print(f"✓ 관리자 계정 이미 존재: {admin.username}")
        
        # 일반 사용자
        try:
            user1 = auth_service.create_user(
                username="user1",
                email="user1@hmm.com",
                password="user123",
                role="user"
            )
            print(f"✓ 사용자 생성: {user1.username}")
        except:
            user1 = db.query(User).filter(User.username == "user1").first()
            print(f"✓ 사용자 이미 존재: {user1.username}")
        
        # 2. LLM 프로바이더 설정
        print("\n3. LLM 프로바이더 설정...")
        provider_service = ProviderService(db)
        
        # Ollama 프로바이더 (선박 시스템용)
        try:
            ollama_provider = provider_service.create_or_update_provider(
                provider_name="ollama",
                base_url="http://localhost:11434",
                model_name="llama2:7b",
                is_main_system=False
            )
            print(f"✓ Ollama 프로바이더 생성: {ollama_provider.provider_name}")
        except Exception as e:
            print(f"  Ollama 프로바이더: {e}")
        
        # OpenAI 프로바이더 (메인 시스템용, API 키는 테스트용)
        try:
            openai_provider = provider_service.create_or_update_provider(
                provider_name="openai",
                api_key="sk-test-key-placeholder",  # 실제 사용 시 변경 필요
                model_name="gpt-3.5-turbo",
                is_main_system=True
            )
            print(f"✓ OpenAI 프로바이더 생성: {openai_provider.provider_name}")
        except Exception as e:
            print(f"  OpenAI 프로바이더: {e}")
        
        # 3. 테스트 문서 생성
        print("\n4. 테스트 문서 생성...")
        doc_service = DocumentService(db)
        
        # 텍스트 파일 생성 및 업로드
        test_docs = [
            {
                "filename": "test_document_1.txt",
                "content": """HMM 선박 운항 매뉴얼

1. 선박 개요
HMM 선박은 최신 기술을 적용한 컨테이너 선박입니다.
총 적재 용량은 20,000 TEU이며, 최대 속도는 24노트입니다.

2. 안전 규정
- 모든 승무원은 안전 장비를 착용해야 합니다.
- 비상 상황 시 즉시 대피 절차를 따라야 합니다.
- 정기적인 안전 점검을 실시합니다.

3. 운항 절차
- 출항 전 엔진 점검 필수
- 항로 계획 수립
- 기상 정보 확인
- 연료 상태 점검"""
            },
            {
                "filename": "test_document_2.txt",
                "content": """HMM 선박 유지보수 가이드

1. 엔진 유지보수
- 매일 엔진 오일 레벨 확인
- 주간 필터 교체
- 월간 전체 점검

2. 전기 시스템
- 배터리 상태 모니터링
- 발전기 정기 점검
- 배전반 안전 확인

3. 선체 유지보수
- 부식 방지 도료 정기 도포
- 선체 청소 및 검사
- 프로펠러 점검"""
            },
            {
                "filename": "test_document_3.txt",
                "content": """HMM 선박 비상 대응 매뉴얼

1. 화재 대응
- 화재 감지 시 즉시 알람 작동
- 소화기 사용 방법 숙지
- 대피 경로 확인

2. 기관 고장 대응
- 비상 발전기 가동
- 예비 부품 확인
- 육상 지원 연락

3. 기상 악화 대응
- 폭풍 경보 시 안전한 항로로 변경
- 화물 고정 강화
- 승무원 안전 확보"""
            }
        ]
        
        uploaded_docs = []
        for doc_data in test_docs:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(doc_data["content"])
                temp_path = f.name
            
            try:
                # 문서 업로드
                document = doc_service.upload_document(
                    file_path=temp_path,
                    filename=doc_data["filename"],
                    user_id=admin.id
                )
                print(f"✓ 문서 업로드: {document.filename}")
                
                # 문서 파싱 (파서가 사용 가능한 경우만)
                if PARSER_AVAILABLE:
                    try:
                        document = doc_service.parse_document(document.id)
                        print(f"  ✓ 문서 파싱 완료: {document.filename}")
                        
                        # 문서 인덱싱 (벡터화)
                        try:
                            document = doc_service.index_document(document.id)
                            print(f"  ✓ 문서 인덱싱 완료: {document.filename}")
                            uploaded_docs.append(document)
                        except Exception as e:
                            print(f"  ⚠ 인덱싱 오류: {e}")
                    except Exception as e:
                        print(f"  ⚠ 파싱 오류: {e}")
                else:
                    print(f"  ⚠ 파서 미사용: 문서 파싱 건너뜀")
                    uploaded_docs.append(document)
            except Exception as e:
                print(f"  ⚠ 업로드 오류: {e}")
            finally:
                # 임시 파일 삭제
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # 4. 권한 설정
        print("\n5. 권한 설정...")
        from app.services.permission_service import PermissionService
        permission_service = PermissionService(db)
        
        if uploaded_docs:
            # user1에게 첫 번째 문서 읽기 권한 부여
            try:
                permission = permission_service.set_permission(
                    document_id=uploaded_docs[0].id,
                    user_id=user1.id,
                    permission_type="read"
                )
                print(f"✓ 권한 설정: user1 -> {uploaded_docs[0].filename} (read)")
            except Exception as e:
                print(f"  권한 설정 오류: {e}")
        
        # 5. 채팅 대화 생성
        print("\n6. 테스트 채팅 대화 생성...")
        chat_service = ChatService(db)
        
        try:
            conversation = chat_service.create_conversation(
                user_id=admin.id,
                title="테스트 대화",
                use_rag=True,
                use_main_system=False,
                provider_name="ollama"
            )
            
            # 테스트 메시지 추가
            chat_service.add_message(
                conversation_id=conversation.id,
                role="user",
                content="HMM 선박의 안전 규정에 대해 알려주세요."
            )
            
            chat_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content="HMM 선박의 안전 규정은 다음과 같습니다:\n\n1. 모든 승무원은 안전 장비를 착용해야 합니다.\n2. 비상 상황 시 즉시 대피 절차를 따라야 합니다.\n3. 정기적인 안전 점검을 실시합니다.",
                provider="ollama"
            )
            
            print(f"✓ 채팅 대화 생성: {conversation.title}")
        except Exception as e:
            print(f"  채팅 대화 생성 오류: {e}")
        
        # 6. 로컬 모델 정보 추가
        print("\n7. 로컬 모델 정보 추가...")
        try:
            local_model = LocalModel(
                model_name="llama2:7b",
                model_type="ollama",
                is_downloaded=True,
                download_progress=100,
                metadata={"size": "3.8GB", "quantized": False}
            )
            db.add(local_model)
            db.commit()
            print(f"✓ 로컬 모델 정보 추가: {local_model.model_name}")
        except Exception as e:
            print(f"  로컬 모델 정보 추가 오류: {e}")
        
        print("\n" + "=" * 60)
        print("테스트 데이터 생성 완료!")
        print("=" * 60)
        print("\n생성된 데이터:")
        print(f"  - 사용자: {db.query(User).count()}명")
        print(f"  - 문서: {db.query(Document).count()}개")
        print(f"  - 문서 청크: {db.query(DocumentChunk).count()}개")
        print(f"  - LLM 프로바이더: {db.query(LLMProvider).count()}개")
        print(f"  - 채팅 대화: {db.query(ChatConversation).count()}개")
        print(f"  - 채팅 메시지: {db.query(ChatMessage).count()}개")
        print(f"  - 로컬 모델: {db.query(LocalModel).count()}개")
        print("\n테스트 계정:")
        print("  관리자: admin / admin123")
        print("  사용자: user1 / user123")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()

