"""
LLM 프로바이더 추상화 레이어
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import httpx
import os
from cryptography.fernet import Fernet
import base64


class LLMProvider(ABC):
    """LLM 프로바이더 기본 클래스"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """프로바이더 사용 가능 여부"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI 프로바이더"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """OpenAI API를 통한 텍스트 생성"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    **kwargs
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude 프로바이더"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Claude API를 통한 텍스트 생성"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": kwargs.get("max_tokens", 1024),
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class GeminiProvider(LLMProvider):
    """Google Gemini 프로바이더"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Gemini API를 통한 텍스트 생성"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class PerplexityProvider(LLMProvider):
    """Perplexity 프로바이더"""
    
    def __init__(self, api_key: str, model: str = "llama-3-sonar-large-32k-online"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.perplexity.ai"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Perplexity API를 통한 텍스트 생성"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    **kwargs
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class OllamaProvider(LLMProvider):
    """Ollama 프로바이더 (로컬)"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2:7b"):
        self.base_url = base_url
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Ollama를 통한 텍스트 생성"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    
    def is_available(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 새 태스크 생성
                import httpx
                with httpx.Client(timeout=2.0) as client:
                    response = client.get(f"{self.base_url}/api/tags")
                    return response.status_code == 200
            else:
                return asyncio.run(self._check_connection())
        except:
            return False
    
    async def _check_connection(self) -> bool:
        """연결 확인 (비동기)"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False


class LLMProviderFactory:
    """LLM 프로바이더 팩토리"""
    
    _providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
        "perplexity": PerplexityProvider,
        "ollama": OllamaProvider,
    }
    
    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[LLMProvider]:
        """프로바이더 생성"""
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            return None
        
        if provider_name.lower() == "ollama":
            return provider_class(
                base_url=base_url or "http://localhost:11434",
                model=model or "llama2:7b"
            )
        else:
            if not api_key:
                return None
            return provider_class(api_key=api_key, model=model or cls._get_default_model(provider_name))
    
    @classmethod
    def _get_default_model(cls, provider_name: str) -> str:
        """기본 모델명 반환"""
        defaults = {
            "openai": "gpt-3.5-turbo",
            "claude": "claude-3-sonnet-20240229",
            "gemini": "gemini-pro",
            "perplexity": "llama-3-sonar-large-32k-online",
        }
        return defaults.get(provider_name.lower(), "")


class APIKeyManager:
    """API 키 암호화 관리"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """암호화 키 초기화"""
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # 환경 변수에서 키 가져오기 또는 기본 키 생성
            key = os.getenv("ENCRYPTION_KEY")
            if key:
                self.key = key.encode()
            else:
                # 기본 키 (프로덕션에서는 반드시 변경)
                self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plain_text: str) -> str:
        """텍스트 암호화"""
        return self.cipher.encrypt(plain_text.encode()).decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """텍스트 복호화"""
        return self.cipher.decrypt(encrypted_text.encode()).decode()

