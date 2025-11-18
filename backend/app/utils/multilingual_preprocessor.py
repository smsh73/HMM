"""
다국어 문서 전처리 유틸리티
한글, 영문, 다국어 문서를 지원하는 전처리 기능
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import langdetect
    from langdetect import detect, detect_langs
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    print("Warning: langdetect not available. Install with: pip install langdetect")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False
    print("Warning: nltk not available. Install with: pip install nltk")

from app.core.logging import logger


@dataclass
class LanguageInfo:
    """언어 정보"""
    language: str
    confidence: float
    is_multilingual: bool = False
    detected_languages: List[Dict[str, float]] = None


class MultilingualPreprocessor:
    """
    다국어 문서 전처리기
    
    지원 기능:
    - 언어 자동 감지
    - 다국어 문서 처리
    - 언어별 청킹 최적화
    - 텍스트 정규화
    """
    
    def __init__(self):
        """다국어 전처리기 초기화"""
        self._init_nltk()
    
    def _init_nltk(self):
        """NLTK 리소스 초기화"""
        if HAS_NLTK:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                try:
                    nltk.download('punkt', quiet=True)
                except:
                    pass
            
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                try:
                    nltk.download('stopwords', quiet=True)
                except:
                    pass
    
    def detect_language(self, text: str) -> LanguageInfo:
        """
        텍스트 언어 감지
        
        Args:
            text: 감지할 텍스트
            
        Returns:
            LanguageInfo 객체
        """
        if not HAS_LANGDETECT:
            # 기본값: 한국어로 가정
            return LanguageInfo(
                language="ko",
                confidence=0.5,
                is_multilingual=False
            )
        
        try:
            # 최소 길이 체크
            if len(text.strip()) < 10:
                return LanguageInfo(
                    language="ko",
                    confidence=0.5,
                    is_multilingual=False
                )
            
            # 언어 감지
            detected_langs = detect_langs(text)
            primary_lang = detected_langs[0]
            
            # 다국어 문서 확인 (두 번째 언어의 신뢰도가 0.1 이상)
            is_multilingual = len(detected_langs) > 1 and detected_langs[1].prob > 0.1
            
            return LanguageInfo(
                language=primary_lang.lang,
                confidence=primary_lang.prob,
                is_multilingual=is_multilingual,
                detected_languages=[
                    {"lang": lang.lang, "prob": lang.prob}
                    for lang in detected_langs[:3]
                ]
            )
        except Exception as e:
            logger.warning(f"언어 감지 실패: {e}, 기본값(한국어) 사용")
            return LanguageInfo(
                language="ko",
                confidence=0.5,
                is_multilingual=False
            )
    
    def normalize_text(self, text: str, language: str = None) -> str:
        """
        텍스트 정규화
        
        Args:
            text: 정규화할 텍스트
            language: 언어 코드 (None이면 자동 감지)
            
        Returns:
            정규화된 텍스트
        """
        # 언어 감지
        if language is None:
            lang_info = self.detect_language(text)
            language = lang_info.language
        
        # 기본 정규화
        # 1. 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 2. 특수 문자 정리 (문장 부호는 유지)
        # 한글, 영문, 숫자, 기본 문장 부호만 유지
        if language == "ko":
            # 한글, 영문, 숫자, 기본 문장 부호
            text = re.sub(r'[^\w\s\u3131-\u318E\uAC00-\uD7A3.,!?;:()\[\]{}"\'-]', ' ', text)
        else:
            # 영문, 숫자, 기본 문장 부호
            text = re.sub(r'[^\w\s.,!?;:()\[\]{}"\'-]', ' ', text)
        
        # 3. 연속된 공백 다시 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 4. 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def smart_chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        language: str = None
    ) -> List[Dict[str, Any]]:
        """
        언어 인식 스마트 청킹
        
        Args:
            text: 청킹할 텍스트
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 오버랩 (문자 수)
            language: 언어 코드 (None이면 자동 감지)
            
        Returns:
            청크 리스트 [{"content": str, "chunk_index": int, "metadata": dict}, ...]
        """
        # 언어 감지
        lang_info = self.detect_language(text)
        if language is None:
            language = lang_info.language
        
        # 텍스트 정규화
        normalized_text = self.normalize_text(text, language)
        
        # 언어별 문장 분리
        sentences = self._split_sentences(normalized_text, language)
        
        # 청크 생성
        chunks = []
        current_chunk = ""
        current_size = 0
        chunk_index = 0
        sentence_buffer = []
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # 현재 청크에 추가하면 크기 초과하는 경우
            if current_size + sentence_len > chunk_size and current_chunk:
                # 현재 청크 저장
                chunks.append({
                    "content": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "metadata": {
                        "language": language,
                        "language_confidence": lang_info.confidence,
                        "is_multilingual": lang_info.is_multilingual,
                        "char_count": len(current_chunk),
                        "sentence_count": len(sentence_buffer)
                    }
                })
                chunk_index += 1
                
                # 오버랩 처리: 마지막 몇 문장을 다음 청크 시작에 포함
                overlap_sentences = []
                overlap_size = 0
                for sent in reversed(sentence_buffer):
                    if overlap_size + len(sent) <= chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_size += len(sent)
                    else:
                        break
                
                current_chunk = " ".join(overlap_sentences)
                current_size = overlap_size
                sentence_buffer = overlap_sentences.copy()
            
            # 문장 추가
            current_chunk += (" " if current_chunk else "") + sentence
            current_size += sentence_len
            sentence_buffer.append(sentence)
        
        # 마지막 청크 저장
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "metadata": {
                    "language": language,
                    "language_confidence": lang_info.confidence,
                    "is_multilingual": lang_info.is_multilingual,
                    "char_count": len(current_chunk),
                    "sentence_count": len(sentence_buffer)
                }
            })
        
        return chunks
    
    def _split_sentences(self, text: str, language: str) -> List[str]:
        """
        언어별 문장 분리
        
        Args:
            text: 분리할 텍스트
            language: 언어 코드
            
        Returns:
            문장 리스트
        """
        if language == "ko":
            # 한국어 문장 분리 (마침표, 느낌표, 물음표 기준)
            sentences = re.split(r'[.!?]\s+', text)
            # 마지막 문장 처리
            if text and text[-1] not in '.!?':
                if sentences and not sentences[-1].strip():
                    sentences.pop()
        elif HAS_NLTK:
            # NLTK를 사용한 영문 문장 분리
            try:
                sentences = sent_tokenize(text)
            except:
                # NLTK 실패 시 기본 분리
                sentences = re.split(r'[.!?]\s+', text)
        else:
            # 기본 문장 분리
            sentences = re.split(r'[.!?]\s+', text)
        
        # 빈 문장 제거 및 정리
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def preprocess_document(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        문서 전체 전처리
        
        Args:
            text: 전처리할 텍스트
            chunk_size: 청크 크기
            chunk_overlap: 청크 오버랩
            
        Returns:
            전처리 결과 딕셔너리
        """
        # 언어 감지
        lang_info = self.detect_language(text)
        
        # 텍스트 정규화
        normalized_text = self.normalize_text(text, lang_info.language)
        
        # 스마트 청킹
        chunks = self.smart_chunk(
            normalized_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            language=lang_info.language
        )
        
        return {
            "original_text": text,
            "normalized_text": normalized_text,
            "language_info": {
                "language": lang_info.language,
                "confidence": lang_info.confidence,
                "is_multilingual": lang_info.is_multilingual,
                "detected_languages": lang_info.detected_languages
            },
            "chunks": chunks,
            "total_chunks": len(chunks),
            "total_chars": len(normalized_text)
        }

