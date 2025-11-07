"""
AI 채팅 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
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
    llm_service = LLMService(db)
    search_service = SearchService(db)
    
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
        
        # 대화 ID 생성 (간단한 구현)
        conversation_id = request.conversation_id or f"conv_{datetime.utcnow().timestamp()}"
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            sources=sources,
            provider=request.provider_name or "default"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"답변 생성 오류: {str(e)}"
        )


@router.get("/history")
async def get_chat_history(
    conversation_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅 기록 조회 (향후 구현)"""
    # 채팅 기록 저장 기능은 향후 구현
    return {"messages": []}

