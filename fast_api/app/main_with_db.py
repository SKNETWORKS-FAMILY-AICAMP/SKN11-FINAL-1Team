#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import date, datetime
import uvicorn
import os

# 데이터베이스 설정
DATABASE_URL = "sqlite:///../../django_prj/onboarding_quest/db.sqlite3"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Onboarding Quest API",
    version="1.0.0",
    description="Django와 연동된 Onboarding Quest API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SQLAlchemy 모델들 (Django 모델과 호환)
class Company(Base):
    __tablename__ = 'core_company'
    
    company_id = Column(String(12), primary_key=True)
    company_name = Column(String(255))

class Department(Base):
    __tablename__ = 'core_department'
    
    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String(50))
    description = Column(String(255))
    company_id = Column(String(12), ForeignKey('core_company.company_id'))
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = 'core_user'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_number = Column(Integer, unique=True, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    mentorship_id = Column(Integer, nullable=True)
    company_id = Column(String(12), ForeignKey('core_company.company_id'), nullable=True)
    department_id = Column(Integer, ForeignKey('core_department.department_id'), nullable=True)
    tag = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False)
    join_date = Column(Date, nullable=True)
    position = Column(String(50), nullable=False)
    job_part = Column(String(50), nullable=True)
    email = Column(String(254), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    phone = Column(String(15), nullable=True)

class Mentorship(Base):
    __tablename__ = 'core_mentorship'
    
    mentorship_id = Column(Integer, primary_key=True, autoincrement=True)
    mentor_id = Column(Integer)
    mentee_id = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    curriculum_title = Column(String(255))
    total_weeks = Column(Integer, default=0)

class TaskAssign(Base):
    __tablename__ = 'core_taskassign'
    
    task_assign_id = Column(Integer, primary_key=True, autoincrement=True)
    mentorship_id_id = Column(Integer, ForeignKey('core_mentorship.mentorship_id'))
    title = Column(String(255))
    description = Column(String(255))
    guideline = Column(String(255))
    week = Column(Integer)
    order = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(10))
    priority = Column(String(2))

class Curriculum(Base):
    __tablename__ = 'core_curriculum'
    
    curriculum_id = Column(Integer, primary_key=True, autoincrement=True)
    curriculum_description = Column(String(255))
    curriculum_title = Column(String(255))
    department_id = Column(Integer, ForeignKey('core_department.department_id'))
    common = Column(Boolean, default=False)
    total_weeks = Column(Integer, default=0)
    week_schedule = Column(Text)

class TaskManage(Base):
    __tablename__ = 'core_taskmanage'
    
    task_manage_id = Column(Integer, primary_key=True, autoincrement=True)
    curriculum_id_id = Column(Integer, ForeignKey('core_curriculum.curriculum_id'), nullable=False)
    week = Column(Integer, nullable=False)
    order = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    guideline = Column(String(255), nullable=True)
    period = Column(Integer, nullable=True)
    priority = Column(String(2), nullable=True)

# Pydantic 모델들
class UserResponse(BaseModel):
    user_id: int
    employee_number: Optional[int]
    email: str
    first_name: str
    last_name: str
    role: str
    position: str
    job_part: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True

class MentorshipResponse(BaseModel):
    mentorship_id: int
    mentor_id: int
    mentee_id: int
    start_date: Optional[date]
    end_date: Optional[date]
    curriculum_title: str
    total_weeks: int
    is_active: bool

    class Config:
        from_attributes = True

class TaskAssignResponse(BaseModel):
    task_assign_id: int
    mentorship_id_id: int
    title: Optional[str]
    description: Optional[str]
    guideline: Optional[str]
    week: int
    order: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[str]
    priority: Optional[str]

    class Config:
        from_attributes = True

class MentorshipCreate(BaseModel):
    mentor_id: int
    mentee_id: int
    start_date: Optional[str]
    end_date: Optional[str]
    curriculum_title: str
    total_weeks: int = 0

class MentorshipCreateDjangoCompat(BaseModel):
    mentee_id: int
    start_date: Optional[str]
    end_date: Optional[str]
    curriculum_id: Optional[int] = None

class TaskAssignCreate(BaseModel):
    mentorship_id_id: int
    title: str
    description: Optional[str]
    guideline: Optional[str]
    week: int
    order: Optional[int]
    start_date: Optional[str]
    end_date: Optional[str]
    status: Optional[str] = "진행 전"
    priority: Optional[str] = "중"

