from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
import models
from database import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# 태스크 관리 (Template의 태스크들)
@router.post("/manage/", response_model=schemas.TaskManage)
async def create_task_manage(task: schemas.TaskManageCreate, db: Session = Depends(get_db)):
    """새 태스크 관리 생성"""
    return crud.create_task_manage(db=db, task=task)


@router.get("/manage/", response_model=List[schemas.TaskManage])
async def get_task_manages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """태스크 관리 목록 조회"""
    tasks = crud.get_task_manages(db, skip=skip, limit=limit)
    return tasks


@router.get("/manage/{task_id}", response_model=schemas.TaskManage)
async def get_task_manage(task_id: int, db: Session = Depends(get_db)):
    """특정 태스크 관리 조회"""
    db_task = crud.get_task_manage(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    return db_task


@router.put("/manage/{task_id}", response_model=schemas.TaskManage)
async def update_task_manage(task_id: int, task: schemas.TaskManageCreate, db: Session = Depends(get_db)):
    """태스크 관리 수정"""
    db_task = crud.get_task_manage(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    return crud.update_task_manage(db=db, task_id=task_id, task_update=task)


@router.delete("/manage/{task_id}")
async def delete_task_manage(task_id: int, db: Session = Depends(get_db)):
    """태스크 관리 삭제"""
    db_task = crud.get_task_manage(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    
    crud.delete_task_manage(db, task_id=task_id)
    return {"message": "태스크가 성공적으로 삭제되었습니다"}


# 태스크 할당 (사용자에게 할당된 태스크들)
@router.post("/assign/", response_model=schemas.TaskAssign)
async def create_task_assign(task: schemas.TaskAssignCreate, db: Session = Depends(get_db)):
    """새 태스크 할당 생성"""
    # 사용자 존재 확인
    db_user = crud.get_user(db, user_id=task.user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 태스크 관리 존재 확인
    db_task_manage = crud.get_task_manage(db, task_id=task.task_manage_id)
    if db_task_manage is None:
        raise HTTPException(status_code=404, detail="관리 태스크를 찾을 수 없습니다")
    
    return crud.create_task_assign(db=db, task=task)


@router.get("/assigns", response_model=List[schemas.TaskAssign])
async def get_task_assigns_by_mentorship(
    mentorship_id: int = None, 
    user_id: int = None,
    status: str = None,
    week: int = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """태스크 할당 목록 조회 (멘토쉽, 사용자, 상태, 주차별 필터링 지원)"""
    tasks = crud.get_task_assigns_filtered(
        db, 
        mentorship_id=mentorship_id,
        user_id=user_id,
        status=status,
        week=week,
        skip=skip, 
        limit=limit
    )
    return tasks


@router.get("/assign/", response_model=List[schemas.TaskAssign])
async def get_task_assigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """태스크 할당 목록 조회"""
    tasks = crud.get_task_assigns(db, skip=skip, limit=limit)
    return tasks


@router.get("/assign/{task_id}", response_model=schemas.TaskAssign)
async def get_task_assign(task_id: int, db: Session = Depends(get_db)):
    """특정 태스크 할당 조회"""
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    return db_task


@router.put("/assign/{task_id}", response_model=schemas.TaskAssign)
async def update_task_assign(task_id: int, task: schemas.TaskAssignCreate, db: Session = Depends(get_db)):
    """태스크 할당 수정"""
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    return crud.update_task_assign(db=db, task_id=task_id, task_update=task)


@router.delete("/assign/{task_id}")
async def delete_task_assign(task_id: int, db: Session = Depends(get_db)):
    """태스크 할당 삭제"""
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    
    crud.delete_task_assign(db, task_id=task_id)
    return {"message": "할당된 태스크가 성공적으로 삭제되었습니다"}


@router.get("/assign/user/{user_id}", response_model=List[schemas.TaskAssign])
async def get_user_tasks(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """특정 사용자의 할당된 태스크 목록 조회"""
    # 사용자 존재 확인
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    tasks = crud.get_task_assigns_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return tasks


@router.patch("/assign/{task_id}/status")
async def update_task_status(task_id: int, status: int, db: Session = Depends(get_db)):
    """태스크 할당 상태 업데이트"""
    valid_statuses = [0, 1, 2, 3]  # 예: 0=미시작, 1=진행중, 2=완료, 3=보류
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 상태입니다. 가능한 상태: {valid_statuses}")
    
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    
    # 상태만 업데이트
    db_task.status = status
    db.commit()
    db.refresh(db_task)
    
    status_names = {0: "미시작", 1: "진행중", 2: "완료", 3: "보류"}
    return {"message": f"태스크 상태가 '{status_names.get(status, status)}'로 업데이트되었습니다"}


# 하위 태스크 (TaskAssign의 서브태스크)
@router.post("/subtask/", response_model=schemas.TaskAssign)
async def create_subtask(subtask: schemas.TaskAssignCreate, db: Session = Depends(get_db)):
    """새 하위 태스크 생성 (TaskAssign의 서브태스크)"""
    # 부모 태스크 할당 존재 확인
    if subtask.parent_id:
        db_parent_task = crud.get_task_assign(db, task_id=subtask.parent_id)
        if db_parent_task is None:
            raise HTTPException(status_code=404, detail="부모 태스크를 찾을 수 없습니다")
    
    # 멘토십 존재 확인
    db_mentorship = crud.get_mentorship(db, mentorship_id=subtask.mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    
    return crud.create_task_assign(db=db, task=subtask)


# 멘토링과 관련된 태스크 기능
@router.post("/mentorship/", response_model=schemas.Mentorship)
async def create_mentorship(mentorship: schemas.MentorshipCreate, db: Session = Depends(get_db)):
    """새 멘토링 관계 생성"""
    # 멘토와 멘티 존재 확인
    mentor = crud.get_user(db, user_id=mentorship.mentor_id)
    mentee = crud.get_user(db, user_id=mentorship.mentee_id)
    
    if mentor is None or mentor.role != "mentor":
        raise HTTPException(status_code=404, detail="멘토를 찾을 수 없습니다")
    
    if mentee is None or mentee.role != "mentee":
        raise HTTPException(status_code=404, detail="멘티를 찾을 수 없습니다")
    
    return crud.create_mentorship(db=db, mentorship=mentorship)


@router.get("/mentorship/", response_model=List[schemas.Mentorship])
async def get_mentorships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """멘토링 관계 목록 조회"""
    mentorships = crud.get_mentorships(db, skip=skip, limit=limit)
    return mentorships 