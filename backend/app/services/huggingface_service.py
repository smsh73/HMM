"""
Hugging Face 모델 관리 서비스
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from huggingface_hub import HfApi, list_models, model_info
import os
from pathlib import Path

from app.models.database import LocalModel
from app.core.config import settings


class HuggingFaceService:
    """Hugging Face 모델 관리 서비스"""
    
    def __init__(self, db: Session):
        """Hugging Face 서비스 초기화"""
        self.db = db
        self.api = HfApi()
        self.models_dir = os.path.join(settings.VECTOR_DB_PATH, "models")
        os.makedirs(self.models_dir, exist_ok=True)
    
    async def search_models(
        self,
        query: str = "",
        task: Optional[str] = None,
        library: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """모델 검색"""
        try:
            filters = {}
            if task:
                filters["task"] = task
            if library:
                filters["library"] = library
            
            # 경량 모델 필터링 (7B 파라미터 이하)
            models = list_models(
                search=query,
                limit=limit,
                **filters
            )
            
            results = []
            for model in models:
                try:
                    info = model_info(model.id)
                    # 파라미터 수 확인
                    param_count = getattr(info, 'safetensors', {}).get('total', 0)
                    if param_count == 0:
                        # 대체 방법으로 파라미터 수 추정
                        config = getattr(info, 'config', {})
                        if config:
                            param_count = config.get('num_parameters', 0)
                    
                    # 7B 이하 또는 양자화 모델만 필터링
                    if param_count > 0 and param_count > 7_000_000_000:
                        continue
                    
                    # 양자화 모델 우선 (q4, q8 등 포함)
                    is_quantized = any(
                        tag in model.id.lower() 
                        for tag in ['q4', 'q8', 'quantized', 'gguf', 'ggml']
                    )
                    
                    results.append({
                        "model_id": model.id,
                        "author": model.id.split('/')[0] if '/' in model.id else '',
                        "downloads": getattr(info, 'downloads', 0),
                        "likes": getattr(info, 'likes', 0),
                        "tags": getattr(info, 'tags', []),
                        "task": task or (info.task if hasattr(info, 'task') else None),
                        "library": library or (info.library_name if hasattr(info, 'library_name') else None),
                        "param_count": param_count,
                        "is_quantized": is_quantized,
                        "size": self._estimate_model_size(param_count),
                    })
                except Exception as e:
                    print(f"모델 정보 조회 오류 ({model.id}): {e}")
                    continue
            
            # 양자화 모델 우선 정렬
            results.sort(key=lambda x: (not x['is_quantized'], -x['downloads']))
            
            return results[:limit]
        except Exception as e:
            print(f"모델 검색 오류: {e}")
            return []
    
    def _estimate_model_size(self, param_count: int) -> str:
        """모델 크기 추정"""
        if param_count == 0:
            return "Unknown"
        
        # 대략적인 크기 추정 (FP16 기준)
        size_gb = (param_count * 2) / (1024 ** 3)
        
        if size_gb < 1:
            return f"{size_gb * 1024:.1f} MB"
        else:
            return f"{size_gb:.2f} GB"
    
    async def download_model(
        self,
        model_id: str,
        model_type: str = "transformers"
    ) -> Dict[str, Any]:
        """모델 다운로드"""
        # 데이터베이스에 모델 정보 저장
        local_model = self.db.query(LocalModel).filter(
            LocalModel.model_name == model_id
        ).first()
        
        if not local_model:
            local_model = LocalModel(
                model_name=model_id,
                model_type=model_type,
                is_downloaded=False,
                download_progress=0,
                metadata={"source": "huggingface"}
            )
            self.db.add(local_model)
        else:
            if local_model.is_downloaded:
                return {
                    "status": "already_downloaded",
                    "model": model_id,
                    "message": "모델이 이미 다운로드되어 있습니다."
                }
        
        self.db.commit()
        
        try:
            from huggingface_hub import snapshot_download
            import asyncio
            
            # 모델 다운로드 경로
            model_path = os.path.join(self.models_dir, model_id.replace("/", "_"))
            
            # 비동기 다운로드
            async def download():
                try:
                    snapshot_download(
                        repo_id=model_id,
                        local_dir=model_path,
                        local_dir_use_symlinks=False
                    )
                    local_model.is_downloaded = True
                    local_model.download_progress = 100
                    local_model.metadata = {
                        **local_model.metadata,
                        "model_path": model_path
                    }
                    self.db.commit()
                except Exception as e:
                    local_model.download_progress = 0
                    local_model.metadata = {
                        **local_model.metadata,
                        "error": str(e)
                    }
                    self.db.commit()
                    raise
            
            # 백그라운드에서 다운로드 시작
            asyncio.create_task(download())
            
            return {
                "status": "downloading",
                "model": model_id,
                "message": "모델 다운로드가 시작되었습니다.",
                "model_path": model_path
            }
        except Exception as e:
            local_model.download_progress = 0
            self.db.commit()
            return {
                "status": "error",
                "model": model_id,
                "error": str(e)
            }
    
    def get_downloaded_models(self) -> List[Dict[str, Any]]:
        """다운로드된 모델 목록 조회"""
        models = self.db.query(LocalModel).filter(
            LocalModel.model_type.in_(["transformers", "huggingface"])
        ).all()
        
        return [
            {
                "id": m.id,
                "model_id": m.model_name,
                "model_type": m.model_type,
                "is_downloaded": m.is_downloaded,
                "download_progress": m.download_progress,
                "metadata": m.metadata,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in models
        ]