class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    employee_number: int
    role: str = "mentee"
    position: str = "신입사원"
    job_part: str = "일반"
    password: str = "123"
    department_id: Optional[int] = None
    company_id: Optional[str] = None

class DepartmentCreate(BaseModel):
    department_name: str
    description: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    job_part: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None

class CurriculumCreate(BaseModel):
    curriculum_title: str
    curriculum_description: Optional[str] = None
    week_schedule: Optional[str] = None
    total_weeks: int = 0
    is_common: bool = False
    department_id: Optional[int] = None
    tasks: List[dict] = []

class TaskManageCreate(BaseModel):
    week: int
    order: int
    title: str
    description: Optional[str] = None
    guideline: Optional[str] = None
    period: Optional[str] = None
    priority: Optional[str] = "중"

class MentorshipUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    curriculum_title: Optional[str] = None
    total_weeks: Optional[int] = None
    is_active: Optional[bool] = None

# 기본 엔드포인트
@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 실제 데이터베이스와 연결되어 실행 중입니다!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "서버가 정상적으로 실행 중입니다.", "database": "SQLite connected"}

# 사용자 API
@app.get("/api/v1/users/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """사용자 목록 조회"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 상세 조회"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

@app.post("/api/v1/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """사용자 생성"""
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    # 사번 중복 확인
    existing_employee = db.query(User).filter(User.employee_number == user.employee_number).first()
    if existing_employee:
        raise HTTPException(status_code=400, detail="이미 존재하는 사번입니다.")
    
    # 비밀번호 해싱
    # Django 설정 없이 간단히 텍스트로 저장 (개발용)
    hashed_password = user.password
    
    # 새 사용자 생성
    db_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        employee_number=user.employee_number,
        role=user.role,
        position=user.position,
        job_part=user.job_part,
        password=hashed_password,
        department_id=user.department_id,
        company_id=user.company_id,
        is_active=True,
        is_admin=False,
        is_superuser=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/v1/account/user/create")
def create_user_django_compat(user: UserCreate, db: Session = Depends(get_db)):
    """Django 호환을 위한 사용자 생성 엔드포인트"""
    try:
        # 기존 create_user 함수 호출
        new_user = create_user(user, db)
        return {
            "success": True,
            "message": "사용자가 성공적으로 생성되었습니다.",
            "user_id": new_user.user_id,
            "email": new_user.email
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/account/department/create")
def create_department_django_compat(department: DepartmentCreate, db: Session = Depends(get_db)):
    """Django 호환을 위한 부서 생성 엔드포인트"""
    try:
        # 부서명 중복 확인
        existing_dept = db.query(Department).filter(Department.department_name == department.department_name).first()
        if existing_dept:
            raise HTTPException(status_code=400, detail="이미 존재하는 부서명입니다.")
        
        # 새 부서 생성
        db_department = Department(
            department_name=department.department_name,
            description=department.description,
            company_id="123-45-67890",  # 기본 회사 ID
            is_active=True
        )
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        
        return {
            "success": True,
            "message": "부서가 성공적으로 생성되었습니다.",
            "department_id": db_department.department_id,
            "department_name": db_department.department_name
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/account/user/{user_id}/update")
def update_user_django_compat(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Django 호환을 위한 사용자 수정 엔드포인트"""
    try:
        # 사용자 조회
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 수정할 필드들 업데이트
        if user_update.first_name is not None:
            user.first_name = user_update.first_name
        if user_update.last_name is not None:
            user.last_name = user_update.last_name
        if user_update.position is not None:
            user.position = user_update.position
        if user_update.job_part is not None:
            user.job_part = user_update.job_part
        if user_update.department_id is not None:
            user.department_id = user_update.department_id
        if user_update.role is not None:
            user.role = user_update.role
        
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": "사용자가 성공적으로 수정되었습니다.",
            "user_id": user.user_id,
            "email": user.email
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/departments/")
def get_departments(db: Session = Depends(get_db)):
    """부서 목록 조회"""
    departments = db.query(Department).filter(Department.is_active == True).all()
    return [
        {
            "department_id": dept.department_id,
            "department_name": dept.department_name,
            "description": dept.description,
            "is_active": dept.is_active
        }
        for dept in departments
    ]

@app.post("/api/v1/mentor/save_curriculum")
def save_curriculum_django_compat(curriculum: CurriculumCreate, db: Session = Depends(get_db)):
    """Django 호환을 위한 커리큘럼 저장 엔드포인트"""
    try:
        # 커리큘럼 생성
        db_curriculum = Curriculum(
            curriculum_title=curriculum.curriculum_title,
            curriculum_description=curriculum.curriculum_description,
            week_schedule=curriculum.week_schedule,
            total_weeks=curriculum.total_weeks,
            common=curriculum.is_common,
            department_id=curriculum.department_id
        )
        db.add(db_curriculum)
        db.commit()
        db.refresh(db_curriculum)
        
        # 과제들 저장
        for task_data in curriculum.tasks:
            # period 값을 정수로 변환 (일 단위 숫자만 추출)
            period_str = task_data.get('period', '0')
            period_int = int(''.join(filter(str.isdigit, period_str))) if period_str else 0
            
            db_task = TaskManage(
                curriculum_id_id=db_curriculum.curriculum_id,
                week=task_data.get('week', 1),
                order=task_data.get('order', 1),
                title=task_data.get('title', ''),
                description=task_data.get('description', ''),
                guideline=task_data.get('guideline', ''),
                period=period_int,
                priority=task_data.get('priority', '중')[:2]  # 최대 2자리
            )
            db.add(db_task)
        
        db.commit()
        
        return {
            "success": True,
            "message": "커리큘럼이 성공적으로 저장되었습니다.",
            "curriculum_id": db_curriculum.curriculum_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/mentorships/{mentorship_id}")
def update_mentorship(mentorship_id: int, mentorship_update: MentorshipUpdate, db: Session = Depends(get_db)):
    """멘토쉽 수정"""
    try:
        # 멘토쉽 조회
        mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
        if not mentorship:
            raise HTTPException(status_code=404, detail="멘토쉽을 찾을 수 없습니다.")
        
        # 수정할 필드들 업데이트
        if mentorship_update.start_date is not None:
            mentorship.start_date = datetime.strptime(mentorship_update.start_date, "%Y-%m-%d").date()
        if mentorship_update.end_date is not None:
            mentorship.end_date = datetime.strptime(mentorship_update.end_date, "%Y-%m-%d").date()
        if mentorship_update.curriculum_title is not None:
            mentorship.curriculum_title = mentorship_update.curriculum_title
        if mentorship_update.total_weeks is not None:
            mentorship.total_weeks = mentorship_update.total_weeks
        if mentorship_update.is_active is not None:
            mentorship.is_active = mentorship_update.is_active
        
        db.commit()
        db.refresh(mentorship)
        
        return {
            "success": True,
            "message": "멘토쉽이 성공적으로 수정되었습니다.",
            "mentorship_id": mentorship.mentorship_id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/curriculums/")
def get_curriculums(db: Session = Depends(get_db)):
    """커리큘럼 목록 조회"""
    curriculums = db.query(Curriculum).all()
    return [
        {
            "curriculum_id": curr.curriculum_id,
            "curriculum_title": curr.curriculum_title,
            "curriculum_description": curr.curriculum_description,
            "total_weeks": curr.total_weeks,
            "common": curr.common,
            "department_id": curr.department_id
        }
        for curr in curriculums
    ]

# 멘토십 API
@app.get("/api/v1/mentorships/", response_model=List[MentorshipResponse])
def get_mentorships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """멘토십 목록 조회"""
    mentorships = db.query(Mentorship).offset(skip).limit(limit).all()
    return mentorships

@app.post("/api/v1/mentorships/", response_model=MentorshipResponse)
def create_mentorship(mentorship: MentorshipCreate, db: Session = Depends(get_db)):
    """멘토십 생성"""
    # 날짜 문자열을 date 객체로 변환
    start_date = datetime.strptime(mentorship.start_date, "%Y-%m-%d").date() if mentorship.start_date else None
    end_date = datetime.strptime(mentorship.end_date, "%Y-%m-%d").date() if mentorship.end_date else None
    
    db_mentorship = Mentorship(
        mentor_id=mentorship.mentor_id,
        mentee_id=mentorship.mentee_id,
        start_date=start_date,
        end_date=end_date,
        curriculum_title=mentorship.curriculum_title,
        total_weeks=mentorship.total_weeks,
        is_active=True
    )
    db.add(db_mentorship)
    db.commit()
    db.refresh(db_mentorship)
    return db_mentorship

@app.post("/api/v1/mentor/create_mentorship")
def create_mentorship_django_compat(mentorship: MentorshipCreateDjangoCompat, db: Session = Depends(get_db)):
    """Django 호환을 위한 멘토십 생성 엔드포인트"""
    try:
        # curriculum_id로 curriculum 정보 조회
        curriculum_title = "기본 커리큘럼"
        total_weeks = 12
        
        if mentorship.curriculum_id:
            curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == mentorship.curriculum_id).first()
            if curriculum:
                curriculum_title = curriculum.curriculum_title
                total_weeks = curriculum.total_weeks
        
        # 기본 mentor_id 설정 (실제로는 JWT 토큰이나 세션에서 추출해야 함)
        mentor_id = 1
        
        # MentorshipCreate 모델로 변환
        mentorship_create = MentorshipCreate(
            mentor_id=mentor_id,
            mentee_id=mentorship.mentee_id,
            start_date=mentorship.start_date,
            end_date=mentorship.end_date,
            curriculum_title=curriculum_title,
            total_weeks=total_weeks
        )
        
        # 기존 create_mentorship 함수 호출
        new_mentorship = create_mentorship(mentorship_create, db)
        return {
            "success": True,
            "message": "멘토십이 성공적으로 생성되었습니다.",
            "mentorship_id": new_mentorship.mentorship_id,
            "mentor_id": new_mentorship.mentor_id,
            "mentee_id": new_mentorship.mentee_id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mentorships/{mentorship_id}", response_model=MentorshipResponse)
def get_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십 상세 조회"""
    mentorship = db.query(Mentorship).filter(Mentorship.mentorship_id == mentorship_id).first()
    if not mentorship:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다.")
    return mentorship

# 과제 할당 API
@app.get("/api/v1/task-assigns/", response_model=List[TaskAssignResponse])
def get_task_assigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """과제 할당 목록 조회"""
    task_assigns = db.query(TaskAssign).offset(skip).limit(limit).all()
    return task_assigns

@app.post("/api/v1/task-assigns/", response_model=TaskAssignResponse)
def create_task_assign(task: TaskAssignCreate, db: Session = Depends(get_db)):
    """과제 할당 생성"""
    # 날짜 문자열을 date 객체로 변환
    start_date = datetime.strptime(task.start_date, "%Y-%m-%d").date() if task.start_date else None
    end_date = datetime.strptime(task.end_date, "%Y-%m-%d").date() if task.end_date else None
    
    db_task = TaskAssign(
        mentorship_id_id=task.mentorship_id_id,
        title=task.title,
        description=task.description,
        guideline=task.guideline,
        week=task.week,
        order=task.order,
        start_date=start_date,
        end_date=end_date,
        status=task.status,
        priority=task.priority
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/api/v1/task-assigns/{task_id}", response_model=TaskAssignResponse)
def get_task_assign(task_id: int, db: Session = Depends(get_db)):
    """과제 할당 상세 조회"""
    task = db.query(TaskAssign).filter(TaskAssign.task_assign_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    return task

@app.put("/api/v1/task-assigns/{task_id}", response_model=TaskAssignResponse)
def update_task_assign(task_id: int, task: TaskAssignCreate, db: Session = Depends(get_db)):
    """과제 할당 수정"""
    db_task = db.query(TaskAssign).filter(TaskAssign.task_assign_id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    # 날짜 문자열을 date 객체로 변환
    start_date = datetime.strptime(task.start_date, "%Y-%m-%d").date() if task.start_date else None
    end_date = datetime.strptime(task.end_date, "%Y-%m-%d").date() if task.end_date else None
    
    db_task.title = task.title
    db_task.description = task.description
    db_task.guideline = task.guideline
    db_task.week = task.week
    db_task.order = task.order
    db_task.start_date = start_date
    db_task.end_date = end_date
    db_task.status = task.status
    db_task.priority = task.priority
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/api/v1/task-assigns/{task_id}")
def delete_task_assign(task_id: int, db: Session = Depends(get_db)):
    """과제 할당 삭제"""
    db_task = db.query(TaskAssign).filter(TaskAssign.task_assign_id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")
    
    db.delete(db_task)
    db.commit()
    return {"message": "과제가 삭제되었습니다."}

# 데이터베이스 연결 테스트
@app.get("/api/v1/test/db")
def test_db_connection(db: Session = Depends(get_db)):
    """데이터베이스 연결 테스트"""
    try:
        # 사용자 수 확인
        user_count = db.query(User).count()
        # 멘토십 수 확인
        mentorship_count = db.query(Mentorship).count()
        # 과제 할당 수 확인
        task_count = db.query(TaskAssign).count()
        
        return {
            "status": "success",
            "message": "데이터베이스 연결 성공",
            "data": {
                "users": user_count,
                "mentorships": mentorship_count,
                "tasks": task_count
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"데이터베이스 연결 실패: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(
        "main_with_db:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    ) 