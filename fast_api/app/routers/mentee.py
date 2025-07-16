from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import TaskAssign, Mentorship, User, Memo
from app.schemas.mentorship import (
    TaskAssignResponse, TaskAssignUpdate, TaskStatus
)
from app.dependencies import get_current_user
from sqlalchemy import func
import json

router = APIRouter(prefix="/mentee", tags=["mentee"])

@router.get("/task/{task_assign_id}", response_model=Dict[str, Any])
async def get_task_detail(
    task_assign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """과제 상세 정보 조회"""
    try:
        # 과제 조회
        task = db.query(TaskAssign).filter(
            TaskAssign.task_assign_id == task_assign_id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail="과제를 찾을 수 없습니다."
            )
        
        # 권한 확인 - 해당 멘토쉽의 멘티인지 확인
        mentorship = db.query(Mentorship).filter(
            Mentorship.mentorship_id == task.mentorship_id
        ).first()
        
        if not mentorship or mentorship.mentee_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="권한이 없습니다."
            )
        
        # 과제 데이터 구성
        task_data = {
            'task_assign_id': task.task_assign_id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'week': task.week,
            'order': task.order,
            'exp': task.exp,
            'estimated_hours': task.estimated_hours,
            'start_date': task.start_date,
            'end_date': task.end_date,
            'actual_hours': task.actual_hours,
            'progress': task.progress,
            'review_feedback': task.review_feedback,
            'mentorship_id': task.mentorship_id
        }
        
        return {
            'success': True,
            'task': task_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )

@router.put("/task/{task_assign_id}", response_model=Dict[str, Any])
async def update_task(
    task_assign_id: int,
    task_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """과제 업데이트"""
    try:
        # 과제 조회
        task = db.query(TaskAssign).filter(
            TaskAssign.task_assign_id == task_assign_id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail="과제를 찾을 수 없습니다."
            )
        
        # 권한 확인 - 해당 멘토쉽의 멘티인지 확인
        mentorship = db.query(Mentorship).filter(
            Mentorship.mentorship_id == task.mentorship_id
        ).first()
        
        if not mentorship or mentorship.mentee_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="권한이 없습니다."
            )
        
        # 허용된 필드만 업데이트
        allowed_fields = ['status', 'progress', 'actual_hours', 'review_feedback']
        updated_fields = []
        
        for field in allowed_fields:
            if field in task_data:
                new_value = task_data[field]
                if hasattr(task, field):
                    setattr(task, field, new_value)
                    updated_fields.append(field)
        
        # 상태 변경 시 메모 생성
        if 'status' in task_data:
            memo_comment = f"과제 상태가 '{task_data['status']}'로 변경되었습니다."
            if task_data['status'] == '완료':
                memo_comment += f" (진행 시간: {task_data.get('actual_hours', 0)}시간)"
            
            memo = Memo(
                task_assign_id=task.task_assign_id,
                comment=memo_comment,
                author_id=current_user.user_id
            )
            db.add(memo)
        
        db.commit()
        
        return {
            'success': True,
            'message': '과제가 성공적으로 업데이트되었습니다.',
            'updated_fields': updated_fields,
            'task': {
                'task_assign_id': task.task_assign_id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'week': task.week,
                'order': task.order,
                'exp': task.exp,
                'estimated_hours': task.estimated_hours,
                'start_date': task.start_date,
                'end_date': task.end_date,
                'actual_hours': task.actual_hours,
                'progress': task.progress,
                'review_feedback': task.review_feedback,
                'mentorship_id': task.mentorship_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"과제 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_tasks(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """멘티의 과제 목록 조회"""
    try:
        # 사용자의 활성 멘토쉽 조회
        mentorship = db.query(Mentorship).filter(
            Mentorship.mentee_id == current_user.user_id,
            Mentorship.is_active == True
        ).first()
        
        if not mentorship:
            return []
        
        # 과제 목록 조회
        query = db.query(TaskAssign).filter(
            TaskAssign.mentorship_id == mentorship.mentorship_id
        )
        
        if status:
            query = query.filter(TaskAssign.status == status)
        
        tasks = query.order_by(TaskAssign.week, TaskAssign.order).all()
        
        return [{
            'task_assign_id': task.task_assign_id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'week': task.week,
            'order': task.order,
            'exp': task.exp,
            'estimated_hours': task.estimated_hours,
            'start_date': task.start_date,
            'end_date': task.end_date,
            'actual_hours': task.actual_hours,
            'progress': task.progress,
            'review_feedback': task.review_feedback,
            'mentorship_id': task.mentorship_id
        } for task in tasks]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"과제 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/mentorship", response_model=Dict[str, Any])
async def get_mentorship_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """멘티의 멘토쉽 정보 조회"""
    try:
        # 사용자의 활성 멘토쉽 조회
        mentorship = db.query(Mentorship).filter(
            Mentorship.mentee_id == current_user.user_id,
            Mentorship.is_active == True
        ).first()
        
        if not mentorship:
            return {
                'mentorship': None,
                'mentor': None,
                'stats': None
            }
        
        # 멘토 정보 조회
        mentor = db.query(User).filter(
            User.user_id == mentorship.mentor_id
        ).first()
        
        # 과제 통계 계산
        tasks = db.query(TaskAssign).filter(
            TaskAssign.mentorship_id == mentorship.mentorship_id
        ).all()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == '완료'])
        in_progress_tasks = len([t for t in tasks if t.status == '진행 중'])
        review_tasks = len([t for t in tasks if t.status == '검토 요청'])
        
        # 총 경험치 계산
        total_exp = sum(task.exp for task in tasks if task.status == '완료')
        
        return {
            'mentorship': {
                'mentorship_id': mentorship.mentorship_id,
                'curriculum_title': mentorship.curriculum_title,
                'total_weeks': mentorship.total_weeks,
                'start_date': mentorship.start_date,
                'end_date': mentorship.end_date,
                'is_active': mentorship.is_active
            },
            'mentor': {
                'user_id': mentor.user_id,
                'name': f"{mentor.last_name}{mentor.first_name}",
                'email': mentor.email,
                'position': mentor.position,
                'department': mentor.department.department_name if mentor.department else None
            } if mentor else None,
            'stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'review_tasks': review_tasks,
                'total_exp': total_exp,
                'progress_percentage': int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"멘토쉽 정보 조회 중 오류가 발생했습니다: {str(e)}"
        ) 