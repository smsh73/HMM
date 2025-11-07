"""
빠른 테스트 스크립트
의존성 없이 기본 기능만 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.database import User, LLMProvider, ChatConversation, ChatMessage
from app.services.auth_service import AuthService
from app.services.provider_service import ProviderService
from app.services.chat_service import ChatService


def quick_test():
    """빠른 테스트 (의존성 최소화)"""
    print("=" * 60)
    print("빠른 테스트 시작 (의존성 최소화)")
    print("=" * 60)
    
    # SQLite 사용 (테스트용)
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test.db")
    
    # 데이터베이스 테이블 생성
    print("\n1. 데이터베이스 테이블 생성...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ 테이블 생성 완료")
    except Exception as e:
        print(f"⚠ 테이블 생성 오류 (이미 존재할 수 있음): {e}")
    
    db = SessionLocal()
    
    try:
        # 사용자 생성
        print("\n2. 테스트 사용자 생성...")
        auth_service = AuthService(db)
        
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
        
        # LLM 프로바이더 설정
        print("\n3. LLM 프로바이더 설정...")
        provider_service = ProviderService(db)
        
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
        
        # 채팅 대화 생성
        print("\n4. 테스트 채팅 대화 생성...")
        chat_service = ChatService(db)
        
        try:
            conversation = chat_service.create_conversation(
                user_id=admin.id,
                title="테스트 대화",
                use_rag=True,
                use_main_system=False,
                provider_name="ollama"
            )
            
            chat_service.add_message(
                conversation_id=conversation.id,
                role="user",
                content="안녕하세요. 테스트 메시지입니다."
            )
            
            chat_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content="안녕하세요! 테스트에 응답합니다.",
                provider="ollama"
            )
            
            print(f"✓ 채팅 대화 생성: {conversation.title}")
        except Exception as e:
            print(f"  채팅 대화 생성 오류: {e}")
        
        print("\n" + "=" * 60)
        print("빠른 테스트 완료!")
        print("=" * 60)
        print("\n생성된 데이터:")
        print(f"  - 사용자: {db.query(User).count()}명")
        print(f"  - LLM 프로바이더: {db.query(LLMProvider).count()}개")
        print(f"  - 채팅 대화: {db.query(ChatConversation).count()}개")
        print(f"  - 채팅 메시지: {db.query(ChatMessage).count()}개")
        print("\n테스트 계정:")
        print("  관리자: admin / admin123")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    quick_test()

