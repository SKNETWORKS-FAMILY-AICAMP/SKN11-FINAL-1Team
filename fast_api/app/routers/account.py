from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
import logging

from app.database import get_db
from app.models.user import User
from app.models.department import Department
from app.models.mentorship import Mentorship
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/account", tags=["account"])
logger = logging.getLogger(__name__)

# Pydantic 모델들
class PasswordResetRequest(BaseModel):
    user_id: int

class PasswordResetResponse(BaseModel):
    success: bool
    message: str

class MentorshipDetailResponse(BaseModel):
    mentorship_id: int
    mentor_id: int
    mentee_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    curriculum_title: Optional[str] = None
    is_active: bool
    total_weeks: Optional[int] = None

class DepartmentCreateRequest(BaseModel):
    department_name: str
    description: Optional[str] = None

class DepartmentUpdateRequest(BaseModel):
    department_name: str
    description: Optional[str] = None

class UserCreateRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    employee_number: str
    department_id: Optional[int] = None
    position: Optional[str] = None
    job_part: Optional[str] = None
    role: str = "mentee"
    password: str = "123"

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    job_part: Optional[str] = None
    department_id: Optional[int] = None

@router.post("/password_reset/{user_id}", response_model=PasswordResetResponse)
async def password_reset(user_id: int, db: Session = Depends(get_db)):
    """비밀번호 재설정"""
    try:
        # 사용자 찾기
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 비밀번호를 기본값으로 재설정
        user.password = "123"  # 실제로는 해시된 비밀번호 사용
        db.commit()
        
        return PasswordResetResponse(
            success=True,
            message=f'사용자 "{user.first_name} {user.last_name}"의 비밀번호가 "123"으로 재설정되었습니다.'
        )
    except Exception as e:
        logger.error(f"비밀번호 재설정 오류: {e}")
        raise HTTPException(status_code=500, detail=f"비밀번호 재설정 중 오류가 발생했습니다: {str(e)}")

