from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, List, Union
import re

# Base 스키마
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

# Company 스키마
class CompanyBase(BaseModel):
    company_id: str = Field(..., description="사업자번호 (000-00-00000 형식)")
    company_name: str = Field(..., description="회사명")
    
    @validator('company_id')
    def validate_company_id(cls, v):
        if not re.match(r'^\d{3}-\d{2}-\d{5}$', v):
            raise ValueError('사업자번호는 000-00-00000 형식이어야 합니다.')
        return v

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    company_id: Optional[str] = None
    company_name: Optional[str] = None

class Company(CompanyBase):
    class Config:
        from_attributes = True

# Department 스키마
class DepartmentBase(BaseModel):
    department_name: str = Field(..., description="부서명")
    description: Optional[str] = Field(None, description="부서 설명")
    is_active: bool = Field(True, description="활성화 여부")
    company_id: str = Field(..., description="소속 회사 ID")

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    company_id: Optional[str] = None

class Department(DepartmentBase):
    department_id: int = Field(..., description="부서 ID")
    
    class Config:
        from_attributes = True

# User 스키마
class UserBase(BaseModel):
    employee_number: Optional[int] = Field(None, description="사번")
    is_admin: bool = Field(False, description="관리자 여부")
    mentorship_id: Optional[int] = Field(None, description="멘토십 ID")
    tag: Optional[str] = Field(None, description="사용자 태그")
    exp: int = Field(0, description="경험치")
    role: str = Field(..., description="역할 (mentee/mentor)")
    join_date: Optional[date] = Field(None, description="입사일")
    position: str = Field(..., description="직위")
    job_part: str = Field(..., description="직무")
    email: str = Field(..., description="이메일")
    last_name: str = Field(..., description="성")
    first_name: str = Field(..., description="이름")
    last_login: Optional[datetime] = Field(None, description="마지막 로그인")
    is_active: bool = Field(True, description="활성화 여부")
    is_staff: bool = Field(False, description="스태프 여부")
    is_superuser: bool = Field(False, description="슈퍼유저 여부")
    company_id: str = Field(..., description="소속 회사 ID")
    department_id: int = Field(..., description="소속 부서 ID")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['mentee', 'mentor']:
            raise ValueError('role은 mentee 또는 mentor여야 합니다.')
        return v

class UserCreate(UserBase):
    password: str = Field(..., description="비밀번호")

class UserUpdate(BaseModel):
    employee_number: Optional[int] = None
    is_admin: Optional[bool] = None
    mentorship_id: Optional[int] = None
    tag: Optional[str] = None
    exp: Optional[int] = None
    role: Optional[str] = None
    position: Optional[str] = None
    job_part: Optional[str] = None
    email: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    is_superuser: Optional[bool] = None
    company_id: Optional[str] = None
    department_id: Optional[int] = None

class User(UserBase):
    user_id: int = Field(..., description="사용자 ID")
    
    class Config:
        from_attributes = True

# Curriculum 스키마
class CurriculumBase(BaseModel):
    curriculum_description: Optional[str] = Field(None, description="커리큘럼 설명")
    curriculum_title: str = Field(..., description="커리큘럼 제목")
    common: bool = Field(False, description="공용 커리큘럼 여부")
    total_weeks: int = Field(0, description="총 주차 수")
    week_schedule: Optional[str] = Field(None, description="주차별 일정")
    department_id: int = Field(..., description="소속 부서 ID")

class CurriculumCreate(CurriculumBase):
    pass

class CurriculumUpdate(BaseModel):
    curriculum_description: Optional[str] = None
    curriculum_title: Optional[str] = None
    common: Optional[bool] = None
    total_weeks: Optional[int] = None
    week_schedule: Optional[str] = None
    department_id: Optional[int] = None

class Curriculum(CurriculumBase):
    curriculum_id_id: int = Field(..., description="커리큘럼 ID")
    
    class Config:
        from_attributes = True

# TaskManage 스키마
class TaskManageBase(BaseModel):
    title: str = Field(..., description="과제 제목")
    description: Optional[str] = Field(None, description="과제 설명")
    guideline: Optional[str] = Field(None, description="가이드라인")
    week: int = Field(..., description="주차")
    order: Optional[int] = Field(None, description="순서")
    period: Optional[int] = Field(None, description="기간")
    priority: Optional[str] = Field(None, description="우선순위 (상/중/하)")
    curriculum_id_id: int = Field(..., description="커리큘럼 ID")
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None and v not in ['상', '중', '하']:
            raise ValueError('priority는 상, 중, 하 중 하나여야 합니다.')
        return v

