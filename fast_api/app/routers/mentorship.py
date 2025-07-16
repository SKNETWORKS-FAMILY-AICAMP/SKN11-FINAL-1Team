from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import Mentorship, User, TaskAssign, Curriculum, TaskManage, Company, Department
from app.schemas.mentorship import (
    MentorshipCreate, MentorshipUpdate, MentorshipResponse,
    MentorshipWithRelations, MentorshipList,
    TaskAssignCreate, TaskAssignResponse
)
from app.schemas.user import UserResponse
from app.dependencies import get_current_user, require_admin
from sqlalchemy import func, or_, and_

router = APIRouter(prefix="/mentorships", tags=["mentorships"])

@router.post("/", response_model=MentorshipResponse)
def create_mentorship(
    mentorship: MentorshipCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """멘토쉽 생성"""
    # 멘토와 멘티 존재 확인
    mentor = db.query(User).filter(User.user_id == mentorship.mentor_id).first()
    mentee = db.query(User).filter(User.user_id == mentorship.mentee_id).first()
    
    if not mentor:
        raise HTTPException(status_code=404, detail="멘토를 찾을 수 없습니다.")
    if not mentee:
        raise HTTPException(status_code=404, detail="멘티를 찾을 수 없습니다.")
    
    # 역할 확인
    if mentor.role != "mentor":
        raise HTTPException(status_code=400, detail="멘토 역할이 아닙니다.")
    if mentee.role != "mentee":
        raise HTTPException(status_code=400, detail="멘티 역할이 아닙니다.")
    
    # 활성화된 멘토쉽이 이미 있는지 확인
    existing = db.query(Mentorship).filter(
        and_(
            Mentorship.mentor_id == mentorship.mentor_id,
            Mentorship.mentee_id == mentorship.mentee_id,
            Mentorship.is_active == True
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="이미 활성화된 멘토쉽이 있습니다.")
    
    # 멘토쉽 생성
    db_mentorship = Mentorship(**mentorship.dict())
    db.add(db_mentorship)
    db.commit()
    db.refresh(db_mentorship)
    
    # 커리큘럼 기반으로 과제 할당 생성
    create_tasks_from_curriculum(db, db_mentorship)
    
    return db_mentorship

@router.get("/", response_model=MentorshipList)
def get_mentorships(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    mentor_id: Optional[int] = None,
    mentee_id: Optional[int] = None,
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """멘토쉽 목록 조회"""
    query = db.query(Mentorship)
    
    # 권한 확인 - 관리자가 아닌 경우 자신과 관련된 멘토쉽만
    if not current_user.is_admin:
        query = query.filter(
            or_(
                Mentorship.mentor_id == current_user.user_id,
                Mentorship.mentee_id == current_user.user_id
            )
        )
    
    if is_active is not None:
        query = query.filter(Mentorship.is_active == is_active)
    
    if mentor_id:
        query = query.filter(Mentorship.mentor_id == mentor_id)
    
    if mentee_id:
        query = query.filter(Mentorship.mentee_id == mentee_id)
    
    if search:
        # 멘토나 멘티 이름으로 검색
        mentors = db.query(User).filter(
            or_(
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        ).all()
        user_ids = [user.user_id for user in mentors]
        query = query.filter(
            or_(
                Mentorship.mentor_id.in_(user_ids),
                Mentorship.mentee_id.in_(user_ids)
            )
        )
    
    if department_id:
        # 부서 필터
        dept_users = db.query(User).filter(User.department_id == department_id).all()
        user_ids = [user.user_id for user in dept_users]
        query = query.filter(
            or_(
                Mentorship.mentor_id.in_(user_ids),
                Mentorship.mentee_id.in_(user_ids)
            )
        )
    
    total = query.count()
    mentorships = query.offset(skip).limit(limit).all()
    
    # 멘토쉽에 사용자 정보 추가
    all_users = {user.user_id: user for user in db.query(User).all()}
    for mentorship in mentorships:
        mentorship.mentor = all_users.get(mentorship.mentor_id)
        mentorship.mentee = all_users.get(mentorship.mentee_id)
    
    return MentorshipList(
        mentorships=mentorships,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/{mentorship_id}", response_model=MentorshipWithRelations)
def get_mentorship(
    mentorship_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """멘토쉽 상세 조회"""
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
    if not mentorship:
        raise HTTPException(status_code=404, detail="멘토쉽을 찾을 수 없습니다.")
    
    # 권한 확인
    if not current_user.is_admin and mentorship.mentor_id != current_user.user_id and mentorship.mentee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return mentorship

@router.put("/{mentorship_id}", response_model=MentorshipResponse)
def update_mentorship(
    mentorship_id: int,
    mentorship_update: MentorshipUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """멘토쉽 수정"""
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
    if not mentorship:
        raise HTTPException(status_code=404, detail="멘토쉽을 찾을 수 없습니다.")
    
    # 업데이트
    for field, value in mentorship_update.dict(exclude_unset=True).items():
        setattr(mentorship, field, value)
    
    db.commit()
    db.refresh(mentorship)
    return mentorship

@router.delete("/{mentorship_id}")
def delete_mentorship(
    mentorship_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """멘토쉽 삭제"""
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
    if not mentorship:
        raise HTTPException(status_code=404, detail="멘토쉽을 찾을 수 없습니다.")
    
    db.delete(mentorship)
    db.commit()
    return {"message": "멘토쉽이 삭제되었습니다."}

@router.get("/mentors/available", response_model=List[UserResponse])
def get_available_mentors(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용 가능한 멘토 목록"""
    query = db.query(User).filter(
        User.role == "mentor",
        User.is_active == True
    )
    
    if department_id:
        query = query.filter(User.department_id == department_id)
    
    # 관리자가 아닌 경우 같은 회사만
    if not current_user.is_admin:
        query = query.filter(User.company_id == current_user.company_id)
    
    mentors = query.offset(skip).limit(limit).all()
    return mentors

@router.get("/mentees/available", response_model=List[UserResponse])
def get_available_mentees(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용 가능한 멘티 목록"""
    query = db.query(User).filter(
        User.role == "mentee",
        User.is_active == True
    )
    
    if department_id:
        query = query.filter(User.department_id == department_id)
    
    # 관리자가 아닌 경우 같은 회사만
    if not current_user.is_admin:
        query = query.filter(User.company_id == current_user.company_id)
    
    mentees = query.offset(skip).limit(limit).all()
    return mentees

@router.get("/mentor/{mentor_id}/mentees", response_model=List[UserResponse])
def get_mentor_mentees(
    mentor_id: int,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """멘토의 멘티 목록"""
    # 권한 확인
    if not current_user.is_admin and mentor_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    query = db.query(Mentorship).filter(Mentorship.mentor_id == mentor_id)
    
    if is_active is not None:
        query = query.filter(Mentorship.is_active == is_active)
    
    mentorships = query.all()
    
    # 멘티 정보 가져오기
    mentee_ids = [m.mentee_id for m in mentorships]
    mentees = db.query(User).filter(User.user_id.in_(mentee_ids)).all()
    
    return mentees

@router.get("/mentee/{mentee_id}/mentors", response_model=List[UserResponse])
def get_mentee_mentors(
    mentee_id: int,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """멘티의 멘토 목록"""
    # 권한 확인
    if not current_user.is_admin and mentee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    query = db.query(Mentorship).filter(Mentorship.mentee_id == mentee_id)
    
    if is_active is not None:
        query = query.filter(Mentorship.is_active == is_active)
    
    mentorships = query.all()
    
    # 멘토 정보 가져오기
    mentor_ids = [m.mentor_id for m in mentorships]
    mentors = db.query(User).filter(User.user_id.in_(mentor_ids)).all()
    
    return mentors

@router.post("/{mentorship_id}/clone-curriculum")
def clone_curriculum_to_mentorship(
    mentorship_id: int,
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """커리큘럼을 멘토쉽에 복사"""
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
    if not mentorship:
        raise HTTPException(status_code=404, detail="멘토쉽을 찾을 수 없습니다.")
    
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다.")
    
    # 기존 과제 삭제
    db.query(TaskAssign).filter(TaskAssign.mentorship_id == mentorship_id).delete()
    
    # 커리큘럼의 과제들을 복사
    task_manages = db.query(TaskManage).filter(TaskManage.curriculum_id == curriculum_id).all()
    
    for task_manage in task_manages:
        task_assign = TaskAssign(
            mentorship_id=mentorship_id,
            title=task_manage.title,
            description=task_manage.description,
            guideline=task_manage.guideline,
            week=task_manage.week,
            order=task_manage.order,
            priority=task_manage.priority,
            status="진행 전"
        )
        db.add(task_assign)
    
    # 멘토쉽 정보 업데이트
    mentorship.curriculum_title = curriculum.curriculum_title
    mentorship.total_weeks = curriculum.total_weeks
    
    db.commit()
    return {"message": "커리큘럼이 복사되었습니다."}

@router.get("/stats/overview")
def get_mentorship_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """멘토쉽 통계"""
    # 전체 멘토쉽 수
    total_mentorships = db.query(Mentorship).count()
    
    # 활성 멘토쉽 수
    active_mentorships = db.query(Mentorship).filter(Mentorship.is_active == True).count()
    
    # 멘토 수
    total_mentors = db.query(User).filter(User.role == "mentor", User.is_active == True).count()
    
    # 멘티 수
    total_mentees = db.query(User).filter(User.role == "mentee", User.is_active == True).count()
    
    # 완료된 과제 수
    completed_tasks = db.query(TaskAssign).filter(TaskAssign.status == "완료").count()
    
    # 진행 중인 과제 수
    in_progress_tasks = db.query(TaskAssign).filter(TaskAssign.status == "진행 중").count()
    
    return {
        "total_mentorships": total_mentorships,
        "active_mentorships": active_mentorships,
        "total_mentors": total_mentors,
        "total_mentees": total_mentees,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks
    }

def create_tasks_from_curriculum(db: Session, mentorship: Mentorship):
    """커리큘럼에서 과제 생성"""
    curriculum = db.query(Curriculum).filter(
        Curriculum.curriculum_title == mentorship.curriculum_title
    ).first()
    
    if not curriculum:
        return
    
    # 커리큘럼의 과제들 복사
    task_manages = db.query(TaskManage).filter(TaskManage.curriculum_id == curriculum.curriculum_id).all()
    
    for task_manage in task_manages:
        task_assign = TaskAssign(
            mentorship_id=mentorship.mentorship_id,
            title=task_manage.title,
            description=task_manage.description,
            guideline=task_manage.guideline,
            week=task_manage.week,
            order=task_manage.order,
            priority=task_manage.priority,
            status="진행 전"
        )
        db.add(task_assign)
    
    db.commit()
