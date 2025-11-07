"""
API 라우터 통합
"""
from fastapi import APIRouter

from app.api import auth, documents, search, summary, permissions, performance, llm_settings, models, rag_sync, huggingface, model_serving, chat

api_router = APIRouter()

# 라우터 등록
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(summary.router)
api_router.include_router(permissions.router)
api_router.include_router(performance.router)
api_router.include_router(llm_settings.router)
api_router.include_router(models.router)
api_router.include_router(rag_sync.router)
api_router.include_router(huggingface.router)
api_router.include_router(model_serving.router)
api_router.include_router(chat.router)

