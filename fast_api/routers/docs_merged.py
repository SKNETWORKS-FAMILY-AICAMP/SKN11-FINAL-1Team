from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db
import os
import logging
from datetime import datetime
from embed_and_upsert import advanced_embed_and_upsert, get_existing_point_ids
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from fastapi.responses import FileResponse
from auth import get_current_user
from models import User

# 환경 변수 및 경로 설정
UPLOAD_BASE_DIR = os.getenv("UPLOAD_BASE_DIR", "uploaded_docs")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "media")
UPLOAD_BASE = os.path.abspath(os.path.join(MEDIA_ROOT, UPLOAD_BASE_DIR))
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "rag_multiformat"

# Qdrant 클라이언트
client = QdrantClient(url=QDRANT_URL)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/docs", tags=["docs"])

@router.post("/rag/upload")
async def upload_document_with_rag(
    file: UploadFile = File(...),
    department_id: Optional[int] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    common_doc: bool = Form(False),
    db: Session = Depends(get_db)
):
    """문서 업로드 + DB 저장 + Qdrant 임베딩"""
    try:
        # 부서 검증
        if department_id:
            db_department = crud.get_department(db, department_id=department_id)
            if db_department is None:
                raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")

        # 파일 저장
        # os.makedirs(UPLOAD_BASE, exist_ok=True)
        # file_ext = os.path.splitext(file.filename)[1]
        # unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        # save_path = os.path.join(UPLOAD_BASE, unique_filename)
        # file_content = await file.read()
        # with open(save_path, "wb") as f:
        #     f.write(file_content)
        # logger.info(f"📄 업로드 파일 저장 완료: {save_path}")
        # 파일 저장
        os.makedirs(UPLOAD_BASE, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        save_path = os.path.join(UPLOAD_BASE, unique_filename)
        file_content = await file.read()
        with open(save_path, "wb") as f:
            f.write(file_content)

        logger.info(f"📄 업로드 파일 저장 완료: {save_path}")

        # ✅ 텍스트 파일이라면 BOM 제거 후 재저장
        if file_ext in [".txt", ".md"]:
            try:
                with open(save_path, "r", encoding="utf-8-sig") as f:
                    text = f.read()
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text)
                logger.info(f"📎 BOM 제거 및 UTF-8 재저장 완료: {save_path}")
            except Exception as e:
                logger.warning(f"⚠ BOM 제거 중 오류: {e}")


        # DB 저장
        docs_data = schemas.DocsCreate(
            title=title or file.filename,
            description=description,
            file_path=save_path,
            common_doc=common_doc,
            department_id=department_id,
            original_file_name=file.filename
        )
        db_docs = crud.create_docs(db=db, docs=docs_data)

        # Qdrant 임베딩
        # existing_ids = get_existing_point_ids()
        chunk_count = advanced_embed_and_upsert(
        save_path,
        department_id=department_id,
        common_doc=common_doc,
        original_file_name=file.filename
        )

        logger.info(f"문서 임베딩 완료: {file.filename} -> {chunk_count} chunks")

        return {
            "success": True,
            "message": "문서가 성공적으로 업로드 및 임베딩되었습니다.",
            "docs": {
                "docs_id": db_docs.docs_id,
                "title": db_docs.title,
                "filename": unique_filename,
                "original_filename": file.filename,
                "file_path": save_path,
                "file_size": len(file_content)
            },
            "chunks_uploaded": chunk_count
        }
    except Exception as e:
        logger.error(f"문서 업로드/임베딩 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 업로드/임베딩 중 오류: {str(e)}")

# @router.delete("/rag/{docs_id}")
# async def delete_document_with_rag(docs_id: int, db: Session = Depends(get_db)):
#     """문서 삭제 + Qdrant 청크 삭제"""
#     logger.info(f"[DELETE] /api/docs/rag/{{docs_id}} 진입: docs_id={docs_id}")
#     file_deleted = False
#     db_deleted = False
#     rag_result = {"removed_from_vector_db": False}
#     try:
#         db_docs = crud.get_docs(db, docs_id=docs_id)
#         if db_docs is None:
#             logger.error(f"삭제 요청된 docs_id={docs_id} 문서를 찾을 수 없습니다.")
#             raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

#         # 파일 삭제
#         if db_docs.file_path and os.path.exists(db_docs.file_path):
#             try:
#                 os.remove(db_docs.file_path)
#                 file_deleted = True
#                 logger.info(f"파일 삭제 완료: {db_docs.file_path}")
#             except Exception as e:
#                 logger.exception(f"파일 삭제 중 오류: {db_docs.file_path}")
#         else:
#             logger.warning(f"삭제 시도 파일이 존재하지 않음: {db_docs.file_path}")

