from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/task-assigns", tags=["task-assigns"])

@router.post("/", response_model=schemas.TaskAssign)
def create_task_assign(task_assign: schemas.TaskAssignCreate, db: Session = Depends(get_db)):
    """과제 할당 생성"""
    # 사용자 존재 확인
    db_user = crud.get_user(db=db, user_id=task_assign.user_id)
    if not db_user:
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    
    # 멘토십 존재 확인
    db_mentorship = crud.get_mentorship(db=db, mentorship_id=task_assign.mentorship_id)
    if not db_mentorship:
        raise HTTPException(status_code=400, detail="존재하지 않는 멘토십입니다.")
    
    return crud.create_task_assign(db=db, task_assign=task_assign)

@router.get("/", response_model=List[schemas.TaskAssign])
def read_task_assigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """과제 할당 목록 조회"""
    task_assigns = crud.get_task_assigns(db=db, skip=skip, limit=limit)
    return task_assigns

@router.get("/{task_assign_id}", response_model=schemas.TaskAssign)
def read_task_assign(task_assign_id: int, db: Session = Depends(get_db)):
    """과제 할당 조회"""
    db_task_assign = crud.get_task_assign(db=db, task_assign_id=task_assign_id)
    if db_task_assign is None:
        raise HTTPException(status_code=404, detail="과제 할당을 찾을 수 없습니다.")
    return db_task_assign

@router.put("/{task_assign_id}", response_model=schemas.TaskAssign)
def update_task_assign(task_assign_id: int, task_assign: schemas.TaskAssignUpdate, db: Session = Depends(get_db)):
    """과제 할당 수정"""
    # 사용자 존재 확인 (user_id가 변경되는 경우)
    if task_assign.user_id:
        db_user = crud.get_user(db=db, user_id=task_assign.user_id)
        if not db_user:
            raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    
    # 멘토십 존재 확인 (mentorship_id가 변경되는 경우)
    if task_assign.mentorship_id:
        db_mentorship = crud.get_mentorship(db=db, mentorship_id=task_assign.mentorship_id)
        if not db_mentorship:
            raise HTTPException(status_code=400, detail="존재하지 않는 멘토십입니다.")
    
    db_task_assign = crud.update_task_assign(db=db, task_assign_id=task_assign_id, task_assign=task_assign)
    if db_task_assign is None:
        raise HTTPException(status_code=404, detail="과제 할당을 찾을 수 없습니다.")
    return db_task_assign

@router.delete("/{task_assign_id}")
def delete_task_assign(task_assign_id: int, db: Session = Depends(get_db)):
    """과제 할당 삭제"""
    db_task_assign = crud.delete_task_assign(db=db, task_assign_id=task_assign_id)
    if db_task_assign is None:
        raise HTTPException(status_code=404, detail="과제 할당을 찾을 수 없습니다.")
    return {"message": "과제 할당이 성공적으로 삭제되었습니다."}

@router.get("/user/{user_id}", response_model=List[schemas.TaskAssign])
def read_task_assigns_by_user(user_id: int, db: Session = Depends(get_db)):
    """사용자별 과제 할당 목록 조회"""
    task_assigns = crud.get_task_assigns_by_user(db=db, user_id=user_id)
    return task_assigns

@router.get("/mentorship/{mentorship_id}", response_model=List[schemas.TaskAssign])
def read_task_assigns_by_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십별 과제 할당 목록 조회"""
    task_assigns = crud.get_task_assigns_by_mentorship(db=db, mentorship_id=mentorship_id)
    return task_assigns

@router.get("/status/{status}", response_model=List[schemas.TaskAssign])
def read_task_assigns_by_status(status: int, db: Session = Depends(get_db)):
    """상태별 과제 할당 목록 조회"""
    task_assigns = crud.get_task_assigns_by_status(db=db, status=status)
    return task_assigns 