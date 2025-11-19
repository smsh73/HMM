"""
델타 동기화 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from fastapi import UploadFile, File, Form
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.delta_service import DeltaService
from app.services.system_role_service import SystemRoleService
from app.services.file_transfer_service import FileTransferService
from app.models.database import User
from app.core.websocket_manager import websocket_manager
import os
import tempfile

router = APIRouter(prefix="/delta-sync", tags=["델타 동기화"])


class CreateDeltaRequest(BaseModel):
    document_ids: List[str]
    package_type: str = "document_add"  # document_add, document_update, document_delete


class SendDeltaRequest(BaseModel):
    package_id: str
    send_type: str = "immediate"  # immediate, scheduled
    scheduled_at: Optional[datetime] = None


@router.post("/create")
async def create_delta_package(
    request: CreateDeltaRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """델타 패키지 생성"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 생성할 수 있습니다."
        )
    
    delta_service = DeltaService(db)
    
    try:
        result = delta_service.create_delta_package(
            document_ids=request.document_ids,
            package_type=request.package_type
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/pending")
async def get_pending_deltas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전송 대기 중인 델타 패키지 조회"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 조회할 수 있습니다."
        )
    
    delta_service = DeltaService(db)
    packages = delta_service.get_pending_deltas()
    
    return {"packages": packages}


@router.post("/send")
async def send_delta_package(
    request: SendDeltaRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """델타 패키지 전송 (즉시 또는 스케줄)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 전송할 수 있습니다."
        )
    
    transfer_service = FileTransferService(db)
    
    try:
        result = await transfer_service.send_delta_package(
            package_id=request.package_id,
            send_type=request.send_type
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"전송 실패: {str(e)}"
        )


@router.post("/receive")
async def receive_delta_package(
    file: UploadFile = File(...),
    package_id: str = Form(...),
    checksum: str = Form(...),
    file_size: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """델타 패키지 수신 (선박 클라이언트)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 수신할 수 있습니다."
        )
    
    # 임시 파일로 저장
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"delta_{package_id}.zip")
    
    try:
        # 파일 저장
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 전송 서비스로 수신 처리
        transfer_service = FileTransferService(db)
        result = await transfer_service.receive_delta_package(
            file_path=temp_file_path,
            package_id=package_id,
            checksum=checksum,
            file_size=file_size
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"수신 실패: {str(e)}"
        )
    finally:
        # 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트 (실시간 이벤트)"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (필요한 경우)
            data = await websocket.receive_text()
            # 필요시 처리 로직 추가
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

