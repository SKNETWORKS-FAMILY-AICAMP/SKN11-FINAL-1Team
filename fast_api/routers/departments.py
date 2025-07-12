from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.post("/", response_model=schemas.Department)
async def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    """새 부서 생성"""
    # 회사 존재 확인
    db_company = crud.get_company(db, company_id=department.company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다")
    
    return crud.create_department(db=db, department=department)


@router.get("/", response_model=List[schemas.Department])
async def get_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """부서 목록 조회"""
    departments = crud.get_departments(db, skip=skip, limit=limit)
    return departments


@router.get("/{department_id}", response_model=schemas.Department)
async def get_department(department_id: int, db: Session = Depends(get_db)):
    """특정 부서 조회"""
    db_department = crud.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    return db_department


@router.put("/{department_id}", response_model=schemas.Department)
async def update_department(department_id: int, department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    """부서 정보 수정"""
    db_department = crud.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    return crud.update_department(db=db, department_id=department_id, department_update=department)


@router.delete("/{department_id}")
async def delete_department(department_id: int, db: Session = Depends(get_db)):
    """부서 삭제"""
    db_department = crud.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    crud.delete_department(db, department_id=department_id)
    return {"message": "부서가 성공적으로 삭제되었습니다"} 