#         # Qdrant 청크 삭제
#         # ✅ Qdrant 청크 삭제 (부서 컬렉션 + 공통 컬렉션)
#         try:
#             normalized_source = f"documents/{os.path.basename(db_docs.file_path)}"
#             filter_must = [
#                 FieldCondition(key="metadata.source", match=MatchValue(value=normalized_source))
#             ]

#             filter_common = Filter(must=filter_must + [
#                 FieldCondition(key="metadata.common_doc", match=MatchValue(value=True))
#             ])
#             filter_dept = Filter(must=filter_must + [
#                 FieldCondition(key="metadata.department_id", match=MatchValue(value=int(db_docs.department_id)))
#             ])

#             # 부서 컬렉션 삭제
#             deleted_dept = client.delete(
#                 collection_name=f"rag_{db_docs.department_id}",
#                 points_selector=filter_dept
#             )
#             logger.info(f"Qdrant 부서 컬렉션 삭제 완료: rag_{db_docs.department_id} -> {deleted_dept}")

#             # 공통 컬렉션도 삭제 시도 (common_doc=True였던 경우)
#             deleted_common = client.delete(
#                 collection_name="rag_common",
#                 points_selector=filter_common
#             )
#             logger.info(f"Qdrant 공통 컬렉션 삭제 완료: rag_common -> {deleted_common}")

#             rag_result = {
#                 "removed_from_vector_db": True,
#                 "deleted_from_department": deleted_dept.deleted,
#                 "deleted_from_common": deleted_common.deleted
#             }
#         except Exception as e:
#             logger.exception("Qdrant 삭제 중 오류")
#             rag_result = {"removed_from_vector_db": False, "error": str(e)}


#         # DB 삭제
#         try:
#             crud.delete_docs(db, docs_id=docs_id)
#             db_deleted = True
#             logger.info(f"DB에서 문서 삭제 완료: docs_id={docs_id}")
#         except Exception as e:
#             logger.exception(f"DB 삭제 중 오류: docs_id={docs_id}")

#         return {
#             "success": True,
#             "message": "문서 및 벡터DB 청크가 성공적으로 삭제되었습니다.",
#             "file_deleted": file_deleted,
#             "db_deleted": db_deleted,
#             "rag": rag_result
#         }
#     except Exception as e:
#         logger.exception(f"문서 삭제 중 오류: docs_id={docs_id}")
#         raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류: {str(e)}")


