"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
import os
import traceback
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.api.router import api_router

# FastAPI 앱 생성
app = FastAPI(
    title="GenAI 문서 검색/요약 시스템",
    description="HMM㈜ 선박 환경용 문서 검색 및 요약 시스템",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api")

# 정적 파일 서빙 (업로드된 문서)
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 프론트엔드 정적 파일 서빙
FRONTEND_BUILD_DIR = Path(__file__).parent.parent.parent / "frontend" / "build"
if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD_DIR / "static")), name="static")


# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "서버 내부 오류가 발생했습니다.",
            "error": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 오류 처리"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """프론트엔드 SPA 서빙"""
    if FRONTEND_BUILD_DIR.exists():
        file_path = FRONTEND_BUILD_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")
    return {
        "message": "GenAI 문서 검색/요약 시스템 API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

