"""
로컬 모델 관리 서비스
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx
import asyncio

from app.models.database import LocalModel
from app.core.config import settings


class ModelService:
    """로컬 모델 관리 서비스"""
    
    def __init__(self, db: Session):
        """모델 서비스 초기화"""
        self.db = db
        self.ollama_url = settings.OLLAMA_BASE_URL
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """사용 가능한 모델 목록 조회 (Ollama)"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Ollama에서 사용 가능한 모델 목록 가져오기
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                models = []
                for model in data.get("models", []):
                    models.append({
                        "name": model.get("name", ""),
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "digest": model.get("digest", "")
                    })
                
                return models
        except Exception as e:
            print(f"모델 목록 조회 오류: {e}")
            return []
    
    async def download_model(self, model_name: str, auto_serve: bool = False) -> Dict[str, Any]:
        """모델 다운로드"""
        # 데이터베이스에 모델 정보 저장
        local_model = self.db.query(LocalModel).filter(
            LocalModel.model_name == model_name
        ).first()
        
        if not local_model:
            local_model = LocalModel(
                model_name=model_name,
                model_type="ollama",
                is_downloaded=False,
                download_progress=0,
                model_metadata={}
            )
            self.db.add(local_model)
        else:
            if local_model.is_downloaded:
                return {"status": "already_downloaded", "model": model_name}
        
        self.db.commit()
        
        try:
            # Ollama를 통한 모델 다운로드
            async with httpx.AsyncClient(timeout=300.0) as client:
                async def download_stream():
                    async with client.stream(
                        "POST",
                        f"{self.ollama_url}/api/pull",
                        json={"name": model_name}
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                import json
                                try:
                                    data = json.loads(line)
                                    if "completed" in data and data["completed"]:
                                        local_model.is_downloaded = True
                                        local_model.download_progress = 100
                                        self.db.commit()
                                        
                                        # 자동 서빙 시작
                                        if auto_serve:
                                            try:
                                                from app.services.model_serving_service import ModelServingService
                                                serving_service = ModelServingService(self.db)
                                                await serving_service.start_serving(
                                                    model_id=model_name,
                                                    model_type="ollama"
                                                )
                                            except Exception as e:
                                                print(f"자동 서빙 시작 오류: {e}")
                                except:
                                    pass
            
            # 백그라운드에서 다운로드 실행
            asyncio.create_task(download_stream())
            
            return {
                "status": "downloading",
                "model": model_name,
                "message": "모델 다운로드가 시작되었습니다."
            }
        except Exception as e:
            local_model.download_progress = 0
            self.db.commit()
            return {
                "status": "error",
                "model": model_name,
                "error": str(e)
            }
    
    def get_local_models(self) -> List[Dict[str, Any]]:
        """로컬 모델 목록 조회"""
        models = self.db.query(LocalModel).all()
        return [
            {
                "id": m.id,
                "model_name": m.model_name,
                "model_type": m.model_type,
                "model_size": m.model_size,
                "is_downloaded": m.is_downloaded,
                "download_progress": m.download_progress,
                "metadata": m.model_metadata,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None
            }
            for m in models
        ]
    
    def delete_model(self, model_id: str) -> bool:
        """모델 삭제"""
        model = self.db.query(LocalModel).filter(LocalModel.id == model_id).first()
        if not model:
            return False
        
        # Ollama에서 모델 삭제 시도
        try:
            import httpx
            with httpx.Client(timeout=10.0) as client:
                client.delete(
                    f"{self.ollama_url}/api/delete",
                    json={"name": model.model_name}
                )
        except:
            pass
        
        self.db.delete(model)
        self.db.commit()
        return True