@router.delete("/rag/{docs_id}")
async def delete_document_with_rag(
    docs_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """문서 삭제 + Qdrant 청크 삭제"""
    logger.info(f"[DELETE] /api/docs/rag/{{docs_id}} 진입: docs_id={docs_id}")
    file_deleted = False
    db_deleted = False
    rag_result = {"removed_from_vector_db": False}
    try:
        db_docs = crud.get_docs(db, docs_id=docs_id)
        if db_docs is None:
            logger.error(f"삭제 요청된 docs_id={docs_id} 문서를 찾을 수 없습니다.")
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        
        logger.warning(
    f"🧾 삭제 요청 정보\n"
    f" - 사용자 이메일: {current_user.email}\n"
    f" - 사용자 부서 ID: {current_user.department_id} ({type(current_user.department_id)})\n"
    f" - 문서 부서 ID: {db_docs.department_id} ({type(db_docs.department_id)})\n"
    f" - 공통 문서 여부: {db_docs.common_doc}"
)


        # 🔐 삭제 권한 확인 (본인 부서만 가능)
        if int(db_docs.department_id) != int(current_user.department_id):
            logger.warning(f"⚠️ 삭제 권한 검사 실패: 문서 부서={db_docs.department_id}({type(db_docs.department_id)}), 사용자 부서={current_user.department_id}({type(current_user.department_id)})")
            raise HTTPException(status_code=403, detail="해당 문서를 삭제할 권한이 없습니다")


        # 파일 삭제
        if db_docs.file_path and os.path.exists(db_docs.file_path):
            try:
                os.remove(db_docs.file_path)
                file_deleted = True
                logger.info(f"파일 삭제 완료: {db_docs.file_path}")
            except Exception as e:
                logger.exception(f"파일 삭제 중 오류: {db_docs.file_path}")
        else:
            logger.warning(f"삭제 시도 파일이 존재하지 않음: {db_docs.file_path}")

        # Qdrant 청크 삭제
        try:
            normalized_source = f"documents/{os.path.basename(db_docs.file_path)}"
            filter_must = [
                FieldCondition(key="metadata.source", match=MatchValue(value=normalized_source))
            ]

            filter_common = Filter(must=filter_must + [
                FieldCondition(key="metadata.common_doc", match=MatchValue(value=True))
            ])
            filter_dept = Filter(must=filter_must + [
                FieldCondition(key="metadata.department_id", match=MatchValue(value=int(db_docs.department_id)))
            ])

            deleted_dept = client.delete(
                collection_name=f"rag_{db_docs.department_id}",
                points_selector=filter_dept
            )
            logger.info(f"Qdrant 부서 컬렉션 삭제 완료: rag_{db_docs.department_id} -> {deleted_dept}")

            deleted_common = client.delete(
                collection_name="rag_common",
                points_selector=filter_common
            )
            logger.info(f"Qdrant 공통 컬렉션 삭제 완료: rag_common -> {deleted_common}")

            rag_result = {
                "removed_from_vector_db": True,
                "deleted_from_department": deleted_dept.deleted,
                "deleted_from_common": deleted_common.deleted
            }
        except Exception as e:
            logger.exception("Qdrant 삭제 중 오류")
            rag_result = {"removed_from_vector_db": False, "error": str(e)}

        # DB 삭제
        try:
            crud.delete_docs(db, docs_id=docs_id)
            db_deleted = True
            logger.info(f"DB에서 문서 삭제 완료: docs_id={docs_id}")
        except Exception as e:
            logger.exception(f"DB 삭제 중 오류: docs_id={docs_id}")

        return {
            "success": True,
            "message": "문서 및 벡터DB 청크가 성공적으로 삭제되었습니다.",
            "file_deleted": file_deleted,
            "db_deleted": db_deleted,
            "rag": rag_result
        }

    except Exception as e:
        logger.exception(f"문서 삭제 중 오류: docs_id={docs_id}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류: {str(e)}")



@router.get("/", response_model=List[schemas.Docs])
async def get_all_docs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """문서 목록 조회"""
    return crud.get_all_docs(db, skip=skip, limit=limit)

@router.get("/{docs_id}", response_model=schemas.Docs)
async def get_docs(docs_id: int, db: Session = Depends(get_db)):
    """특정 문서 조회"""
    db_docs = crud.get_docs(db, docs_id=docs_id)
    if db_docs is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    return db_docs

# @router.get("/department/{department_id}", response_model=List[schemas.Docs])
# async def get_docs_by_department(department_id: int, db: Session = Depends(get_db)):
#     """부서별 문서 조회"""
#     db_department = crud.get_department(db, department_id=department_id)
#     if db_department is None:
#         raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
#     return crud.get_docs_by_department(db, department_id=department_id)

@router.get("/department/{department_id}", response_model=List[schemas.Docs])
async def get_docs_by_department(department_id: int, db: Session = Depends(get_db)):
    """부서별 문서 + 공통 문서 조회"""
    db_department = crud.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    return crud.get_department_documents(db, department_id=department_id, include_common=True)



@router.get("/common/", response_model=List[schemas.Docs])
async def get_common_docs(db: Session = Depends(get_db)):
    """공용 문서 조회"""
    return crud.get_common_docs(db)

@router.get("/rag/health")
async def rag_docs_health():
    return {"rag_available": True, "status": "healthy", "message": "RAG 문서 처리가 활성화됨"}

# @router.get("/download/{docs_id}")
# async def download_document(docs_id: int):
#     """문서 다운로드"""
#     if not RAG_AVAILABLE:
#         raise HTTPException(status_code=500, detail="RAG 시스템이 로드되지 않았습니다.")
    
#     try:
#         with get_db_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute("""
#                 SELECT file_path, original_file_name 
#                 FROM core_docs 
#                 WHERE docs_id = ?
#             """, (docs_id,))
#             row = cursor.fetchone()

#             if not row:
#                 raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

#             file_path = row["file_path"]
#             original_name = row["original_file_name"] or "downloaded_file"

#             abs_path = os.path.abspath(file_path)
#             if not os.path.exists(abs_path):
#                 raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")

#             # 확장자 보완
#             if not os.path.splitext(original_name)[1]:
#                 ext = os.path.splitext(abs_path)[1]
#                 if ext:
#                     original_name += ext

#             # 한글 포함 대응
#             encoded_filename = quote(original_name)

#             return FileResponse(
#                 path=abs_path,
#                 media_type='application/octet-stream',
#                 headers={
#                     "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
#                 }
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/download/{docs_id}")
async def download_document(docs_id: int, db: Session = Depends(get_db)):
    """문서 다운로드 API"""
    db_docs = crud.get_docs(db, docs_id=docs_id)
    if db_docs is None or not db_docs.file_path:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if not os.path.exists(db_docs.file_path):
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")

    # 원래 파일명 (Content-Disposition용)
    filename = db_docs.original_file_name or os.path.basename(db_docs.file_path)

    return FileResponse(
        path=db_docs.file_path,
        media_type='application/octet-stream',
        filename=filename
    )
