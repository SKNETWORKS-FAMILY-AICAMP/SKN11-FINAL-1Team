from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import date, datetime
from fastapi import Form, UploadFile, File


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: 'User'

class TokenData(BaseModel):
    email: Optional[str] = None


# Base schemas
class CompanyBase(BaseModel):
    company_name: str
    
    @validator('company_name')
    def company_name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('회사명은 비어있을 수 없습니다')
        return v.strip()

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    company_id: str
    
    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    department_name: str
    description: Optional[str] = None
    
    @validator('department_name')
    def department_name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('부서명은 비어있을 수 없습니다')
        return v.strip()
    
    @validator('description')
    def description_strip_whitespace(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class DepartmentCreate(DepartmentBase):
    company_id: str

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Department(DepartmentBase):
    department_id: int  # Integer로 다시 변경
    company_id: str
    is_active: Optional[bool] = True
    company: Optional[Company] = None
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    job_part: str
    position: str
    join_date: date
    tag: Optional[str] = None
    role: str
    employee_number: Optional[int] = None
    is_admin: Optional[bool] = False
    profile_image: Optional[str] = None
    
    @validator('first_name', 'last_name', 'job_part', 'role', 'position')
    def name_fields_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('필수 텍스트 필드는 비어있을 수 없습니다')
        return v.strip()
    
    @validator('employee_number')
    def employee_number_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('사번은 양수여야 합니다')
        return v
    
    @validator('tag')
    def tag_strip_whitespace(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class UserCreate(UserBase):
    password: str
    department_id: Optional[int] = None  # Integer로 다시 변경
    company_id: Optional[str] = None
    employee_number: Optional[int] = None
    is_admin: Optional[bool] = False
    tag: Optional[str] = None

class User(UserBase):
    user_id: int
    department_id: Optional[int] = None  # Integer로 다시 변경
    company_id: Optional[str] = None
    mentorship_id: Optional[int] = None
    last_login: Optional[datetime] = None
    profile_image: Optional[str] = None
    is_active: Optional[bool] = True
    is_staff: Optional[bool] = False
    department: Optional[Department] = None
    company: Optional[Company] = None
    
    class Config:
        from_attributes = True


class AlarmBase(BaseModel):
    message: str
    is_active: Optional[bool] = True
    
    @validator('message')
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('알림 메시지는 비어있을 수 없습니다')
        return v.strip()

class AlarmCreate(AlarmBase):
    user_id: int

class Alarm(AlarmBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


class CurriculumBase(BaseModel):
    curriculum_title: str
    curriculum_description: Optional[str] = None
    common: Optional[bool] = False
    total_weeks: Optional[int] = 0
    week_schedule: Optional[str] = None

class CurriculumCreate(CurriculumBase):
    department_id: Optional[int] = None  # Integer로 다시 변경

class Curriculum(CurriculumBase):
    curriculum_id: int
    department_id: Optional[int] = None  # Integer로 다시 변경
    department: Optional[Department] = None
    
    class Config:
        from_attributes = True


class TaskManageBase(BaseModel):
    title: str
    description: Optional[str] = None
    guideline: Optional[str] = None
    week: int
    order: Optional[int] = None
    period: Optional[int] = None
    priority: Optional[str] = None

class TaskManageCreate(TaskManageBase):
    curriculum_id: int

class TaskManage(TaskManageBase):
    task_manage_id: int
    curriculum_id: int
    curriculum: Optional[Curriculum] = None
    
    class Config:
        from_attributes = True


class TaskAssignBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    guideline: Optional[str] = None
    week: int
    order: Optional[int] = None
    scheduled_start_date: Optional[date] = None
    scheduled_end_date: Optional[date] = None
    real_start_date: Optional[date] = None
    real_end_date: Optional[date] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class TaskAssignCreate(TaskAssignBase):
    parent_id: Optional[int] = None
    mentorship_id: int

class TaskAssign(TaskAssignBase):
    task_assign_id: int
    parent_id: Optional[int] = None
    mentorship_id: int
    
    class Config:
        from_attributes = True

# 순환 참조를 피하기 위한 응답용 스키마
class TaskAssignResponse(TaskAssignBase):
    task_assign_id: int
    parent_id: Optional[int] = None
    mentorship_id: int
    
    class Config:
        from_attributes = True


class MentorshipBase(BaseModel):
    mentor_id: int
    mentee_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = True
    curriculum_title: Optional[str] = None  # Django 모델에 맞게 curriculum_title 사용
    total_weeks: Optional[int] = 0

class MentorshipCreate(MentorshipBase):
    pass

class Mentorship(MentorshipBase):
    mentorship_id: int  # Django 모델의 기본키
    mentor: Optional[User] = None
    mentee: Optional[User] = None
    
    class Config:
        from_attributes = True

class MentorshipResponse(BaseModel):
    """FastAPI 응답용 풍부한 멘토십 정보"""
    id: int
    mentor_id: int
    mentee_id: int
    curriculum_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 추가 정보
    mentee_name: str
    mentor_name: str
    curriculum_title: str
    total_weeks: int
    total_tasks: int
    completed_tasks: int
    tags: List[str] = []
    
    class Config:
        from_attributes = True


class MemoBase(BaseModel):
    create_date: Optional[datetime] = None
    comment: Optional[str] = None

class MemoCreate(MemoBase):
    task_assign_id: int
    user_id: int

class Memo(MemoBase):
    memo_id: int
    task_assign_id: int
    user_id: int
    user: Optional['User'] = None  # 사용자 정보 포함
    
    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    summary: Optional[str] = None

class ChatSessionCreate(ChatSessionBase):
    user_id: int

class ChatSession(ChatSessionBase):
    session_id: int
    user_id: int
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    message_type: str
    message_text: Optional[str] = None
    create_time: Optional[date] = None

class ChatMessageCreate(ChatMessageBase):
    session_id: int

class ChatMessage(ChatMessageBase):
    message_id: int
    session_id: int
    session: Optional[ChatSession] = None
    
    class Config:
        from_attributes = True


class DocsBase(BaseModel):
    title: str
    description: Optional[str] = None
    file_path: str
    common_doc: Optional[bool] = False

class DocsCreate(DocsBase):
    department_id: int  # Integer로 다시 변경

class Docs(DocsBase):
    docs_id: int
    create_time: datetime
    department_id: int  # Integer로 다시 변경
    department: Optional[Department] = None
    
    class Config:
        from_attributes = True


# Template schemas
class TemplateBase(BaseModel):
    template_title: str
    template_description: Optional[str] = None
    
    @validator('template_title')
    def template_title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('템플릿 제목은 비어있을 수 없습니다')
        return v.strip()
    
    @validator('template_description')
    def description_strip_whitespace(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class TemplateCreate(TemplateBase):
    department_id: int

class Template(TemplateBase):
    template_id: int
    department_id: int
    department: Optional[Department] = None
    
    class Config:
        from_attributes = True


# 폼 데이터 처리용 스키마
class UserFormData(BaseModel):
    """사용자 폼 데이터 스키마"""
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    job_part: str
    position: str
    join_date: date
    tag: Optional[str] = None
    role: str
    employee_number: Optional[int] = None
    is_admin: Optional[bool] = False
    department_id: Optional[int] = None  # Integer로 다시 변경
    company_id: Optional[str] = None


class TaskFormData(BaseModel):
    """태스크 폼 데이터 스키마"""
    title: str
    description: Optional[str] = None
    guideline: Optional[str] = None
    week: int
    order: Optional[int] = None
    period: Optional[int] = None
    priority: Optional[str] = None
    curriculum_id: int


class CompanyFormData(BaseModel):
    """회사 폼 데이터 스키마"""
    company_name: str


class DepartmentFormData(BaseModel):
    """부서 폼 데이터 스키마"""
    department_name: str
    description: Optional[str] = None
    company_id: str


class CurriculumFormData(BaseModel):
    """커리큘럼 폼 데이터 스키마"""
    curriculum_title: str
    curriculum_description: Optional[str] = None
    department_id: Optional[int] = None  # Integer로 다시 변경
    common: Optional[bool] = False
    total_weeks: Optional[int] = 0
    week_schedule: Optional[str] = None


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 스키마"""
    filename: str
    file_path: str
    file_size: int
    content_type: str
    upload_time: datetime