@router.get("/mentorship/{mentorship_id}", response_model=MentorshipDetailResponse)
async def get_mentorship_detail(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토쉽 상세 정보"""
    try:
        mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
        if not mentorship:
            raise HTTPException(status_code=404, detail="멘토쉽을 찾을 수 없습니다.")
        
        return MentorshipDetailResponse(
            mentorship_id=mentorship.mentorship_id,
            mentor_id=mentorship.mentor_id,
            mentee_id=mentorship.mentee_id,
            start_date=mentorship.start_date.strftime('%Y-%m-%d') if mentorship.start_date else None,
            end_date=mentorship.end_date.strftime('%Y-%m-%d') if mentorship.end_date else None,
            curriculum_title=mentorship.curriculum_title,
            is_active=mentorship.is_active,
            total_weeks=mentorship.total_weeks
        )
    except Exception as e:
        logger.error(f"멘토쉽 상세 정보 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"멘토쉽 정보 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/department/create")
async def create_department(request: DepartmentCreateRequest, db: Session = Depends(get_db)):
    """부서 생성"""
    try:
        # 부서 중복 확인
        existing_dept = db.query(Department).filter(Department.department_name == request.department_name).first()
        if existing_dept:
            raise HTTPException(status_code=400, detail="이미 존재하는 부서명입니다.")
        
        # 새 부서 생성
        new_department = Department(
            department_name=request.department_name,
            description=request.description,
            is_active=True
        )
        db.add(new_department)
        db.commit()
        db.refresh(new_department)
        
        return {
            "success": True,
            "message": f'부서 "{request.department_name}"이(가) 성공적으로 생성되었습니다.',
            "department_id": new_department.department_id
        }
    except Exception as e:
        logger.error(f"부서 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"부서 생성 중 오류가 발생했습니다: {str(e)}")

@router.put("/department/{department_id}")
async def update_department(department_id: int, request: DepartmentUpdateRequest, db: Session = Depends(get_db)):
    """부서 수정"""
    try:
        department = db.query(Department).filter(Department.department_id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
        
        # 부서 정보 업데이트
        if request.department_name:
            department.department_name = request.department_name
        if request.description is not None:
            department.description = request.description
        
        db.commit()
        
        return {
            "success": True,
            "message": f'부서 "{department.department_name}"이(가) 성공적으로 수정되었습니다.'
        }
    except Exception as e:
        logger.error(f"부서 수정 오류: {e}")
        raise HTTPException(status_code=500, detail=f"부서 수정 중 오류가 발생했습니다: {str(e)}")

@router.delete("/department/{department_id}")
async def delete_department(department_id: int, db: Session = Depends(get_db)):
    """부서 삭제"""
    try:
        department = db.query(Department).filter(Department.department_id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
        
        # 부서에 속한 사용자가 있는지 확인
        user_count = db.query(User).filter(User.department_id == department_id).count()
        if user_count > 0:
            raise HTTPException(status_code=400, detail="해당 부서에 속한 사용자가 있어 삭제할 수 없습니다.")
        
        db.delete(department)
        db.commit()
        
        return {
            "success": True,
            "message": f'부서 "{department.department_name}"이(가) 성공적으로 삭제되었습니다.'
        }
    except Exception as e:
        logger.error(f"부서 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"부서 삭제 중 오류가 발생했습니다: {str(e)}")

@router.post("/user/create")
async def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    """사용자 생성"""
    try:
        # 중복 확인
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
        
        existing_emp = db.query(User).filter(User.employee_number == request.employee_number).first()
        if existing_emp:
            raise HTTPException(status_code=400, detail="이미 존재하는 사번입니다.")
        
        # 부서 확인
        department = None
        if request.department_id:
            department = db.query(Department).filter(Department.department_id == request.department_id).first()
            if not department:
                raise HTTPException(status_code=400, detail="존재하지 않는 부서입니다.")
        
        # 새 사용자 생성
        new_user = User(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            employee_number=request.employee_number,
            department_id=request.department_id,
            position=request.position,
            job_part=request.job_part,
            role=request.role,
            password=request.password,  # 실제로는 해시된 비밀번호 사용
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "message": f'사용자 "{request.first_name} {request.last_name}"이(가) 성공적으로 생성되었습니다.',
            "user_id": new_user.user_id
        }
    except Exception as e:
        logger.error(f"사용자 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 생성 중 오류가 발생했습니다: {str(e)}")

@router.put("/user/{user_id}")
async def update_user(user_id: int, request: UserUpdateRequest, db: Session = Depends(get_db)):
    """사용자 수정"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 사용자 정보 업데이트
        if request.first_name:
            user.first_name = request.first_name
        if request.last_name:
            user.last_name = request.last_name
        if request.position:
            user.position = request.position
        if request.job_part:
            user.job_part = request.job_part
        if request.department_id:
            department = db.query(Department).filter(Department.department_id == request.department_id).first()
            if department:
                user.department_id = request.department_id
        
        db.commit()
        
        return {
            "success": True,
            "message": f'사용자 "{user.first_name} {user.last_name}"이(가) 성공적으로 수정되었습니다.'
        }
    except Exception as e:
        logger.error(f"사용자 수정 오류: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 수정 중 오류가 발생했습니다: {str(e)}")

@router.delete("/user/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 삭제"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 사용자가 참여한 멘토쉽이 있는지 확인
        mentorship_count = db.query(Mentorship).filter(
            (Mentorship.mentor_id == user_id) | (Mentorship.mentee_id == user_id)
        ).count()
        
        if mentorship_count > 0:
            # 완전 삭제 대신 비활성화
            user.is_active = False
            db.commit()
            return {
                "success": True,
                "message": f'사용자 "{user.first_name} {user.last_name}"이(가) 비활성화되었습니다.'
            }
        else:
            # 멘토쉽 기록이 없으면 완전 삭제
            db.delete(user)
            db.commit()
            return {
                "success": True,
                "message": f'사용자 "{user.first_name} {user.last_name}"이(가) 성공적으로 삭제되었습니다.'
            }
    except Exception as e:
        logger.error(f"사용자 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 삭제 중 오류가 발생했습니다: {str(e)}") 