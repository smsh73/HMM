"""
문서 요약 엔진
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.core.config import settings
from app.parsers.base import ParsedDocument
from app.ai.llm_providers import LLMProvider


@dataclass
class Summary:
    """요약 결과"""
    summary_type: str
    content: str
    keywords: List[str]
    quality_score: float
    original_length: int
    summary_length: int


class DocumentSummarizer:
    """문서 요약 엔진"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """요약 엔진 초기화"""
        self.llm_provider = llm_provider
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
    
    async def summarize_document(
        self,
        document: ParsedDocument,
        summary_type: str = "core",
        llm_provider: Optional[LLMProvider] = None
    ) -> Summary:
        """문서 요약 생성"""
        text = document.full_text
        
        # 요약 타입별 프롬프트
        prompts = {
            "core": f"""다음 문서의 핵심 내용을 간결하게 요약해주세요. (200자 이내)

문서 내용:
{text}

핵심 요약:""",
            
            "detailed": f"""다음 문서를 상세하게 요약해주세요. 주요 섹션과 내용을 포함해주세요.

문서 내용:
{text}

상세 요약:""",
            
            "keywords": f"""다음 문서에서 핵심 키워드 5-10개를 추출해주세요. 키워드는 쉼표로 구분해주세요.

문서 내용:
{text}

핵심 키워드:"""
        }
        
        prompt = prompts.get(summary_type, prompts["core"])
        
        # LLM 프로바이더를 통한 요약 생성
        provider = llm_provider or self.llm_provider
        if not provider:
            # 기본 Ollama 사용
            from app.ai.llm_providers import OllamaProvider
            provider = OllamaProvider(
                base_url=self.ollama_url,
                model=self.ollama_model
            )
        
        try:
            summary_content = await provider.generate(prompt)
        except Exception as e:
            print(f"요약 생성 오류: {e}")
            summary_content = "요약 생성 중 오류가 발생했습니다."
        
        # 키워드 추출 (키워드 타입이 아닌 경우)
        keywords = []
        if summary_type != "keywords":
            keywords = await self._extract_keywords(text)
        else:
            keywords = [kw.strip() for kw in summary_content.split(",") if kw.strip()]
        
        # 품질 점수 계산
        quality_score = self._evaluate_summary_quality(text, summary_content)
        
        return Summary(
            summary_type=summary_type,
            content=summary_content,
            keywords=keywords,
            quality_score=quality_score,
            original_length=len(text),
            summary_length=len(summary_content)
        )
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """키워드 추출"""
        # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용 가능)
        words = text.split()
        # 한글 단어 필터링 및 빈도 기반 추출
        korean_words = [w for w in words if any('\uac00' <= c <= '\ud7a3' for c in w)]
        # 빈도 기반으로 상위 키워드 선택 (간단한 구현)
        word_freq = {}
        for word in korean_words:
            if len(word) > 1:  # 1글자 제외
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:10]]
    
    def _evaluate_summary_quality(
        self,
        original: str,
        summary: str
    ) -> float:
        """요약 품질 평가"""
        if not summary or not original:
            return 0.0
        
        # 간단한 품질 지표
        # 1. 압축률 (적절한 길이)
        compression_ratio = len(summary) / len(original) if original else 0
        compression_score = 1.0 if 0.1 <= compression_ratio <= 0.3 else 0.5
        
        # 2. 원문 단어 포함률
        original_words = set(original.split())
        summary_words = set(summary.split())
        overlap_ratio = len(original_words & summary_words) / len(original_words) if original_words else 0
        overlap_score = min(overlap_ratio * 2, 1.0)  # 50% 이상이면 만점
        
        # 종합 점수
        quality_score = (compression_score * 0.4 + overlap_score * 0.6)
        
        return round(quality_score, 2)

