"""
AI 채팅 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.logging import logger
from app.api.dependencies import get_current_user
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.services.chat_service import ChatService
from app.models.database import User

router = APIRouter(prefix="/chat", tags=["AI 채팅"])


class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_rag: bool = False
    use_main_system: bool = True
    provider_name: Optional[str] = None
    
    class Config:
        # 입력 검증
        min_length = {"message": 1}
        max_length = {"message": 5000}


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[dict]] = None
    provider: str


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI 채팅"""
    # 입력 검증
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="메시지를 입력하세요."
        )
    
    if len(request.message) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="메시지가 너무 깁니다. (최대 5000자)"
        )
    
    logger.info(f"채팅 요청: 사용자={current_user.username}, RAG={request.use_rag}, 시스템={request.use_main_system}")
    
    llm_service = LLMService(db)
    search_service = SearchService(db)
    chat_service = ChatService(db)
    
    # 대화 조회 또는 생성
    conversation = chat_service.get_or_create_conversation(
        conversation_id=request.conversation_id,
        user_id=current_user.id,
        use_rag=request.use_rag,
        use_main_system=request.use_main_system,
        provider_name=request.provider_name
    )
    
    # 사용자 메시지 저장
    chat_service.add_message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    
    # RAG 사용 시 문서 검색
    context = ""
    sources = None
    if request.use_rag:
        search_results = await search_service.search(
            query=request.message,
            user_id=current_user.id,
            top_k=3,
            generate_answer=False,
            use_main_system=request.use_main_system,
            provider_name=request.provider_name
        )
        
        if search_results.get("results"):
            context = "\n\n참고 문서:\n" + "\n".join([
                f"- {r['content'][:200]}..." 
                for r in search_results["results"][:3]
            ])
            sources = search_results["results"]
    
    # 프롬프트 구성
    prompt = f"""{context}

사용자 질문: {request.message}

답변:"""
    
    # LLM을 통한 답변 생성
    try:
        provider = llm_service.get_provider(
            provider_name=request.provider_name,
            use_main_system=request.use_main_system
        )
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용 가능한 LLM 프로바이더가 없습니다."
            )
        
        response_text = await provider.generate(prompt)
        provider_name = request.provider_name or "default"
        
        # AI 응답 저장
        chat_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            sources=sources,
            provider=provider_name
        )
        
        logger.info(f"채팅 응답 생성 완료: 대화ID={conversation.id}, 프로바이더={provider_name}")
        return ChatResponse(
            response=response_text,
            conversation_id=conversation.id,
            sources=sources,
            provider=provider_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 응답 생성 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="답변 생성 중 오류가 발생했습니다."
        )


@router.get("/conversations")
async def get_conversations(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 대화 목록 조회"""
    chat_service = ChatService(db)
    conversations = chat_service.get_conversations(
        user_id=current_user.id,
        limit=limit
    )
    return {"conversations": conversations}


@router.get("/history")
async def get_chat_history(
    conversation_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅 기록 조회"""
    chat_service = ChatService(db)
    messages = chat_service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit
    )
    return {"messages": messages}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """대화 삭제"""
    chat_service = ChatService(db)
    success = chat_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다."
        )
    return {"message": "대화가 삭제되었습니다."}

