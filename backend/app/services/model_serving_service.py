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
from app.core.logging import logger
from app.ai.local_slm import LocalSLMProvider

# 모듈 레벨 싱글톤: 모든 서비스 인스턴스가 공유하는 서빙 모델 레지스트리
_SERVING_MODELS_REGISTRY: Dict[str, Any] = {}
_CURRENT_SERVING_MODEL: Optional[str] = None  # 현재 서빙 중인 모델 ID (단일 모델 제한)


class ModelServingService:
    """로컬 모델 서빙 서비스 (단일 모델 제한)"""
    
    def __init__(self, db: Session):
        """모델 서빙 서비스 초기화"""
        self.db = db
        self.ollama_url = settings.OLLAMA_BASE_URL
        # 모듈 레벨 레지스트리 사용 (모든 인스턴스가 공유)
        self.serving_models = _SERVING_MODELS_REGISTRY
        self.current_serving_model = _CURRENT_SERVING_MODEL
    
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
        """
        Transformers 모델 서빙 시작 (LocalSLMProvider 사용)
        단일 모델 제한: 이미 다른 모델이 서빙 중이면 자동으로 언로드 후 로드
        """
        global _CURRENT_SERVING_MODEL
        
        try:
            # 이미 서빙 중인지 확인
            if model_id in self.serving_models and _CURRENT_SERVING_MODEL == model_id:
                return {
                    "status": "already_running",
                    "model": model_id,
                    "message": "모델이 이미 서빙 중입니다."
                }
            
            # 다른 모델이 서빙 중인 경우 언로드
            if _CURRENT_SERVING_MODEL and _CURRENT_SERVING_MODEL != model_id:
                logger.info(f"기존 모델 언로드: {_CURRENT_SERVING_MODEL}")
                await self._unload_model(_CURRENT_SERVING_MODEL)
            
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
                
                logger.info(f"모델 로딩 시작: {model_id}")
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
                
                # 서빙 모델 등록 (단일 모델만 유지)
                self.serving_models.clear()  # 기존 모델 제거
                self.serving_models[model_id] = slm_provider
                _CURRENT_SERVING_MODEL = model_id
                self.current_serving_model = model_id
                
                # 데이터베이스 업데이트 (모든 모델의 서빙 상태 초기화 후 현재 모델만 활성화)
                all_models = self.db.query(LocalModel).filter(
                    LocalModel.model_type == "transformers"
                ).all()
                for model in all_models:
                    model.is_serving = (model.model_name == model_id)
                    if model.model_metadata:
                        if model.model_name == model_id:
                            model.model_metadata = {
                                **(model.model_metadata or {}),
                                "serving_status": "running",
                                "device": "cpu"
                            }
                        else:
                            model.model_metadata = {
                                **(model.model_metadata or {}),
                                "serving_status": "stopped"
                            }
                self.db.commit()
                
                logger.info(f"모델 서빙 시작 완료: {model_id}")
                
                return {
                    "status": "running",
                    "model": model_id,
                    "message": "모델 서빙이 시작되었습니다.",
                    "device": "cpu",
                    "model_info": slm_provider.get_model_info()
                }
                
            except Exception as e:
                logger.error(f"모델 로딩 오류: {e}")
                return {
                    "status": "error",
                    "message": f"모델 로딩 오류: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"모델 서빙 시작 오류: {e}")
            return {
                "status": "error",
                "message": f"모델 서빙 시작 오류: {str(e)}"
            }
    
    async def _unload_model(self, model_id: str):
        """모델 언로드 (내부 메서드)"""
        global _CURRENT_SERVING_MODEL
        
        if model_id in self.serving_models:
            # 모델 인스턴스 제거 (메모리 해제)
            del self.serving_models[model_id]
            
            if _CURRENT_SERVING_MODEL == model_id:
                _CURRENT_SERVING_MODEL = None
                self.current_serving_model = None
            
            logger.info(f"모델 언로드 완료: {model_id}")
    
    async def stop_serving(self, model_id: str) -> Dict[str, Any]:
        """모델 서빙 중지"""
        global _CURRENT_SERVING_MODEL
        
        if model_id in self.serving_models:
            # 모델 언로드
            await self._unload_model(model_id)
            
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
    
    async def replace_model(
        self,
        old_model_id: str,
        new_model_id: str
    ) -> Dict[str, Any]:
        """
        모델 교체 (기존 모델 언로드 후 새 모델 로드)
        
        Args:
            old_model_id: 교체할 기존 모델 ID
            new_model_id: 새로 로드할 모델 ID
            
        Returns:
            교체 결과
        """
        # 기존 모델 중지
        if old_model_id in self.serving_models:
            await self.stop_serving(old_model_id)
        
        # 새 모델 시작
        result = await self.start_serving(new_model_id, model_type="transformers")
        
        return {
            "status": "replaced" if result.get("status") == "running" else "error",
            "old_model": old_model_id,
            "new_model": new_model_id,
            "message": f"모델 교체 완료: {old_model_id} → {new_model_id}" if result.get("status") == "running" else f"모델 교체 실패: {result.get('message', '')}",
            "new_model_info": result.get("model_info")
        }
    
    def get_current_serving_model(self) -> Optional[str]:
        """현재 서빙 중인 모델 ID 반환"""
        global _CURRENT_SERVING_MODEL
        return _CURRENT_SERVING_MODEL
    
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

