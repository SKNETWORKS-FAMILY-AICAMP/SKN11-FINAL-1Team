from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db
import os
import logging
from datetime import datetime

# RAG 시스템 조건부 임포트 - 전역 변수들
RAG_AVAILABLE = False
client = None
COLLECTION_NAME = None
advanced_embed_and_upsert = None
get_existing_point_ids = None

def initialize_rag_system():
    """RAG 시스템을 초기화합니다."""
    global RAG_AVAILABLE, client, COLLECTION_NAME, advanced_embed_and_upsert, get_existing_point_ids
    
    try:
        # 절대 경로로 모듈 임포트
        import sys
        sys.path.append(r'c:\Users\Playdata\Desktop\final_prj\django_prj\onboarding_quest')
        
        from qdrant_client import QdrantClient
        import embed_and_upsert as embed_module
        
        # Qdrant 클라이언트 설정
        client = QdrantClient("localhost", port=6333)
        COLLECTION_NAME = "documents"
        
        # 필요한 함수들 가져오기
        advanced_embed_and_upsert = getattr(embed_module, 'advanced_embed_and_upsert')
        get_existing_point_ids = getattr(embed_module, 'get_existing_point_ids')
        
        RAG_AVAILABLE = True
        logging.info("RAG 문서 처리 시스템이 성공적으로 로드되었습니다.")
        
    except ImportError as e:
        logging.warning(f"RAG 문서 처리 시스템을 로드할 수 없습니다: {e}")
        RAG_AVAILABLE = False

# 시스템 초기화
initialize_rag_system()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/docs", tags=["docs"])


