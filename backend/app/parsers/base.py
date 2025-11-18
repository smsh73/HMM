"""
문서 파서 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

from app.utils.multilingual_preprocessor import MultilingualPreprocessor


@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    title: str = ""
    author: str = ""
    created_date: datetime = None
    modified_date: datetime = None
    page_count: int = 0
    word_count: int = 0
    language: str = "ko"
    custom_fields: Dict[str, Any] = None


@dataclass
class ContentChunk:
    """문서 청크"""
    content: str
    chunk_index: int
    page_number: int = None
    section_title: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class ParsedDocument:
    """파싱된 문서"""
    filename: str
    file_type: str
    metadata: DocumentMetadata
    chunks: List[ContentChunk]
    full_text: str
    structure: Dict[str, Any] = None  # 문서 구조 (제목, 섹션 등)


class DocumentParser(ABC):
    """문서 파서 기본 클래스"""
    
    def __init__(self):
        """파서 초기화"""
        self.preprocessor = MultilingualPreprocessor()
    
    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """문서 파싱"""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """메타데이터 추출"""
        pass
    
    def chunk_document(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[ContentChunk]:
        """
        문서를 청크로 분할 (다국어 지원)
        
        Args:
            text: 청킹할 텍스트
            chunk_size: 청크 크기
            chunk_overlap: 청크 오버랩
            
        Returns:
            ContentChunk 리스트
        """
        # 다국어 전처리기를 사용한 스마트 청킹
        chunk_data = self.preprocessor.smart_chunk(
            text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # ContentChunk 객체로 변환
        chunks = []
        for chunk_info in chunk_data:
            chunks.append(ContentChunk(
                content=chunk_info["content"],
                chunk_index=chunk_info["chunk_index"],
                metadata=chunk_info.get("metadata", {})
            ))
        
        return chunks

