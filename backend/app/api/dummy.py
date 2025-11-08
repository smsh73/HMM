"""
AI 기능 비활성화 시 더미 응답 제공
"""
from fastapi import APIRouter, Depends
from typing import List
from app.api.dependencies import get_current_user
from app.models.database import User

router = APIRouter()


@router.get("/documents")
async def get_documents(
    current_user: User = Depends(get_current_user)
):
    """문서 목록 조회 (더미)"""
    return {
        "documents": [],
        "total": 0,
        "message": "AI/ML 라이브러리가 설치되지 않아 문서 기능이 비활성화되었습니다."
    }


@router.get("/models/available")
async def get_available_models(
    current_user: User = Depends(get_current_user)
):
    """사용 가능한 모델 목록 (더미)"""
    return {
        "models": [],
        "message": "AI/ML 라이브러리가 설치되지 않아 모델 기능이 비활성화되었습니다."
    }


@router.get("/models/local")
async def get_local_models(
    current_user: User = Depends(get_current_user)
):
    """로컬 모델 목록 (더미)"""
    return {
        "models": [],
        "message": "AI/ML 라이브러리가 설치되지 않아 모델 기능이 비활성화되었습니다."
    }
