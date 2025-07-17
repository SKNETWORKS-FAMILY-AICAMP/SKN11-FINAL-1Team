from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("/", response_model=schemas.Template)
async def create_template(template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    """새 템플릿 생성"""
    # 부서 존재 확인
    db_department = crud.get_department(db, department_id=template.department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    return crud.create_template(db=db, template=template)


@router.get("/", response_model=List[schemas.Template])
async def get_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """템플릿 목록 조회"""
    templates = crud.get_templates(db, skip=skip, limit=limit)
    return templates


@router.get("/{template_id}", response_model=schemas.Template)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """특정 템플릿 조회"""
    db_template = crud.get_template(db, template_id=template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    return db_template


@router.put("/{template_id}", response_model=schemas.Template)
async def update_template(template_id: int, template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    """템플릿 정보 수정"""
    db_template = crud.get_template(db, template_id=template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    return crud.update_template(db=db, template_id=template_id, template_update=template)


@router.delete("/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    """템플릿 삭제"""
    db_template = crud.get_template(db, template_id=template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    crud.delete_template(db, template_id=template_id)
    return {"message": "템플릿이 성공적으로 삭제되었습니다"} 