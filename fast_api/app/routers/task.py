from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import (
    TaskAssign, Mentorship, User, TaskManage, Curriculum, 
    Department, Subtask, Memo
)
from app.schemas.mentorship import (
    TaskAssignCreate, TaskAssignUpdate, TaskAssignResponse,
    TaskAssignWithRelations, TaskAssignList, TaskStatus,
    MemoCreate, MemoUpdate, MemoResponse, MemoList
)
from app.schemas.task import (
    TaskManageCreate, TaskManageUpdate, TaskManageResponse,
    TaskManageWithRelations, TaskManageList,
    CurriculumCreate, CurriculumUpdate, CurriculumResponse,
    CurriculumWithRelations, CurriculumList
)
from app.dependencies import get_current_user, require_admin
from sqlalchemy import func
from collections import defaultdict

router = APIRouter(prefix="/tasks", tags=["tasks"])

# TaskAssign 관련 엔드포인트
@router.get("/assigns", response_model=TaskAssignList)
def get_task_assigns(
    skip: int = 0,
    limit: int = 100,
    mentorship_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    week: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """과제 할당 목록 조회"""
    query = db.query(TaskAssign)
    
    if mentorship_id:
        query = query.filter(TaskAssign.mentorship_id == mentorship_id)
    
    if status:
        query = query.filter(TaskAssign.status == status.value)
    
    if week:
        query = query.filter(TaskAssign.week == week)
    
    # 권한 확인 - 관리자가 아닌 경우 자신과 관련된 과제만
    if not current_user.is_admin:
        mentorships = db.query(Mentorship).filter(
            (Mentorship.mentor_id == current_user.user_id) |
            (Mentorship.mentee_id == current_user.user_id)
        ).all()
        mentorship_ids = [m.mentorship_id for m in mentorships]
        query = query.filter(TaskAssign.mentorship_id.in_(mentorship_ids))
    
    query = query.order_by(TaskAssign.week, TaskAssign.order)
    total = query.count()
    task_assigns = query.offset(skip).limit(limit).all()
    
    return TaskAssignList(
        task_assigns=task_assigns,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/assigns/{task_assign_id}", response_model=TaskAssignWithRelations)
def get_task_assign(
    task_assign_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """과제 할당 상세 조회"""
    task_assign = db.query(TaskAssign).filter(TaskAssign.task_assign_id == task_assign_id).first()
    if not task_assign:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    # 권한 확인
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == task_assign.mentorship_id).first()
    if not current_user.is_admin and mentorship.mentor_id != current_user.user_id and mentorship.mentee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return task_assign

@router.put("/assigns/{task_assign_id}", response_model=TaskAssignResponse)
def update_task_assign(
    task_assign_id: int,
    task_update: TaskAssignUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """과제 할당 수정"""
    task_assign = db.query(TaskAssign).filter(TaskAssign.task_assign_id == task_assign_id).first()
    if not task_assign:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    # 권한 확인
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == task_assign.mentorship_id).first()
    if not current_user.is_admin and mentorship.mentor_id != current_user.user_id and mentorship.mentee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    # 업데이트
    for field, value in task_update.dict(exclude_unset=True).items():
        if field == "status" and value:
            setattr(task_assign, field, value.value)
        elif field == "priority" and value:
            setattr(task_assign, field, value.value)
        else:
            setattr(task_assign, field, value)
    
    db.commit()
    db.refresh(task_assign)
    return task_assign

@router.get("/assigns/mentorship/{mentorship_id}/by-week")
def get_tasks_by_week(
    mentorship_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """멘토쉽의 주차별 과제 목록"""
    # 멘토쉽 존재 확인
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
    if not mentorship:
        raise HTTPException(status_code=404, detail="멘토쉽을 찾을 수 없습니다.")
    
    # 권한 확인
    if not current_user.is_admin and mentorship.mentor_id != current_user.user_id and mentorship.mentee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    # 과제 조회
    tasks = db.query(TaskAssign).filter(
        TaskAssign.mentorship_id == mentorship_id
    ).order_by(TaskAssign.week, TaskAssign.order).all()
    
    # 주차별로 그룹핑
    week_tasks = defaultdict(list)
    for task in tasks:
        subtasks = db.query(Subtask).filter(Subtask.task_assign_id == task.task_assign_id).all()
        task_data = {
            "id": task.task_assign_id,
            "title": task.title,
            "description": task.description,
            "guideline": task.guideline,
            "week": task.week,
            "order": task.order,
            "start_date": task.start_date,
            "end_date": task.end_date,
            "status": task.status,
            "priority": task.priority,
            "subtasks": [{"subtask_id": s.subtask_id} for s in subtasks]
        }
        week_tasks[task.week].append(task_data)
    
    # 첫 번째 주의 첫 번째 과제를 기본 선택
    selected_task = None
    if week_tasks:
        first_week = sorted(week_tasks.keys())[0]
        if week_tasks[first_week]:
            selected_task = week_tasks[first_week][0]
    
    return {
        "week_tasks": dict(week_tasks),
        "selected_task": selected_task
    }

# Memo 관련 엔드포인트
@router.post("/assigns/{task_assign_id}/memos", response_model=MemoResponse)
def create_memo(
    task_assign_id: int,
    memo: MemoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """메모 생성"""
    # 과제 존재 확인
    task_assign = db.query(TaskAssign).filter(TaskAssign.task_assign_id == task_assign_id).first()
    if not task_assign:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    # 권한 확인
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == task_assign.mentorship_id).first()
    if not current_user.is_admin and mentorship.mentor_id != current_user.user_id and mentorship.mentee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    db_memo = Memo(
        task_assign_id=task_assign_id,
        user_id=current_user.user_id,
        comment=memo.comment
    )
    db.add(db_memo)
    db.commit()
    db.refresh(db_memo)
    return db_memo

@router.get("/assigns/{task_assign_id}/memos", response_model=MemoList)
def get_task_memos(
    task_assign_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """과제 메모 목록"""
    # 과제 존재 확인
    task_assign = db.query(TaskAssign).filter(TaskAssign.task_assign_id == task_assign_id).first()
    if not task_assign:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    # 권한 확인
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == task_assign.mentorship_id).first()
    if not current_user.is_admin and mentorship.mentor_id != current_user.user_id and mentorship.mentee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    query = db.query(Memo).filter(Memo.task_assign_id == task_assign_id)
    total = query.count()
    memos = query.offset(skip).limit(limit).all()
    
    return MemoList(
        memos=memos,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

# Curriculum 관련 엔드포인트
@router.post("/curriculums", response_model=CurriculumResponse)
def create_curriculum(
    curriculum: CurriculumCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """커리큘럼 생성"""
    db_curriculum = Curriculum(**curriculum.dict())
    db.add(db_curriculum)
    db.commit()
    db.refresh(db_curriculum)
    return db_curriculum

@router.get("/curriculums", response_model=CurriculumList)
def get_curriculums(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    common: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """커리큘럼 목록 조회"""
    query = db.query(Curriculum)
    
    if department_id:
        query = query.filter(Curriculum.department_id == department_id)
    
    if common is not None:
        query = query.filter(Curriculum.common == common)
    
    # 관리자가 아닌 경우 자신의 부서나 공통 커리큘럼만
    if not current_user.is_admin:
        query = query.filter(
            (Curriculum.department_id == current_user.department_id) |
            (Curriculum.common == True)
        )
    
    total = query.count()
    curriculums = query.offset(skip).limit(limit).all()
    
    return CurriculumList(
        curriculums=curriculums,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/curriculums/{curriculum_id}", response_model=CurriculumWithRelations)
def get_curriculum(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """커리큘럼 상세 조회"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다.")
    
    # 권한 확인
    if not current_user.is_admin and not curriculum.common and curriculum.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return curriculum

@router.put("/curriculums/{curriculum_id}", response_model=CurriculumResponse)
def update_curriculum(
    curriculum_id: int,
    curriculum_update: CurriculumUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """커리큘럼 수정"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다.")
    
    # 업데이트
    for field, value in curriculum_update.dict(exclude_unset=True).items():
        setattr(curriculum, field, value)
    
    db.commit()
    db.refresh(curriculum)
    return curriculum

@router.delete("/curriculums/{curriculum_id}")
def delete_curriculum(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """커리큘럼 삭제"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다.")
    
    db.delete(curriculum)
    db.commit()
    return {"message": "커리큘럼이 삭제되었습니다."}

# TaskManage 관련 엔드포인트
@router.post("/manages", response_model=TaskManageResponse)
def create_task_manage(
    task: TaskManageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """과제 템플릿 생성"""
    db_task = TaskManage(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/manages", response_model=TaskManageList)
def get_task_manages(
    skip: int = 0,
    limit: int = 100,
    curriculum_id: Optional[int] = None,
    week: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """과제 템플릿 목록 조회"""
    query = db.query(TaskManage)
    
    if curriculum_id:
        query = query.filter(TaskManage.curriculum_id == curriculum_id)
    
    if week:
        query = query.filter(TaskManage.week == week)
    
    query = query.order_by(TaskManage.week, TaskManage.order)
    total = query.count()
    tasks = query.offset(skip).limit(limit).all()
    
    return TaskManageList(
        tasks=tasks,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/manages/{task_manage_id}", response_model=TaskManageWithRelations)
def get_task_manage(
    task_manage_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """과제 템플릿 상세 조회"""
    task = db.query(TaskManage).filter(TaskManage.task_manage_id == task_manage_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    return task

@router.put("/manages/{task_manage_id}", response_model=TaskManageResponse)
def update_task_manage(
    task_manage_id: int,
    task_update: TaskManageUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """과제 템플릿 수정"""
    task = db.query(TaskManage).filter(TaskManage.task_manage_id == task_manage_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    # 업데이트
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

@router.delete("/manages/{task_manage_id}")
def delete_task_manage(
    task_manage_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """과제 템플릿 삭제"""
    task = db.query(TaskManage).filter(TaskManage.task_manage_id == task_manage_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    db.delete(task)
    db.commit()
    return {"message": "과제가 삭제되었습니다."}
