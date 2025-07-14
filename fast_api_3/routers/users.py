from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """사용자 생성"""
    # 중복 검사
    if user.email:
        db_user = crud.get_user_by_email(db=db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    if user.employee_number:
        db_user = crud.get_user_by_employee_number(db=db, employee_number=user.employee_number)
        if db_user:
            raise HTTPException(status_code=400, detail="이미 존재하는 사번입니다.")
    
    # 회사 존재 확인
    db_company = crud.get_company(db=db, company_id=user.company_id)
    if not db_company:
        raise HTTPException(status_code=400, detail="존재하지 않는 회사입니다.")
    
    # 부서 존재 확인
    db_department = crud.get_department(db=db, department_id=user.department_id)
    if not db_department:
        raise HTTPException(status_code=400, detail="존재하지 않는 부서입니다.")
    
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """사용자 목록 조회"""
    users = crud.get_users(db=db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 조회"""
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return db_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    """사용자 수정"""
    # 회사 존재 확인 (company_id가 변경되는 경우)
    if user.company_id:
        db_company = crud.get_company(db=db, company_id=user.company_id)
        if not db_company:
            raise HTTPException(status_code=400, detail="존재하지 않는 회사입니다.")
    
    # 부서 존재 확인 (department_id가 변경되는 경우)
    if user.department_id:
        db_department = crud.get_department(db=db, department_id=user.department_id)
        if not db_department:
            raise HTTPException(status_code=400, detail="존재하지 않는 부서입니다.")
    
    db_user = crud.update_user(db=db, user_id=user_id, user=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 삭제"""
    db_user = crud.delete_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {"message": "사용자가 성공적으로 삭제되었습니다."}

@router.get("/role/{role}", response_model=List[schemas.User])
def read_users_by_role(role: str, db: Session = Depends(get_db)):
    """역할별 사용자 목록 조회"""
    if role not in ['mentee', 'mentor']:
        raise HTTPException(status_code=400, detail="역할은 mentee 또는 mentor여야 합니다.")
    
    users = crud.get_users_by_role(db=db, role=role)
    return users

@router.get("/email/{email}", response_model=schemas.User)
def read_user_by_email(email: str, db: Session = Depends(get_db)):
    """이메일로 사용자 조회"""
    db_user = crud.get_user_by_email(db=db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return db_user

@router.get("/employee-number/{employee_number}", response_model=schemas.User)
def read_user_by_employee_number(employee_number: int, db: Session = Depends(get_db)):
    """사번으로 사용자 조회"""
    db_user = crud.get_user_by_employee_number(db=db, employee_number=employee_number)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return db_user

@router.get("/{user_id}/task-assigns", response_model=List[schemas.TaskAssign])
def read_user_task_assigns(user_id: int, db: Session = Depends(get_db)):
    """사용자 할당 과제 목록 조회"""
    task_assigns = crud.get_task_assigns_by_user(db=db, user_id=user_id)
    return task_assigns 