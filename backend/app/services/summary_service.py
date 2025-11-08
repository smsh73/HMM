"""
요약 서비스
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.database import Document
from app.parsers.parser_factory import ParserFactory
from app.ai.summarizer import DocumentSummarizer
from app.services.llm_service import LLMService


class SummaryService:
    """요약 서비스"""
    
    def __init__(self, db: Session):
        """요약 서비스 초기화"""
        self.db = db
        self.summarizer = DocumentSummarizer()
        self.llm_service = LLMService(db)
    
    async def summarize_document(
        self,
        document_id: str,
        summary_type: str = "core",
        use_main_system: bool = True,
        provider_name: Optional[str] = None
    ) -> dict:
        """문서 요약 생성"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("문서를 찾을 수 없습니다.")
        
        if not document.is_parsed:
            raise ValueError("문서가 파싱되지 않았습니다. 먼저 파싱을 수행하세요.")
        
        # 파서로 문서 재파싱 (또는 캐시된 파싱 결과 사용)
        parser = ParserFactory.get_parser(document.file_path)
        parsed_doc = parser.parse(document.file_path)
        
        # LLM 프로바이더 가져오기
        llm_provider = self.llm_service.get_provider(
            provider_name=provider_name,
            use_main_system=use_main_system
        )
        
        # 요약 생성
        summary = await self.summarizer.summarize_document(
            parsed_doc, 
            summary_type,
            llm_provider=llm_provider
        )
        
        return {
            "document_id": document_id,
            "summary_type": summary.summary_type,
            "content": summary.content,
            "keywords": summary.keywords,
            "quality_score": summary.quality_score,
            "original_length": summary.original_length,
            "summary_length": summary.summary_length
        }

