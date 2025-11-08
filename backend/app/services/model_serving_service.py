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


class ModelServingService:
    """로컬 모델 서빙 서비스"""
    
    def __init__(self, db: Session):
        """모델 서빙 서비스 초기화"""
        self.db = db
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.serving_models = {}  # {model_id: process}
    
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
        """Transformers 모델 서빙 시작 (향후 구현)"""
        # Transformers 모델은 직접 서빙하기보다는
        # Ollama로 변환하거나 별도 서빙 서버 필요
        return {
            "status": "not_implemented",
            "message": "Transformers 모델 직접 서빙은 향후 구현 예정입니다."
        }
    
    async def stop_serving(self, model_id: str) -> Dict[str, Any]:
        """모델 서빙 중지"""
        if model_id in self.serving_models:
            process = self.serving_models[model_id]
            process.terminate()
            del self.serving_models[model_id]
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
                    "model": model_id
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"모델 테스트 오류: {str(e)}"
            }

