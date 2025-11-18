"""
sample docs 폴더의 문서들을 전처리하여 벡터 임베딩 및 Hybrid RAG 구성
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.services.document_service import DocumentService
from app.core.logging import logger
from app.parsers.parser_factory import ParserFactory


def process_sample_documents():
    """sample docs 폴더의 모든 문서 처리"""
    # 데이터베이스 초기화
    init_db()
    db: Session = SessionLocal()
    
    try:
        # 관리자 사용자 조회 또는 생성
        from app.models.database import User
        admin_user = db.query(User).filter(User.role == "admin").first()
        
        if not admin_user:
            logger.error("관리자 사용자가 없습니다. 먼저 사용자를 생성하세요.")
            return
        
        # sample docs 폴더 경로
        sample_docs_dir = project_root.parent / "sample docs"
        
        if not sample_docs_dir.exists():
            logger.error(f"sample docs 폴더를 찾을 수 없습니다: {sample_docs_dir}")
            return
        
        logger.info(f"sample docs 폴더 처리 시작: {sample_docs_dir}")
        
        # 문서 서비스 초기화
        doc_service = DocumentService(db)
        
        # 지원되는 파일 확장자
        supported_extensions = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"}
        
        # 모든 문서 파일 찾기
        doc_files = []
        for ext in supported_extensions:
            doc_files.extend(sample_docs_dir.glob(f"*{ext}"))
            doc_files.extend(sample_docs_dir.glob(f"*{ext.upper()}"))
        
        logger.info(f"처리할 문서 수: {len(doc_files)}")
        
        # 각 문서 처리
        processed_count = 0
        error_count = 0
        
        for doc_file in doc_files:
            try:
                logger.info(f"문서 처리 시작: {doc_file.name}")
                
                # 파일이 지원되는 형식인지 확인
                if not ParserFactory.is_supported(str(doc_file)):
                    logger.warning(f"지원하지 않는 파일 형식: {doc_file.name}")
                    continue
                
                # 문서 업로드
                document = doc_service.upload_document(
                    file_path=str(doc_file),
                    filename=doc_file.name,
                    user_id=admin_user.id
                )
                
                logger.info(f"문서 업로드 완료: {document.filename} (ID: {document.id})")
                
                # 문서 파싱
                document = doc_service.parse_document(document.id)
                logger.info(f"문서 파싱 완료: {document.filename} - {len(document.parsed_content.get('chunks', []))}개 청크")
                
                # 문서 인덱싱 (벡터 임베딩 및 Hybrid RAG 구성)
                index_result = doc_service.index_document(document.id, admin_user.id)
                logger.info(
                    f"문서 인덱싱 완료: {document.filename} - "
                    f"추가={index_result.get('added', 0)}, "
                    f"수정={index_result.get('modified', 0)}, "
                    f"삭제={index_result.get('deleted', 0)}"
                )
                
                processed_count += 1
                logger.info(f"문서 처리 완료: {doc_file.name} ✓")
                
            except Exception as e:
                error_count += 1
                logger.error(f"문서 처리 오류 ({doc_file.name}): {e}", exc_info=True)
        
        logger.info(
            f"\n{'='*60}\n"
            f"문서 처리 완료\n"
            f"총 문서 수: {len(doc_files)}\n"
            f"처리 성공: {processed_count}\n"
            f"처리 실패: {error_count}\n"
            f"{'='*60}"
        )
        
    except Exception as e:
        logger.error(f"문서 처리 중 오류 발생: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    process_sample_documents()

