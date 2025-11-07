"""
요약 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.schemas import SummaryRequest, SummaryResponse
from app.services.summary_service import SummaryService
from app.services.permission_service import PermissionService
from app.models.database import User

router = APIRouter(prefix="/summary", tags=["요약"])


@router.post("/documents/{document_id}", response_model=SummaryResponse)
async def summarize_document(
    document_id: str,
    summary_request: SummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """문서 요약 생성"""
    permission_service = PermissionService(db)
    
    # 권한 확인
    if not permission_service.check_permission(current_user.id, document_id, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 문서를 요약할 권한이 없습니다."
        )
    
    summary_service = SummaryService(db)
    
    try:
        result = await summary_service.summarize_document(
            document_id=document_id,
            summary_type=summary_request.summary_type
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