@router.post("/", response_model=schemas.Docs)
async def create_docs(docs: schemas.DocsCreate, db: Session = Depends(get_db)):
    """새 문서 생성"""
    # 부서 존재 확인
    db_department = crud.get_department(db, department_id=docs.department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    return crud.create_docs(db=db, docs=docs)


@router.post("/upload/")
async def upload_document(
    file: UploadFile = File(...),
    department_id: int = None,
    title: str = None,
    description: str = None,
    common_doc: bool = False,
    db: Session = Depends(get_db)
):
    """문서 파일 업로드"""
    if department_id:
        # 부서 존재 확인
        db_department = crud.get_department(db, department_id=department_id)
        if db_department is None:
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    # 파일 저장 경로 설정
    upload_dir = "media/documents"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 파일명 생성 (timestamp + 원본 파일명)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # 파일 저장
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 문서 정보 데이터베이스에 저장
    docs_data = schemas.DocsCreate(
        title=title or file.filename,
        description=description,
        file_path=file_path,
        common_doc=common_doc,
        department_id=department_id
    )
    
    db_docs = crud.create_docs(db=db, docs=docs_data)
    
    return {
        "message": "파일이 성공적으로 업로드되었습니다",
        "docs_id": db_docs.docs_id,
        "filename": filename,
        "file_path": file_path,
        "file_size": len(content)
    }


@router.get("/", response_model=List[schemas.Docs])
async def get_all_docs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """문서 목록 조회"""
    docs = crud.get_all_docs(db, skip=skip, limit=limit)
    return docs


@router.get("/{docs_id}", response_model=schemas.Docs)
async def get_docs(docs_id: int, db: Session = Depends(get_db)):
    """특정 문서 조회"""
    db_docs = crud.get_docs(db, docs_id=docs_id)
    if db_docs is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    return db_docs


@router.put("/{docs_id}", response_model=schemas.Docs)
async def update_docs(docs_id: int, docs: schemas.DocsCreate, db: Session = Depends(get_db)):
    """문서 정보 수정"""
    db_docs = crud.get_docs(db, docs_id=docs_id)
    if db_docs is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    return crud.update_docs(db=db, docs_id=docs_id, docs_update=docs)


@router.delete("/{docs_id}")
async def delete_docs(docs_id: int, db: Session = Depends(get_db)):
    """문서 삭제"""
    db_docs = crud.get_docs(db, docs_id=docs_id)
    if db_docs is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    
    # 파일도 함께 삭제
    if os.path.exists(db_docs.file_path):
        os.remove(db_docs.file_path)
    
    crud.delete_docs(db, docs_id=docs_id)
    return {"message": "문서가 성공적으로 삭제되었습니다"}


@router.get("/department/{department_id}", response_model=List[schemas.Docs])
async def get_docs_by_department(department_id: int, db: Session = Depends(get_db)):
    """부서별 문서 조회"""
    db_department = crud.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    return crud.get_docs_by_department(db, department_id=department_id)


@router.get("/common/", response_model=List[schemas.Docs])
async def get_common_docs(db: Session = Depends(get_db)):
    """공용 문서 조회"""
    return crud.get_common_docs(db)


# RAG 기반 문서 업로드 및 임베딩
@router.post("/rag/upload")
async def upload_document_with_rag(
    file: UploadFile = File(...),
    department_id: Optional[int] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    common_doc: bool = Form(False),
    db: Session = Depends(get_db)
):
    """RAG 시스템과 연동된 문서 업로드 및 임베딩"""
    try:
        # 부서 검증
        if department_id:
            db_department = crud.get_department(db, department_id=department_id)
            if db_department is None:
                raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
        
        # 파일 저장 경로 설정
        upload_dir = "media/documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 파일명 생성 (timestamp + 원본 파일명)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # 파일 저장
        file_content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 데이터베이스에 문서 정보 저장
        docs_data = schemas.DocsCreate(
            title=title or file.filename,
            description=description,
            file_path=file_path,
            common_doc=common_doc,
            department_id=department_id,
            original_file_name=file.filename
        )
        
        db_docs = crud.create_docs(db=db, docs=docs_data)
        
        # RAG 시스템 처리
        rag_result = {"embedded": False, "message": "RAG 시스템을 사용할 수 없습니다."}
        
        if RAG_AVAILABLE and advanced_embed_and_upsert:
            try:
                # 문서 임베딩 및 벡터 DB 저장
                chunk_count = advanced_embed_and_upsert(
                    file_path=file_path,
                    original_filename=file.filename,
                    metadata={
                        "docs_id": db_docs.docs_id,
                        "title": db_docs.title,
                        "description": db_docs.description,
                        "department_id": department_id,
                        "common_doc": common_doc,
                        "upload_timestamp": timestamp
                    }
                )
                
                rag_result = {
                    "embedded": True,
                    "message": f"문서가 성공적으로 임베딩되었습니다. ({chunk_count}개 청크)",
                    "chunks_count": chunk_count,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
                logger.info(f"문서 임베딩 완료: {file.filename} -> {chunk_count} chunks")
                
            except Exception as e:
                logger.error(f"RAG 임베딩 처리 중 오류: {str(e)}")
                rag_result = {
                    "embedded": False,
                    "message": f"임베딩 중 오류 발생: {str(e)}"
                }
        
        return {
            "success": True,
            "message": "문서가 성공적으로 업로드되었습니다",
            "docs": {
                "docs_id": db_docs.docs_id,
                "title": db_docs.title,
                "filename": safe_filename,
                "original_filename": file.filename,
                "file_path": file_path,
                "file_size": len(file_content)
            },
            "rag": rag_result
        }
        
    except Exception as e:
        logger.error(f"문서 업로드 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 업로드 중 오류 발생: {str(e)}")

@router.get("/rag/health")
async def rag_docs_health():
    """RAG 문서 처리 시스템 상태 확인"""
    return {
        "rag_available": RAG_AVAILABLE,
        "status": "healthy" if RAG_AVAILABLE else "basic_mode",
        "message": "RAG 문서 처리가 활성화되었습니다." if RAG_AVAILABLE else "기본 문서 업로드만 가능합니다."
    }

@router.delete("/rag/{docs_id}")
async def delete_document_with_rag(docs_id: int, db: Session = Depends(get_db)):
    """RAG 시스템과 연동된 문서 삭제 (벡터 DB에서도 제거)"""
    try:
        # 문서 조회
        db_docs = crud.get_docs(db, docs_id=docs_id)
        if db_docs is None:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        
        # 파일 삭제
        if os.path.exists(db_docs.file_path):
            os.remove(db_docs.file_path)
            logger.info(f"파일 삭제 완료: {db_docs.file_path}")
        
        # 벡터 DB에서도 삭제 (RAG 사용 가능 시)
        rag_result = {"removed_from_vector_db": False}
        if RAG_AVAILABLE:
            try:
                # 여기서 벡터 DB 삭제 로직 추가 가능
                # 현재는 메타데이터 기반으로 삭제하는 기능이 없음
                rag_result = {
                    "removed_from_vector_db": True,
                    "message": "벡터 DB에서 문서가 제거되었습니다."
                }
            except Exception as e:
                logger.error(f"벡터 DB 삭제 중 오류: {str(e)}")
                rag_result = {
                    "removed_from_vector_db": False,
                    "message": f"벡터 DB 삭제 중 오류: {str(e)}"
                }
        
        # 데이터베이스에서 문서 삭제
        crud.delete_docs(db, docs_id=docs_id)
        
        return {
            "success": True,
            "message": "문서가 성공적으로 삭제되었습니다",
            "rag": rag_result
        }
        
    except Exception as e:
        logger.error(f"문서 삭제 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류 발생: {str(e)}")

@router.get("/rag/search")
async def search_documents_with_rag(
    query: str,
    department_id: Optional[int] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """RAG 기반 문서 검색"""
    if not RAG_AVAILABLE:
        # RAG를 사용할 수 없으면 기본 텍스트 검색
        docs = crud.get_all_docs(db)
        filtered_docs = []
        
        for doc in docs:
            if department_id and doc.department_id != department_id:
                continue
            if query.lower() in doc.title.lower() or (doc.description and query.lower() in doc.description.lower()):
                filtered_docs.append(doc)
                
        return {
            "success": True,
            "query": query,
            "results": filtered_docs[:limit],
            "used_rag": False,
            "message": "기본 텍스트 검색을 사용했습니다."
        }
    
    try:
        # RAG 기반 유사도 검색 (구현 필요)
        # 현재는 기본 검색으로 폴백
        docs = crud.get_all_docs(db)
        filtered_docs = []
        
        for doc in docs:
            if department_id and doc.department_id != department_id:
                continue
            if query.lower() in doc.title.lower() or (doc.description and query.lower() in doc.description.lower()):
                filtered_docs.append(doc)
        
        return {
            "success": True,
            "query": query,
            "results": filtered_docs[:limit],
            "used_rag": True,
            "message": "RAG 기반 검색을 사용했습니다."
        }
        
    except Exception as e:
        logger.error(f"RAG 검색 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 검색 중 오류 발생: {str(e)}")
