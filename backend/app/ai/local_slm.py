"""
로컬 SLM (Small Language Model) 프로바이더
Hugging Face Transformers 기반, 맥북 인텔 CPU 환경 최적화

권장 모델:
- beomi/KoAlpaca-Polyglot-5.8B (한글 특화, 5.8B 파라미터)
- nlpai-lab/kullm-polyglot-5.8b-v2 (한글 특화)
- google/gemma-2b-it (경량, 2B 파라미터)
- microsoft/phi-2 (경량, 2.7B 파라미터)
"""
import torch
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        pipeline,
        TextGenerationPipeline
    )
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("Warning: transformers not available. Local SLM will not work.")

from app.core.config import settings
from app.core.logging import logger
from app.ai.llm_providers import LLMProvider


class LocalSLMProvider(LLMProvider):
    """
    로컬 SLM 프로바이더
    
    특징:
    - Hugging Face Hub에서 자동 다운로드
    - CPU 전용 최적화 (맥북 인텔 환경)
    - 한글 프롬프트 지원
    - 인터넷 없이 로컬 실행
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/phi-2",
        device: str = "cpu",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        cache_dir: Optional[str] = None
    ):
        """
        로컬 SLM 초기화
        
        Args:
            model_name: Hugging Face 모델 이름
            device: 디바이스 ("cpu", "cuda", "mps")
            max_new_tokens: 최대 생성 토큰 수
            temperature: 생성 온도 (0.0~1.0)
            top_p: Nucleus sampling
            cache_dir: 모델 캐시 디렉토리
        """
        if not HAS_TRANSFORMERS:
            raise ImportError("transformers가 설치되지 않았습니다. pip install transformers")
        
        self.model_name = model_name
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        
        # 캐시 디렉토리 설정
        if cache_dir is None:
            # settings.DATA_DIR이 없으면 기본 경로 사용
            data_dir = getattr(settings, 'DATA_DIR', './data')
            cache_dir = str(Path(data_dir) / "huggingface_cache")
        self.cache_dir = cache_dir
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        # 모델 및 토크나이저 로드
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        
        self._load_model()
        
        logger.info(
            f"로컬 SLM 초기화 완료: "
            f"모델={model_name}, "
            f"디바이스={device}, "
            f"최대 토큰={max_new_tokens}"
        )
    
    def _load_model(self):
        """모델 로드"""
        try:
            logger.info(f"모델 로딩 시작: {self.model_name}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # 모델 로드 (CPU 최적화)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float32,  # CPU는 float32 사용
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            
            # 디바이스 이동
            self.model.to(self.device)
            
            # 추론 모드 (속도 향상)
            self.model.eval()
            
            # Pipeline 생성
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,  # -1 = CPU
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info(f"모델 로딩 완료: {self.model_name}")
            
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        텍스트 생성
        
        Args:
            prompt: 프롬프트
            max_tokens: 최대 토큰 수 (None이면 기본값 사용)
            temperature: 생성 온도 (None이면 기본값 사용)
            
        Returns:
            생성된 텍스트
        """
        if self.pipeline is None:
            raise RuntimeError("모델이 로드되지 않았습니다")
        
        try:
            # 파라미터 설정
            gen_params = {
                "max_new_tokens": max_tokens or self.max_new_tokens,
                "temperature": temperature or self.temperature,
                "top_p": self.top_p,
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id
            }
            
            # 생성
            outputs = self.pipeline(
                prompt,
                **gen_params
            )
            
            # 결과 추출 (프롬프트 제거)
            generated_text = outputs[0]["generated_text"]
            
            # 프롬프트 이후 텍스트만 추출
            if generated_text.startswith(prompt):
                answer = generated_text[len(prompt):].strip()
            else:
                answer = generated_text.strip()
            
            logger.debug(f"텍스트 생성 완료: {len(answer)}자")
            
            return answer
            
        except Exception as e:
            logger.error(f"텍스트 생성 실패: {e}")
            raise
    
    def is_available(self) -> bool:
        """프로바이더 사용 가능 여부"""
        return self.pipeline is not None
    
    async def generate_stream(self, prompt: str, **kwargs):
        """
        스트리밍 생성 (현재 미지원)
        
        Note: transformers pipeline은 기본적으로 스트리밍을 지원하지 않음
        """
        raise NotImplementedError("로컬 SLM은 현재 스트리밍을 지원하지 않습니다")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        채팅 형식 대화
        
        Args:
            messages: 메시지 리스트 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            AI 응답
        """
        # 메시지를 프롬프트로 변환
        prompt = self._format_chat_prompt(messages)
        
        # 생성
        return await self.generate(prompt, **kwargs)
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        채팅 메시지를 프롬프트로 변환
        
        Args:
            messages: 메시지 리스트
            
        Returns:
            포맷된 프롬프트
        """
        # 간단한 채팅 포맷 (모델에 따라 조정 필요)
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"시스템: {content}")
            elif role == "user":
                prompt_parts.append(f"사용자: {content}")
            elif role == "assistant":
                prompt_parts.append(f"AI: {content}")
        
        # 마지막에 AI 응답 시작 표시
        prompt_parts.append("AI:")
        
        return "\n\n".join(prompt_parts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "cache_dir": self.cache_dir,
            "loaded": self.pipeline is not None
        }


# 사전 정의된 모델 설정
RECOMMENDED_MODELS = {
    "phi-2": {
        "name": "microsoft/phi-2",
        "description": "Microsoft Phi-2 (2.7B, 영어 특화, 경량)",
        "max_tokens": 512
    },
    "gemma-2b": {
        "name": "google/gemma-2b-it",
        "description": "Google Gemma 2B (경량, instruction-tuned)",
        "max_tokens": 512
    },
    "koalpaca": {
        "name": "beomi/KoAlpaca-Polyglot-5.8B",
        "description": "KoAlpaca (5.8B, 한글 특화)",
        "max_tokens": 512
    },
    "kullm": {
        "name": "nlpai-lab/kullm-polyglot-5.8b-v2",
        "description": "KULLM (5.8B, 한글 특화)",
        "max_tokens": 512
    }
}


def create_local_slm(
    model_key: str = "phi-2",
    device: str = "cpu"
) -> LocalSLMProvider:
    """
    사전 정의된 모델로 로컬 SLM 생성
    
    Args:
        model_key: 모델 키 ("phi-2", "gemma-2b", "koalpaca", "kullm")
        device: 디바이스 ("cpu", "cuda", "mps")
        
    Returns:
        로컬 SLM 프로바이더
    """
    if model_key not in RECOMMENDED_MODELS:
        raise ValueError(
            f"알 수 없는 모델: {model_key}. "
            f"사용 가능: {list(RECOMMENDED_MODELS.keys())}"
        )
    
    model_config = RECOMMENDED_MODELS[model_key]
    
    return LocalSLMProvider(
        model_name=model_config["name"],
        device=device,
        max_new_tokens=model_config["max_tokens"]
    )
