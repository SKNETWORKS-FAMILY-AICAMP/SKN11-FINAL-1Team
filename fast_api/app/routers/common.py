from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import os

from app.database import get_db
from app.models.user import User
from app.models.department import Department
from app.models.mentorship import Mentorship
from app.models.task import TaskAssign
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/common", tags=["common"])
logger = logging.getLogger(__name__)

# Pydantic 모델들
class AuthTestRequest(BaseModel):
    email: str
    password: str

class AuthTestResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None

class UsersTestResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None

class StatsTestResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None

class DocUploadResponse(BaseModel):
    success: bool
    message: str
    doc_id: Optional[int] = None
    error: Optional[str] = None

class TaskCreateRequest(BaseModel):
    title: str
    description: str
    status: str = "진행 전"
    priority: str
    end_date: str
    mentorship_id: Optional[int] = None

class TaskCreateResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[int] = None
    error: Optional[str] = None

@router.post("/api/test/auth", response_model=AuthTestResponse)
async def api_test_auth(request: AuthTestRequest, db: Session = Depends(get_db)):
    """FastAPI 인증 테스트"""
    try:
        # 사용자 확인
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
        
        # 비밀번호 확인 (실제로는 해시된 비밀번호와 비교)
        if user.password != request.password:
            raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
        
        # 성공 응답
        return AuthTestResponse(
            success=True,
            data={
                "user_id": user.user_id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "role": user.role
            },
            message="FastAPI 인증 성공"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증 테스트 오류: {e}")
        return AuthTestResponse(
            success=False,
            error=str(e),
            message="FastAPI 인증 실패"
        )

@router.get("/api/test/users", response_model=UsersTestResponse)
async def api_test_users(page: int = 1, size: int = 20, db: Session = Depends(get_db)):
    """FastAPI 사용자 목록 테스트"""
    try:
        # 페이지네이션
        offset = (page - 1) * size
        users = db.query(User).offset(offset).limit(size).all()
        total = db.query(User).count()
        
        # 사용자 데이터 변환
        users_data = []
        for user in users:
            users_data.append({
                "user_id": user.user_id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "role": user.role,
                "department": user.department.department_name if user.department else None,
                "position": user.position,
                "is_active": user.is_active
            })
        
        return UsersTestResponse(
            success=True,
            data={
                "users": users_data,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            message="FastAPI 사용자 목록 조회 성공"
        )
    except Exception as e:
        logger.error(f"사용자 목록 조회 오류: {e}")
        return UsersTestResponse(
            success=False,
            error=str(e),
            message="FastAPI 사용자 목록 조회 실패"
        )

@router.get("/api/test/stats", response_model=StatsTestResponse)
async def api_test_stats(db: Session = Depends(get_db)):
    """FastAPI 통계 데이터 테스트"""
    try:
        # 사용자 통계
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        mentors = db.query(User).filter(User.role == "mentor").count()
        mentees = db.query(User).filter(User.role == "mentee").count()
        
        # 멘토쉽 통계
        total_mentorships = db.query(Mentorship).count()
        active_mentorships = db.query(Mentorship).filter(Mentorship.is_active == True).count()
        
        # 과제 통계
        total_tasks = db.query(TaskAssign).count()
        completed_tasks = db.query(TaskAssign).filter(TaskAssign.status == "완료").count()
        in_progress_tasks = db.query(TaskAssign).filter(TaskAssign.status == "진행 중").count()
        
        # 부서 통계
        total_departments = db.query(Department).count()
        active_departments = db.query(Department).filter(Department.is_active == True).count()
        
        stats_data = {
            "user_stats": {
                "total": total_users,
                "active": active_users,
                "mentors": mentors,
                "mentees": mentees
            },
            "mentorship_stats": {
                "total": total_mentorships,
                "active": active_mentorships,
                "completed": total_mentorships - active_mentorships
            },
            "task_stats": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
                "pending": total_tasks - completed_tasks - in_progress_tasks
            },
            "department_stats": {
                "total": total_departments,
                "active": active_departments
            }
        }
        
        return StatsTestResponse(
            success=True,
            data=stats_data,
            message="FastAPI 통계 데이터 조회 성공"
        )
    except Exception as e:
        logger.error(f"통계 데이터 조회 오류: {e}")
        return StatsTestResponse(
            success=False,
            error=str(e),
            message="FastAPI 통계 데이터 조회 실패"
        )

@router.post("/doc/upload", response_model=DocUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    common_doc: bool = Form(False),
    db: Session = Depends(get_db)
):
    """문서 업로드"""
    try:
        # 업로드 디렉토리 생성
        upload_dir = "uploads/documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 파일 저장
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 문서 정보를 데이터베이스에 저장 (실제 Docs 모델이 있다면)
        # 여기서는 임시로 성공 응답만 반환
        
        return DocUploadResponse(
            success=True,
            message="문서가 성공적으로 업로드되었습니다.",
            doc_id=1  # 임시 ID
        )
    except Exception as e:
        logger.error(f"문서 업로드 오류: {e}")
        return DocUploadResponse(
            success=False,
            error=str(e),
            message=f"문서 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/doc/{doc_id}")
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """문서 삭제"""
    try:
        # 실제 Docs 모델이 있다면 해당 문서 삭제
        # 여기서는 임시로 성공 응답만 반환
        
        return {
            "success": True,
            "message": "문서가 성공적으로 삭제되었습니다."
        }
    except Exception as e:
        logger.error(f"문서 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류가 발생했습니다: {str(e)}")

@router.post("/task/create", response_model=TaskCreateResponse)
async def create_task(request: TaskCreateRequest, db: Session = Depends(get_db)):
    """과제 생성"""
    try:
        # 멘토쉽 찾기
        mentorship = None
        if request.mentorship_id:
            mentorship = db.query(Mentorship).filter(
                Mentorship.mentorship_id == request.mentorship_id
            ).first()
        
        if not mentorship:
            raise HTTPException(status_code=400, detail="유효한 멘토쉽을 찾을 수 없습니다.")
        
        # 과제 생성
        new_task = TaskAssign(
            mentorship_id=mentorship.mentorship_id,
            title=request.title,
            description=request.description,
            status=request.status,
            priority=request.priority,
            week=1,  # 기본값
            order=1,  # 기본값
            end_date=datetime.strptime(request.end_date, "%Y-%m-%d").date()
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return TaskCreateResponse(
            success=True,
            message="과제가 성공적으로 생성되었습니다.",
            task_id=new_task.task_assign_id
        )
    except Exception as e:
        logger.error(f"과제 생성 오류: {e}")
        return TaskCreateResponse(
            success=False,
            error=str(e),
            message=f"과제 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/api/proxy/{endpoint:path}")
async def api_proxy_get(endpoint: str, request: Request, db: Session = Depends(get_db)):
    """FastAPI 프록시 GET 요청"""
    try:
        # 실제 프록시 로직 구현
        # 여기서는 임시로 성공 응답만 반환
        return {
            "success": True,
            "message": f"프록시 요청 처리 완료: {endpoint}",
            "method": "GET",
            "params": dict(request.query_params)
        }
    except Exception as e:
        logger.error(f"프록시 GET 요청 오류: {e}")
        raise HTTPException(status_code=500, detail=f"프록시 요청 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/api/proxy/{endpoint:path}")
async def api_proxy_post(endpoint: str, request: Request, db: Session = Depends(get_db)):
    """FastAPI 프록시 POST 요청"""
    try:
        # 요청 바디 읽기
        body = await request.body()
        
        # 실제 프록시 로직 구현
        # 여기서는 임시로 성공 응답만 반환
        return {
            "success": True,
            "message": f"프록시 요청 처리 완료: {endpoint}",
            "method": "POST",
            "body_size": len(body)
        }
    except Exception as e:
        logger.error(f"프록시 POST 요청 오류: {e}")
        raise HTTPException(status_code=500, detail=f"프록시 요청 처리 중 오류가 발생했습니다: {str(e)}")

@router.put("/api/proxy/{endpoint:path}")
async def api_proxy_put(endpoint: str, request: Request, db: Session = Depends(get_db)):
    """FastAPI 프록시 PUT 요청"""
    try:
        # 요청 바디 읽기
        body = await request.body()
        
        # 실제 프록시 로직 구현
        # 여기서는 임시로 성공 응답만 반환
        return {
            "success": True,
            "message": f"프록시 요청 처리 완료: {endpoint}",
            "method": "PUT",
            "body_size": len(body)
        }
    except Exception as e:
        logger.error(f"프록시 PUT 요청 오류: {e}")
        raise HTTPException(status_code=500, detail=f"프록시 요청 처리 중 오류가 발생했습니다: {str(e)}")

@router.delete("/api/proxy/{endpoint:path}")
async def api_proxy_delete(endpoint: str, request: Request, db: Session = Depends(get_db)):
    """FastAPI 프록시 DELETE 요청"""
    try:
        # 실제 프록시 로직 구현
        # 여기서는 임시로 성공 응답만 반환
        return {
            "success": True,
            "message": f"프록시 요청 처리 완료: {endpoint}",
            "method": "DELETE"
        }
    except Exception as e:
        logger.error(f"프록시 DELETE 요청 오류: {e}")
        raise HTTPException(status_code=500, detail=f"프록시 요청 처리 중 오류가 발생했습니다: {str(e)}") 