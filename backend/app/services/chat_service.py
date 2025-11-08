"""
채팅 서비스
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.database import ChatConversation, ChatMessage, User


class ChatService:
    """채팅 서비스"""
    
    def __init__(self, db: Session):
        """채팅 서비스 초기화"""
        self.db = db
    
    def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        use_rag: bool = False,
        use_main_system: bool = True,
        provider_name: Optional[str] = None
    ) -> ChatConversation:
        """대화 생성"""
        conversation = ChatConversation(
            user_id=user_id,
            title=title or "새 대화",
            use_rag=use_rag,
            use_main_system=use_main_system,
            provider_name=provider_name
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        user_id: str,
        use_rag: bool = False,
        use_main_system: bool = True,
        provider_name: Optional[str] = None
    ) -> ChatConversation:
        """대화 조회 또는 생성"""
        if conversation_id:
            conversation = self.db.query(ChatConversation).filter(
                ChatConversation.id == conversation_id,
                ChatConversation.user_id == user_id
            ).first()
            if conversation:
                return conversation
        
        return self.create_conversation(
            user_id=user_id,
            use_rag=use_rag,
            use_main_system=use_main_system,
            provider_name=provider_name
        )
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[str] = None
    ) -> ChatMessage:
        """메시지 추가"""
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            provider=provider
        )
        self.db.add(message)
        
        # 대화 제목 업데이트 (첫 사용자 메시지 기반)
        if role == "user":
            conversation = self.db.query(ChatConversation).filter(
                ChatConversation.id == conversation_id
            ).first()
            if conversation and not conversation.title or conversation.title == "새 대화":
                # 첫 50자로 제목 설정
                conversation.title = content[:50] + ("..." if len(content) > 50 else "")
                conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """사용자의 대화 목록 조회"""
        conversations = self.db.query(ChatConversation).filter(
            ChatConversation.user_id == user_id
        ).order_by(
            ChatConversation.updated_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": c.id,
                "title": c.title,
                "use_rag": c.use_rag,
                "use_main_system": c.use_main_system,
                "provider_name": c.provider_name,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "message_count": len(c.messages)
            }
            for c in conversations
        ]
    
    def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """대화의 메시지 목록 조회"""
        # 권한 확인
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user_id
        ).first()
        
        if not conversation:
            return []
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(
            ChatMessage.created_at.asc()
        ).limit(limit).all()
        
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "provider": m.provider,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]
    
    def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """대화 삭제"""
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user_id
        ).first()
        
        if not conversation:
            return False
        
        self.db.delete(conversation)
        self.db.commit()
        return True

