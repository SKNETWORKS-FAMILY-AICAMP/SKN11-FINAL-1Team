from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/departments", tags=["departments"])

@router.post("/", response_model=schemas.Department)
def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    """부서 생성"""
    # 회사 존재 확인
    db_company = crud.get_company(db=db, company_id=department.company_id)
    if not db_company:
        raise HTTPException(status_code=400, detail="존재하지 않는 회사입니다.")
    
    return crud.create_department(db=db, department=department)

@router.get("/", response_model=List[schemas.Department])
def read_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """부서 목록 조회"""
    departments = crud.get_departments(db=db, skip=skip, limit=limit)
    return departments

@router.get("/{department_id}", response_model=schemas.Department)
def read_department(department_id: int, db: Session = Depends(get_db)):
    """부서 조회"""
    db_department = crud.get_department(db=db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    return db_department

@router.put("/{department_id}", response_model=schemas.Department)
def update_department(department_id: int, department: schemas.DepartmentUpdate, db: Session = Depends(get_db)):
    """부서 수정"""
    # 회사 존재 확인 (company_id가 변경되는 경우)
    if department.company_id:
        db_company = crud.get_company(db=db, company_id=department.company_id)
        if not db_company:
            raise HTTPException(status_code=400, detail="존재하지 않는 회사입니다.")
    
    db_department = crud.update_department(db=db, department_id=department_id, department=department)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    return db_department

@router.delete("/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    """부서 삭제"""
    db_department = crud.delete_department(db=db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    return {"message": "부서가 성공적으로 삭제되었습니다."}

@router.get("/{department_id}/users", response_model=List[schemas.User])
def read_department_users(department_id: int, db: Session = Depends(get_db)):
    """부서 소속 사용자 목록 조회"""
    users = crud.get_users_by_department(db=db, department_id=department_id)
    return users

@router.get("/{department_id}/curriculums", response_model=List[schemas.Curriculum])
def read_department_curriculums(department_id: int, db: Session = Depends(get_db)):
    """부서 소속 커리큘럼 목록 조회"""
    curriculums = crud.get_curriculums_by_department(db=db, department_id=department_id)
    return curriculums 