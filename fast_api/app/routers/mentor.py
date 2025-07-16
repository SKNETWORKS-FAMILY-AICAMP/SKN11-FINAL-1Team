from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import Mentorship, User, TaskAssign, Curriculum, TaskManage, Department
from app.schemas.mentorship import (
    MentorshipCreate, MentorshipResponse, 
    TaskAssignCreate, TaskAssignResponse
)
from app.schemas.task import (
    CurriculumCreate, CurriculumUpdate, CurriculumResponse,
    TaskManageCreate, TaskManageResponse
)
from app.schemas.user import UserResponse
from app.dependencies import get_current_user
from sqlalchemy import func, or_, and_
from datetime import date
import json

router = APIRouter(prefix="/mentor", tags=["mentor"])

@router.get("/mentees", response_model=List[UserResponse])
async def get_mentees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """현재 멘토쉽이 없는 멘티 목록 조회"""
    try:
        # 현재 활성 멘토쉽이 있는 멘티 ID 목록
        existing_mentee_ids = db.query(Mentorship.mentee_id).filter(
            Mentorship.is_active == True
        ).all()
        existing_mentee_ids = [id[0] for id in existing_mentee_ids]
        
        # 멘토쉽이 없는 멘티들 조회
        mentees = db.query(User).filter(
            User.role == 'mentee',
            User.is_active == True,
            ~User.user_id.in_(existing_mentee_ids)
        ).order_by(User.last_name, User.first_name).all()
        
        return [UserResponse(
            user_id=mentee.user_id,
            email=mentee.email,
            first_name=mentee.first_name,
            last_name=mentee.last_name,
            employee_number=mentee.employee_number,
            role=mentee.role,
            is_active=mentee.is_active,
            department_id=mentee.department_id,
            position=mentee.position,
            join_date=mentee.join_date,
            create_date=mentee.create_date
        ) for mentee in mentees]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"멘티 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/save_curriculum", response_model=Dict[str, Any])
async def save_curriculum(
    curriculum_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """커리큘럼 저장 API"""
    try:
        curriculum_id = curriculum_data.get('curriculum_id')
        curriculum_title = curriculum_data.get('curriculum_title', '').strip()
        curriculum_description = curriculum_data.get('curriculum_description', '').strip()
        week_schedule = curriculum_data.get('week_schedule', '').strip()
        is_common = curriculum_data.get('is_common', False)
        tasks = curriculum_data.get('tasks', [])
        
        # 필수 필드 검증
        if not curriculum_title:
            raise HTTPException(
                status_code=400,
                detail="커리큘럼 제목을 입력해주세요."
            )
        
        # 커리큘럼 생성 또는 업데이트
        if curriculum_id:
            # 기존 커리큘럼 업데이트
            curriculum = db.query(Curriculum).filter(
                Curriculum.curriculum_id == curriculum_id
            ).first()
            
            if not curriculum:
                raise HTTPException(
                    status_code=404,
                    detail="커리큘럼을 찾을 수 없습니다."
                )
            
            # 권한 확인
            if not is_common and curriculum.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=403,
                    detail="권한이 없습니다."
                )
            
            curriculum.curriculum_title = curriculum_title
            curriculum.curriculum_description = curriculum_description
            curriculum.week_schedule = week_schedule
            curriculum.common = is_common
            curriculum.department_id = None if is_common else current_user.department_id
            
        else:
            # 새 커리큘럼 생성
            curriculum = Curriculum(
                curriculum_title=curriculum_title,
                curriculum_description=curriculum_description,
                week_schedule=week_schedule,
                common=is_common,
                department_id=None if is_common else current_user.department_id
            )
            db.add(curriculum)
        
        db.commit()
        db.refresh(curriculum)
        
        # 기존 작업 삭제
        if curriculum_id:
            db.query(TaskManage).filter(
                TaskManage.curriculum_id == curriculum.curriculum_id
            ).delete()
            db.commit()
        
        # 새 작업 추가
        for task_data in tasks:
            task = TaskManage(
                curriculum_id=curriculum.curriculum_id,
                title=task_data.get('title', ''),
                description=task_data.get('description', ''),
                week=task_data.get('week', 1),
                order=task_data.get('order', 1),
                exp=task_data.get('exp', 0),
                priority=task_data.get('priority', '중'),
                estimated_hours=task_data.get('estimated_hours', 0)
            )
            db.add(task)
        
        db.commit()
        
        # 총 주차 수 계산
        max_week = max([task.get('week', 1) for task in tasks]) if tasks else 1
        curriculum.total_weeks = max_week
        db.commit()
        
        return {
            'success': True,
            'message': '커리큘럼이 성공적으로 저장되었습니다.',
            'curriculum_id': curriculum.curriculum_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"커리큘럼 저장 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/create_mentorship", response_model=Dict[str, Any])
