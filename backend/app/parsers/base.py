"""
문서 파서 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


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
        """문서를 청크로 분할"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # 문장 경계에서 자르기
            if end < len(text):
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                cut_point = max(last_period, last_newline)
                if cut_point > chunk_size * 0.5:  # 최소한 절반 이상은 유지
                    chunk_text = chunk_text[:cut_point + 1]
                    end = start + len(chunk_text)
            
            chunks.append(ContentChunk(
                content=chunk_text.strip(),
                chunk_index=chunk_index,
                metadata={"start": start, "end": end}
            ))
            
            chunk_index += 1
            start = end - chunk_overlap
        
        return chunks

