"""
RAG 동기화 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.rag_sync_service import RAGSyncService
from app.models.database import User

router = APIRouter(prefix="/rag-sync", tags=["RAG 동기화"])


class SyncRequest(BaseModel):
    target_system: str


class ImportRequest(BaseModel):
    sync_id: Optional[str] = None
    source_path: Optional[str] = None


@router.post("/export")
async def export_rag(
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """RAG 데이터 내보내기 (메인 시스템 -> 선박 시스템)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 내보낼 수 있습니다."
        )
    
    sync_service = RAGSyncService(db)
    result = sync_service.export_rag(sync_request.target_system)
    return result


@router.post("/import")
async def import_rag(
    import_request: ImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """RAG 데이터 가져오기 (선박 시스템 <- 메인 시스템)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 가져올 수 있습니다."
        )
    
    sync_service = RAGSyncService(db)
    result = sync_service.import_rag(
        sync_id=import_request.sync_id,
        source_path=import_request.source_path
    )
    return result


@router.get("/history")
async def get_sync_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """동기화 기록 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 조회할 수 있습니다."
        )
    
    sync_service = RAGSyncService(db)
    history = sync_service.get_sync_history(limit=limit)
    return {"history": history}