async def create_mentorship(
    mentorship_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """멘토쉽 생성 API"""
    try:
        mentee_id = mentorship_data.get('mentee_id')
        curriculum_id = mentorship_data.get('curriculum_id')
        
        if not mentee_id or not curriculum_id:
            raise HTTPException(
                status_code=400,
                detail="멘티와 커리큘럼을 선택해주세요."
            )
        
        # 멘티 확인
        mentee = db.query(User).filter(
            User.user_id == mentee_id,
            User.role == 'mentee',
            User.is_active == True
        ).first()
        
        if not mentee:
            raise HTTPException(
                status_code=404,
                detail="멘티를 찾을 수 없습니다."
            )
        
        # 이미 활성 멘토쉽이 있는지 확인
        existing_mentorship = db.query(Mentorship).filter(
            Mentorship.mentee_id == mentee_id,
            Mentorship.is_active == True
        ).first()
        
        if existing_mentorship:
            raise HTTPException(
                status_code=400,
                detail="이미 활성 멘토쉽이 있는 멘티입니다."
            )
        
        # 커리큘럼 확인
        curriculum = db.query(Curriculum).filter(
            Curriculum.curriculum_id == curriculum_id
        ).first()
        
        if not curriculum:
            raise HTTPException(
                status_code=404,
                detail="커리큘럼을 찾을 수 없습니다."
            )
        
        # 멘토쉽 생성
        mentorship = Mentorship(
            mentor_id=current_user.user_id,
            mentee_id=mentee_id,
            curriculum_title=curriculum.curriculum_title,
            total_weeks=curriculum.total_weeks,
            start_date=date.today(),
            is_active=True
        )
        db.add(mentorship)
        db.commit()
        db.refresh(mentorship)
        
        # 커리큘럼의 작업들을 TaskAssign으로 복사
        tasks = db.query(TaskManage).filter(
            TaskManage.curriculum_id == curriculum_id
        ).order_by(TaskManage.week, TaskManage.order).all()
        
        for task in tasks:
            task_assign = TaskAssign(
                mentorship_id=mentorship.mentorship_id,
                title=task.title,
                description=task.description,
                status='진행 전',
                priority=task.priority,
                week=task.week,
                order=task.order,
                exp=task.exp,
                estimated_hours=task.estimated_hours
            )
            db.add(task_assign)
        
        db.commit()
        
        return {
            'success': True,
            'message': '멘토쉽이 성공적으로 생성되었습니다.',
            'mentorship_id': mentorship.mentorship_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"멘토쉽 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/curriculums", response_model=List[CurriculumResponse])
async def get_curriculums(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """커리큘럼 목록 조회"""
    try:
        # 사용자 부서의 커리큘럼 + 공통 커리큘럼
        query = db.query(Curriculum)
        
        if current_user.department_id:
            query = query.filter(
                or_(
                    Curriculum.department_id == current_user.department_id,
                    Curriculum.common == True
                )
            )
        else:
            query = query.filter(Curriculum.common == True)
        
        curriculums = query.order_by(Curriculum.curriculum_id.desc()).all()
        
        return [CurriculumResponse(
            curriculum_id=curr.curriculum_id,
            curriculum_title=curr.curriculum_title,
            curriculum_description=curr.curriculum_description,
            department_id=curr.department_id,
            common=curr.common,
            total_weeks=curr.total_weeks,
            week_schedule=curr.week_schedule
        ) for curr in curriculums]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"커리큘럼 목록 조회 중 오류가 발생했습니다: {str(e)}"
        ) 