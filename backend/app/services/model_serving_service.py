"""
로컬 모델 서빙 서비스
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import httpx
import subprocess
import os
import json
from pathlib import Path

from app.models.database import LocalModel
from app.core.config import settings
from app.ai.local_slm import LocalSLMProvider

# 모듈 레벨 싱글톤: 모든 서비스 인스턴스가 공유하는 서빙 모델 레지스트리
_SERVING_MODELS_REGISTRY: Dict[str, Any] = {}


class ModelServingService:
    """로컬 모델 서빙 서비스"""
    
    def __init__(self, db: Session):
        """모델 서빙 서비스 초기화"""
        self.db = db
        self.ollama_url = settings.OLLAMA_BASE_URL
        # 모듈 레벨 레지스트리 사용 (모든 인스턴스가 공유)
        self.serving_models = _SERVING_MODELS_REGISTRY
    
    async def start_serving(
        self,
        model_id: str,
        model_type: str = "ollama"
    ) -> Dict[str, Any]:
        """모델 서빙 시작"""
        if model_type == "ollama":
            return await self._start_ollama_model(model_id)
        elif model_type == "transformers":
            return await self._start_transformers_model(model_id)
        else:
            return {"status": "error", "message": f"지원하지 않는 모델 타입: {model_type}"}
    
    async def _start_ollama_model(self, model_id: str) -> Dict[str, Any]:
        """Ollama 모델 서빙 시작"""
        try:
            # Ollama 서버가 실행 중인지 확인
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": "Ollama 서버가 실행 중이지 않습니다."
                    }
            
            # 모델이 Ollama에 있는지 확인
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                models = response.json().get("models", [])
                model_exists = any(m.get("name") == model_id for m in models)
                
                if not model_exists:
                    return {
                        "status": "error",
                        "message": f"모델 {model_id}가 Ollama에 설치되어 있지 않습니다."
                    }
            
            return {
                "status": "running",
                "model": model_id,
                "message": "모델이 서빙 중입니다.",
                "endpoint": f"{self.ollama_url}/api/generate"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"모델 서빙 시작 오류: {str(e)}"
            }
    
    async def _start_transformers_model(self, model_id: str) -> Dict[str, Any]:
        """Transformers 모델 서빙 시작 (LocalSLMProvider 사용)"""
        try:
            # 이미 서빙 중인지 확인
            if model_id in self.serving_models:
                return {
                    "status": "already_running",
                    "model": model_id,
                    "message": "모델이 이미 서빙 중입니다."
                }
            
            # 다운로드된 모델 확인
            local_model = self.db.query(LocalModel).filter(
                LocalModel.model_name == model_id,
                LocalModel.is_downloaded == True
            ).first()
            
            if not local_model:
                return {
                    "status": "error",
                    "message": f"모델 {model_id}가 다운로드되어 있지 않습니다."
                }
            
            # LocalSLMProvider로 모델 로딩
            try:
                model_path = local_model.model_metadata.get("model_path") if local_model.model_metadata else None
                
                slm_provider = LocalSLMProvider(
                    model_name=model_id,
                    device='cpu',
                    cache_dir=model_path if model_path else None
                )
                
                # 모델 로딩 확인
                if not slm_provider.is_available():
                    return {
                        "status": "error",
                        "message": f"모델 {model_id} 로딩에 실패했습니다."
                    }
                
                # 서빙 모델 등록
                self.serving_models[model_id] = slm_provider
                
                # 데이터베이스 업데이트
                local_model.is_serving = True
                local_model.model_metadata = {
                    **(local_model.model_metadata or {}),
                    "serving_status": "running",
                    "device": "cpu"
                }
                self.db.commit()
                
                return {
                    "status": "running",
                    "model": model_id,
                    "message": "모델 서빙이 시작되었습니다.",
                    "device": "cpu",
                    "model_info": slm_provider.get_model_info()
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"모델 로딩 오류: {str(e)}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"모델 서빙 시작 오류: {str(e)}"
            }
    
    async def stop_serving(self, model_id: str) -> Dict[str, Any]:
        """모델 서빙 중지"""
        if model_id in self.serving_models:
            # LocalSLMProvider 인스턴스 제거
            del self.serving_models[model_id]
            
            # 데이터베이스 업데이트
            local_model = self.db.query(LocalModel).filter(
                LocalModel.model_name == model_id
            ).first()
            
            if local_model:
                local_model.is_serving = False
                if local_model.model_metadata:
                    local_model.model_metadata["serving_status"] = "stopped"
                self.db.commit()
            
            return {
                "status": "stopped",
                "model": model_id,
                "message": "모델 서빙이 중지되었습니다."
            }
        return {
            "status": "not_running",
            "message": f"모델 {model_id}가 서빙 중이 아닙니다."
        }
    
    async def get_serving_status(self) -> List[Dict[str, Any]]:
        """서빙 중인 모델 상태 조회"""
        statuses = []
        
        # Transformers 모델 상태 (메모리에 로딩된 모델)
        for model_id, slm_provider in self.serving_models.items():
            model_info = slm_provider.get_model_info()
            statuses.append({
                "model_id": model_id,
                "model_type": "transformers",
                "status": "running",
                "device": model_info.get("device", "cpu"),
                "loaded": model_info.get("loaded", False),
                "max_tokens": model_info.get("max_new_tokens", 0)
            })
        
        # Ollama 모델 상태 확인
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    for model in models:
                        statuses.append({
                            "model_id": model.get("name", ""),
                            "model_type": "ollama",
                            "status": "running",
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", "")
                        })
        except:
            pass
        
        return statuses
    
    async def test_model(self, model_id: str, prompt: str = "Hello") -> Dict[str, Any]:
        """모델 테스트"""
        # Transformers 모델 테스트
        if model_id in self.serving_models:
            try:
                import asyncio
                slm_provider = self.serving_models[model_id]
                # generate는 async 함수이므로 await 사용
                response = await slm_provider.generate(prompt, max_tokens=50)
                return {
                    "status": "success",
                    "response": response,
                    "model": model_id,
                    "model_type": "transformers"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"모델 테스트 오류: {str(e)}"
                }
        
        # Ollama 모델 테스트
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model_id,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return {
                    "status": "success",
                    "response": result.get("response", ""),
                    "model": model_id,
                    "model_type": "ollama"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"모델 테스트 오류: {str(e)}"
            }

