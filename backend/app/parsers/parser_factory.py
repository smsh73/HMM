"""
문서 파서 팩토리
"""
from pathlib import Path
from typing import Optional

from app.parsers.base import DocumentParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.word_parser import WordParser
from app.parsers.excel_parser import ExcelParser


class ParserFactory:
    """문서 파서 팩토리"""
    
    _parsers = {
        ".pdf": PDFParser,
        ".docx": WordParser,
        ".doc": WordParser,
        ".xlsx": ExcelParser,
        ".xls": ExcelParser,
    }
    
    @classmethod
    def get_parser(cls, file_path: str) -> Optional[DocumentParser]:
        """파일 경로에 따라 적절한 파서 반환"""
        file_ext = Path(file_path).suffix.lower()
        parser_class = cls._parsers.get(file_ext)
        
        if parser_class:
            return parser_class()
        
        return None
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """파일이 지원되는 형식인지 확인"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in cls._parsers