class TaskManageCreate(TaskManageBase):
    pass

class TaskManageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    guideline: Optional[str] = None
    week: Optional[int] = None
    order: Optional[int] = None
    period: Optional[int] = None
    priority: Optional[str] = None
    curriculum_id_id: Optional[int] = None

class TaskManage(TaskManageBase):
    task_manage_id: int = Field(..., description="과제 관리 ID")
    
    class Config:
        from_attributes = True

# TaskAssign 스키마
class TaskAssignBase(BaseModel):
    title: Optional[str] = Field(None, description="과제 제목")
    start_date: Optional[date] = Field(None, description="시작일")
    end_date: Optional[date] = Field(None, description="종료일")
    status: int = Field(..., description="상태")
    difficulty: Optional[str] = Field(None, description="난이도")
    description: Optional[str] = Field(None, description="설명")
    exp: Optional[int] = Field(None, description="경험치")
    order: Optional[int] = Field(None, description="순서")
    user_id: int = Field(..., description="사용자 ID")
    mentorship_id: int = Field(..., description="멘토십 ID")

class TaskAssignCreate(TaskAssignBase):
    pass

class TaskAssignUpdate(BaseModel):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[int] = None
    difficulty: Optional[str] = None
    description: Optional[str] = None
    exp: Optional[int] = None
    order: Optional[int] = None
    user_id: Optional[int] = None
    mentorship_id: Optional[int] = None

class TaskAssign(TaskAssignBase):
    task_assign_id: int = Field(..., description="과제 할당 ID")
    
    class Config:
        from_attributes = True

# Mentorship 스키마
class MentorshipBase(BaseModel):
    mentor_id: int = Field(..., description="멘토 ID")
    mentee_id: int = Field(..., description="멘티 ID")

class MentorshipCreate(MentorshipBase):
    pass

class MentorshipUpdate(BaseModel):
    mentor_id: Optional[int] = None
    mentee_id: Optional[int] = None

class Mentorship(MentorshipBase):
    mentorship_id: int = Field(..., description="멘토십 ID")
    
    class Config:
        from_attributes = True

# ChatSession 스키마
class ChatSessionBase(BaseModel):
    summary: Optional[str] = Field(None, description="세션 요약")
    user_id: int = Field(..., description="사용자 ID")

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionUpdate(BaseModel):
    summary: Optional[str] = None
    user_id: Optional[int] = None

class ChatSession(ChatSessionBase):
    session_id: int = Field(..., description="세션 ID")
    
    class Config:
        from_attributes = True

# ChatMessage 스키마
class ChatMessageBase(BaseModel):
    message_type: str = Field(..., description="메시지 타입 (user/chatbot)")
    message_text: Optional[str] = Field(None, description="메시지 내용")
    create_time: Optional[date] = Field(None, description="생성일")
    session_id: int = Field(..., description="세션 ID")
    
    @validator('message_type')
    def validate_message_type(cls, v):
        if v not in ['user', 'chatbot']:
            raise ValueError('message_type은 user 또는 chatbot이어야 합니다.')
        return v

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageUpdate(BaseModel):
    message_type: Optional[str] = None
    message_text: Optional[str] = None
    create_time: Optional[date] = None
    session_id: Optional[int] = None

class ChatMessage(ChatMessageBase):
    message_id: int = Field(..., description="메시지 ID")
    
    class Config:
        from_attributes = True

# Docs 스키마
class DocsBase(BaseModel):
    title: str = Field(..., description="문서 제목")
    description: Optional[str] = Field(None, description="문서 설명")
    file_path: str = Field(..., description="파일 경로")
    create_time: Optional[datetime] = Field(None, description="생성일")
    common_doc: bool = Field(False, description="공용 문서 여부")
    department_id: int = Field(..., description="소속 부서 ID")

class DocsCreate(DocsBase):
    pass

class DocsUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    create_time: Optional[datetime] = None
    common_doc: Optional[bool] = None
    department_id: Optional[int] = None

class Docs(DocsBase):
    docs_id: int = Field(..., description="문서 ID")
    
    class Config:
        from_attributes = True

# 응답 스키마
class ApiResponse(BaseModel):
    message: str
    data: Optional[Union[dict, list]] = None
    error: Optional[str] = None 