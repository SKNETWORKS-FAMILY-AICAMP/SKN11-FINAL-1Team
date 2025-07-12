from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# Base schemas
class CompanyBase(BaseModel):
    company_name: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    company_id: int
    
    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    department_name: str
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    company_id: int

class Department(DepartmentBase):
    department_id: int
    company_id: int
    company: Optional[Company] = None
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    job_part: str
    position: int
    join_date: date
    skill: Optional[str] = None
    role: str
    exp: Optional[int] = 0
    level: Optional[int] = 1
    admin: Optional[bool] = False

class UserCreate(UserBase):
    password: str
    department_id: int
    company_id: int

class User(UserBase):
    user_id: int
    department_id: int
    company_id: int
    department: Optional[Department] = None
    company: Optional[Company] = None
    
    class Config:
        from_attributes = True


class TemplateBase(BaseModel):
    template_title: str
    template_description: Optional[str] = None

class TemplateCreate(TemplateBase):
    department_id: int

class Template(TemplateBase):
    template_id: int
    department_id: int
    department: Optional[Department] = None
    
    class Config:
        from_attributes = True


class TaskManageBase(BaseModel):
    title: str
    start_date: date
    end_date: date
    difficulty: Optional[str] = None
    description: Optional[str] = None
    exp: int
    order: Optional[int] = None

class TaskManageCreate(TaskManageBase):
    template_id: int

class TaskManage(TaskManageBase):
    task_manage_id: int
    template_id: int
    template: Optional[Template] = None
    
    class Config:
        from_attributes = True


class TaskAssignBase(BaseModel):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: int
    difficulty: Optional[str] = None
    description: Optional[str] = None
    exp: Optional[Decimal] = None
    order: Optional[int] = None

class TaskAssignCreate(TaskAssignBase):
    user_id: int
    task_manage_id: int
    mentorship_id: Optional[int] = None

class TaskAssign(TaskAssignBase):
    task_assign_id: int
    user_id: int
    task_manage_id: int
    mentorship_id: Optional[int] = None
    user: Optional[User] = None
    task_manage: Optional[TaskManage] = None
    
    class Config:
        from_attributes = True


class SubtaskBase(BaseModel):
    pass

class SubtaskCreate(SubtaskBase):
    task_assign_id: int

class Subtask(SubtaskBase):
    subtask_id: int
    task_assign_id: int
    task_assign: Optional[TaskAssign] = None
    
    class Config:
        from_attributes = True


class MentorshipBase(BaseModel):
    mentor_id: int
    mentee_id: int

class MentorshipCreate(MentorshipBase):
    pass

class Mentorship(MentorshipBase):
    mentorship_id: int
    mentor: Optional[User] = None
    mentee: Optional[User] = None
    
    class Config:
        from_attributes = True


class MemoBase(BaseModel):
    create_date: Optional[date] = None
    comment: Optional[str] = None

class MemoCreate(MemoBase):
    task_assign_id: int
    user_id: int

class Memo(MemoBase):
    memo_id: int
    task_assign_id: int
    user_id: int
    task_assign: Optional[TaskAssign] = None
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    summary: Optional[str] = None
    started_time: datetime
    ended_time: datetime

class ChatSessionCreate(ChatSessionBase):
    user_id: int

class ChatSession(ChatSessionBase):
    session_id: int
    user_id: int
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    message_type: Optional[str] = None
    message_text: Optional[str] = None

class ChatMessageCreate(ChatMessageBase):
    session_id: int

class ChatMessage(ChatMessageBase):
    message_id: int
    create_time: datetime
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
    department_id: int

class Docs(DocsBase):
    docs_id: int
    create_time: datetime
    department_id: int
    department: Optional[Department] = None
    
    class Config:
        from_attributes = True 