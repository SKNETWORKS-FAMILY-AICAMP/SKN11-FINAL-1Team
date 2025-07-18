from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db
import os
from datetime import datetime

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
