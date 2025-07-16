from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path

from app.database import get_db
from app.models.user import Docs
from app.models.department import Department
from app.schemas.docs import DocsCreate, DocsResponse, DocsUpdate
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter()

@router.post("/upload", response_model=DocsResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    common_doc: bool = Form(False),
    department_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """문서 업로드 (임시로 인증 없이)"""
    try:
        # 파일 크기 검사
        if file.size and file.size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB까지 업로드 가능합니다."
            )
        
        # 업로드 디렉토리 생성
        upload_dir = Path(settings.UPLOAD_DIR) / "documents"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 데이터베이스에 문서 정보 저장
        doc = Docs(
            title=title,
            description=description or "",
            file_path=str(file_path),
            common_doc=common_doc,
            department_id=department_id
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        return DocsResponse(
            docs_id=doc.docs_id,
            title=doc.title,
            description=doc.description,
            file_path=doc.file_path,
            common_doc=doc.common_doc,
            department_id=doc.department_id,
            create_time=doc.create_time
        )
        
    except Exception as e:
        # 업로드 실패 시 파일 삭제
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}")

@router.get("/", response_model=List[DocsResponse])
async def get_documents(
    common_only: bool = False,
    db: Session = Depends(get_db)
):
    """문서 목록 조회 (임시로 인증 없이)"""
    query = db.query(Docs)
    
    if common_only:
        query = query.filter(Docs.common_doc == True)
    
    docs = query.order_by(Docs.create_time.desc()).all()
    
    return [DocsResponse(
        docs_id=doc.docs_id,
        title=doc.title,
        description=doc.description,
        file_path=doc.file_path,
        common_doc=doc.common_doc,
        department_id=doc.department_id,
        create_time=doc.create_time
    ) for doc in docs]

@router.get("/{doc_id}", response_model=DocsResponse)
async def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """특정 문서 조회"""
    doc = db.query(Docs).filter(Docs.docs_id == doc_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    
    # 권한 확인
    if not doc.common_doc and doc.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="이 문서에 접근할 권한이 없습니다.")
    
    return DocsResponse(
        docs_id=doc.docs_id,
        title=doc.title,
        description=doc.description,
        file_path=doc.file_path,
        common_doc=doc.common_doc,
        department_id=doc.department_id,
        create_time=doc.create_time
    )

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """문서 삭제"""
    doc = db.query(Docs).filter(Docs.docs_id == doc_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    
    # 권한 확인 (같은 부서 또는 관리자)
    if doc.department_id != current_user.department_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="이 문서를 삭제할 권한이 없습니다.")
    
    # 파일 삭제
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    # 데이터베이스에서 삭제
    db.delete(doc)
    db.commit()
    
    return {"message": "문서가 성공적으로 삭제되었습니다."}

@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """문서 다운로드"""
    doc = db.query(Docs).filter(Docs.docs_id == doc_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    
    # 권한 확인
    if not doc.common_doc and doc.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="이 문서에 접근할 권한이 없습니다.")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    return FileResponse(
        path=doc.file_path,
        filename=doc.title,
        media_type='application/octet-stream'
    ) 