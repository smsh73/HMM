"""
PDF 문서 파서
"""
import pdfplumber
from typing import List
from datetime import datetime

from app.parsers.base import DocumentParser, ParsedDocument, DocumentMetadata, ContentChunk


class PDFParser(DocumentParser):
    """PDF 문서 파서"""
    
    def parse(self, file_path: str) -> ParsedDocument:
        """PDF 문서 파싱"""
        full_text = ""
        chunks = []
        structure = {
            "pages": [],
            "tables": [],
            "images": []
        }
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 텍스트 추출
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                    structure["pages"].append({
                        "page_number": page_num,
                        "text_length": len(page_text)
                    })
                
                # 표 추출
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        table_text = self._table_to_text(table)
                        full_text += table_text + "\n"
                        structure["tables"].append({
                            "page_number": page_num,
                            "table_index": table_idx,
                            "rows": len(table)
                        })
        
        # 메타데이터 추출
        metadata = self.extract_metadata(file_path)
        metadata.page_count = len(structure["pages"])
        metadata.word_count = len(full_text.split())
        
        # 청크 분할
        chunks = self.chunk_document(full_text)
        
        # 페이지 번호 추가
        current_page = 1
        chars_per_page = len(full_text) // metadata.page_count if metadata.page_count > 0 else len(full_text)
        for chunk in chunks:
            chunk.page_number = min(
                current_page,
                int(chunk.metadata.get("start", 0) // chars_per_page) + 1
            )
        
        return ParsedDocument(
            filename=file_path.split("/")[-1],
            file_type="pdf",
            metadata=metadata,
            chunks=chunks,
            full_text=full_text,
            structure=structure
        )
    
    def extract_metadata(self, file_path: str) -> DocumentMetadata:
        """PDF 메타데이터 추출"""
        metadata = DocumentMetadata()
        
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata.page_count = len(pdf.pages)
                
                # PDF 메타데이터 추출 시도
                if hasattr(pdf, 'metadata') and pdf.metadata:
                    metadata.title = pdf.metadata.get('Title', '')
                    metadata.author = pdf.metadata.get('Author', '')
                    if pdf.metadata.get('CreationDate'):
                        try:
                            metadata.created_date = datetime.fromisoformat(
                                pdf.metadata['CreationDate'].replace('D:', '')
                            )
                        except:
                            pass
        except Exception as e:
            print(f"메타데이터 추출 오류: {e}")
        
        return metadata
    
    def _table_to_text(self, table: List[List]) -> str:
        """표를 텍스트로 변환"""
        if not table:
            return ""
        
        text_rows = []
        for row in table:
            if row:
                text_row = " | ".join(str(cell) if cell else "" for cell in row)
                text_rows.append(text_row)
        
        return "\n".join(text_rows)

