"""
LLM 프로바이더 관리 서비스
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.database import LLMProvider as LLMProviderModel
from app.services.llm_service import LLMService, APIKeyManager


class ProviderService:
    """LLM 프로바이더 관리 서비스"""
    
    def __init__(self, db: Session):
        """프로바이더 서비스 초기화"""
        self.db = db
        self.key_manager = APIKeyManager()
    
    def create_or_update_provider(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        is_main_system: bool = True,
        config: Optional[Dict[str, Any]] = None
    ) -> LLMProviderModel:
        """프로바이더 생성 또는 업데이트"""
        provider = self.db.query(LLMProviderModel).filter(
            LLMProviderModel.provider_name == provider_name
        ).first()
        
        if provider:
            # 업데이트
            if api_key:
                provider.api_key = self.key_manager.encrypt(api_key)
            if base_url:
                provider.base_url = base_url
            if model_name:
                provider.model_name = model_name
            provider.is_main_system = is_main_system
            if config:
                provider.config = config
            from datetime import datetime
            provider.updated_at = datetime.utcnow()
        else:
            # 생성
            provider = LLMProviderModel(
                provider_name=provider_name,
                api_key=self.key_manager.encrypt(api_key) if api_key else None,
                base_url=base_url,
                model_name=model_name,
                is_main_system=is_main_system,
                config=config or {}
            )
            self.db.add(provider)
        
        self.db.commit()
        self.db.refresh(provider)
        return provider
    
    def get_providers(
        self,
        is_main_system: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """프로바이더 목록 조회"""
        query = self.db.query(LLMProviderModel)
        if is_main_system is not None:
            query = query.filter(LLMProviderModel.is_main_system == is_main_system)
        
        providers = query.all()
        return [
            {
                "id": p.id,
                "provider_name": p.provider_name,
                "base_url": p.base_url,
                "model_name": p.model_name,
                "is_active": p.is_active,
                "is_main_system": p.is_main_system,
                "config": p.config,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in providers
        ]
    
    def get_provider(self, provider_id: str) -> Optional[LLMProviderModel]:
        """프로바이더 조회"""
        return self.db.query(LLMProviderModel).filter(
            LLMProviderModel.id == provider_id
        ).first()
    
    def delete_provider(self, provider_id: str) -> bool:
        """프로바이더 삭제"""
        provider = self.db.query(LLMProviderModel).filter(
            LLMProviderModel.id == provider_id
        ).first()
        if not provider:
            return False
        
        self.db.delete(provider)
        self.db.commit()
        return True
    
    def toggle_provider_status(self, provider_id: str) -> bool:
        """프로바이더 활성/비활성 토글"""
        provider = self.db.query(LLMProviderModel).filter(
            LLMProviderModel.id == provider_id
        ).first()
        if not provider:
            return False
        
        provider.is_active = not provider.is_active
        from datetime import datetime
        provider.updated_at = datetime.utcnow()
        self.db.commit()
        return True

