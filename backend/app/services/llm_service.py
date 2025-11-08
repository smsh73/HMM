"""
LLM 서비스
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.database import LLMProvider as LLMProviderModel
from app.ai.llm_providers import LLMProviderFactory, LLMProvider, APIKeyManager
from app.core.config import settings


class LLMService:
    """LLM 서비스"""
    
    def __init__(self, db: Session):
        """LLM 서비스 초기화"""
        self.db = db
        self.key_manager = APIKeyManager()
    
    def get_provider(
        self,
        provider_name: Optional[str] = None,
        use_main_system: bool = True
    ) -> Optional[LLMProvider]:
        """프로바이더 인스턴스 가져오기"""
        if not provider_name:
            # 기본 프로바이더 조회
            provider_model = self.db.query(LLMProviderModel).filter(
                LLMProviderModel.is_active == True,
                LLMProviderModel.is_main_system == use_main_system
            ).first()
            
            if not provider_model:
                # 기본값으로 Ollama 사용
                return LLMProviderFactory.create_provider(
                    "ollama",
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.OLLAMA_MODEL
                )
            
            provider_name = provider_model.provider_name
        else:
            provider_model = self.db.query(LLMProviderModel).filter(
                LLMProviderModel.provider_name == provider_name,
                LLMProviderModel.is_active == True
            ).first()
        
        if not provider_model:
            return None
        
        # API 키 복호화
        api_key = None
        if provider_model.api_key:
            try:
                api_key = self.key_manager.decrypt(provider_model.api_key)
            except:
                pass
        
        # 프로바이더 생성
        return LLMProviderFactory.create_provider(
            provider_name=provider_model.provider_name,
            api_key=api_key,
            base_url=provider_model.base_url,
            model=provider_model.model_name or settings.OLLAMA_MODEL
        )
    
    async def generate_text(
        self,
        prompt: str,
        provider_name: Optional[str] = None,
        use_main_system: bool = True,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        provider = self.get_provider(provider_name, use_main_system)
        if not provider:
            raise ValueError("사용 가능한 LLM 프로바이더가 없습니다.")
        
        if not provider.is_available():
            raise ValueError(f"{provider_name} 프로바이더를 사용할 수 없습니다.")
        
        return await provider.generate(prompt, **kwargs)

