from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import logging
from urllib.parse import quote
from datetime import datetime
import sys

# FastAPI 내부 임포트
from database import get_db
from fastapi import Depends

# RAG 시스템 임포트
RAG_AVAILABLE = False
client = None
COLLECTION_NAME = None
advanced_embed_and_upsert = None
get_existing_point_ids = None
get_db_connection = None

def initialize_rag_for_documents():
    """문서 관리용 RAG 시스템 초기화"""
    global RAG_AVAILABLE, client, COLLECTION_NAME, advanced_embed_and_upsert, get_existing_point_ids, get_db_connection
    
    # 절대 경로로 Django 프로젝트 경로 찾기
    current_file = os.path.abspath(__file__)
    fast_api_dir = os.path.dirname(os.path.dirname(current_file))  # fast_api 디렉토리
    project_root = os.path.dirname(fast_api_dir)  # final_prj 디렉토리
    django_rag_path = os.path.join(project_root, "django_prj", "onboarding_quest")
    
    logging.info(f"문서 관리 RAG 시스템 초기화 시도 - 경로: {django_rag_path}")
    
    if django_rag_path not in sys.path:
        sys.path.insert(0, django_rag_path)
    
    try:
        # RAG 모듈 import
        rag_module = __import__('rag_agent_graph_db_v3_finaltemp_v2')
        client = getattr(rag_module, 'client')
        COLLECTION_NAME = getattr(rag_module, 'COLLECTION_NAME')
        get_db_connection = getattr(rag_module, 'get_db_connection')
        
        # 임베딩 모듈 import
        embed_module = __import__('embed_and_upsert')
        advanced_embed_and_upsert = getattr(embed_module, 'advanced_embed_and_upsert')
        get_existing_point_ids = getattr(embed_module, 'get_existing_point_ids')
        
        RAG_AVAILABLE = True
        logging.info("✅ 문서 관리용 RAG 시스템 초기화 성공")
        
    except Exception as e:
        logging.warning(f"⚠️ 문서 관리용 RAG 시스템 초기화 실패: {e}")
        RAG_AVAILABLE = False

# 초기화 실행
initialize_rag_for_documents()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# 업로드 기본 경로
UPLOAD_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "django_prj", "onboarding_quest", "uploaded_docs")

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    department_id: int = Form(...),
    common_doc: bool = Form(False),
    original_file_name: str = Form(""),
    description: str = Form(""),
):
    """문서 업로드 및 임베딩 처리"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=500, detail="RAG 시스템이 로드되지 않았습니다.")
    
    try:
        # 1. 파일 저장
        os.makedirs(UPLOAD_BASE, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        save_path = os.path.join(UPLOAD_BASE, unique_filename)

        with open(save_path, "wb") as f:
            f.write(await file.read())

        logger.info(f"📄 업로드 파일 저장 완료: {save_path}")

        # 2. 임베딩 처리
        existing_ids = get_existing_point_ids()
        chunk_count = advanced_embed_and_upsert(
            save_path,
            existing_ids,
            department_id=department_id,
            common_doc=common_doc,
            original_file_name=original_file_name or file.filename
        )

        # 3. DB에 삽입
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO core_docs 
                (department_id, title, description, file_path, common_doc, original_file_name, create_time) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                department_id,
                original_file_name or file.filename,
                description,
                save_path,
                int(common_doc),
                original_file_name or file.filename,
                datetime.now().isoformat()
            ))
            docs_id = cursor.lastrowid

        return JSONResponse({
            "success": True,
            "chunks_uploaded": chunk_count,
            "original_file": file.filename,
            "saved_path": save_path,
            "docs_id": docs_id
        })

    except Exception as e:
        logger.error(f"📄 문서 업로드 처리 중 오류: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/delete")
async def delete_document(
    docs_id: int = Form(...),
    department_id: int = Form(...)
):
    """문서 삭제"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=500, detail="RAG 시스템이 로드되지 않았습니다.")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM core_docs WHERE docs_id = ? AND department_id = ?", (docs_id, department_id))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
            file_path = row["file_path"]
            abs_path = os.path.abspath(file_path)

            # 실제 파일 삭제
            if os.path.exists(abs_path):
                os.remove(abs_path)

            # Qdrant에서 삭제
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            delete_filter = Filter(must=[
                FieldCondition(key="metadata.source", match=MatchValue(value=abs_path)),
                FieldCondition(key="metadata.department_id", match=MatchValue(value=department_id))
            ])
            client.delete(collection_name=COLLECTION_NAME, points_selector=delete_filter)

            # DB에서 삭제
            cursor.execute("DELETE FROM core_docs WHERE docs_id = ? AND department_id = ?", (docs_id, department_id))

        return {"success": True, "message": "문서 및 Qdrant 청크 삭제 완료"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/update")
async def update_document(
    docs_id: int = Form(...),
    department_id: int = Form(...),
    tags: str = Form(""),
    description: str = Form(""),
    common_doc: bool = Form(False)
):
    """문서 정보 수정"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=500, detail="RAG 시스템이 로드되지 않았습니다.")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE core_docs
                SET tags = ?, description = ?, common_doc = ?
                WHERE docs_id = ? AND department_id = ?
            """, (tags, description, int(common_doc), docs_id, department_id))

        return {"success": True, "message": "문서 정보가 수정되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/list")
async def list_documents(department_id: int = Query(...)):
    """문서 목록 조회"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=500, detail="RAG 시스템이 로드되지 않았습니다.")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, dept.department_name as department_name
                FROM core_docs d
                LEFT JOIN core_department dept ON d.department_id = dept.department_id
                WHERE d.department_id = ? OR d.common_doc = 1
            """, (department_id,))
            rows = cursor.fetchall()
            docs = [dict(row) for row in rows]

        return {"success": True, "docs": docs}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/download/{docs_id}")
async def download_document(docs_id: int):
    """문서 다운로드"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=500, detail="RAG 시스템이 로드되지 않았습니다.")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_path, original_file_name 
                FROM core_docs 
                WHERE docs_id = ?
            """, (docs_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

            file_path = row["file_path"]
            original_name = row["original_file_name"] or "downloaded_file"

            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")

            # 확장자 보완
            if not os.path.splitext(original_name)[1]:
                ext = os.path.splitext(abs_path)[1]
                if ext:
                    original_name += ext

            # 한글 포함 대응
            encoded_filename = quote(original_name)

            return FileResponse(
                path=abs_path,
                media_type='application/octet-stream',
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
