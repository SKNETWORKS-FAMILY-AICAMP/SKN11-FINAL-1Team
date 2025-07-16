from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import date
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "진행 전"
    IN_PROGRESS = "진행 중"
    REVIEW_REQUESTED = "검토 요청"
    COMPLETED = "완료"

class TaskPriority(str, Enum):
    HIGH = "상"
    MEDIUM = "중"
    LOW = "하"

class MentorshipBase(BaseModel):
    mentor_id: int
    mentee_id: int
    curriculum_title: str
    total_weeks: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True

class MentorshipCreate(MentorshipBase):
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('종료일은 시작일보다 늦어야 합니다.')
        return v

class MentorshipUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    total_weeks: Optional[int] = None
    
    class Config:
        from_attributes = True

class MentorshipResponse(MentorshipBase):
    mentorship_id: int
    
    class Config:
        from_attributes = True

class MentorshipWithRelations(MentorshipResponse):
    mentor: Optional['UserResponse'] = None
    mentee: Optional['UserResponse'] = None
    task_assigns: List['TaskAssignResponse'] = []

class MentorshipList(BaseModel):
    mentorships: List[MentorshipResponse]
    total: int
    page: int
    per_page: int

class TaskAssignBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    guideline: Optional[str] = None
    week: int
    order: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[TaskStatus] = TaskStatus.PENDING
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    
    class Config:
        from_attributes = True

class TaskAssignCreate(TaskAssignBase):
    mentorship_id: int
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('종료일은 시작일보다 늦어야 합니다.')
        return v

class TaskAssignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    guideline: Optional[str] = None
    order: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    
    class Config:
        from_attributes = True

class TaskAssignResponse(TaskAssignBase):
    task_assign_id: int
    mentorship_id: int
    
    class Config:
        from_attributes = True

class TaskAssignWithRelations(TaskAssignResponse):
    mentorship: Optional['MentorshipResponse'] = None
    subtasks: List['SubtaskResponse'] = []
    memos: List['MemoResponse'] = []

class TaskAssignList(BaseModel):
    task_assigns: List[TaskAssignResponse]
    total: int
    page: int
    per_page: int

class SubtaskBase(BaseModel):
    class Config:
        from_attributes = True

class SubtaskCreate(SubtaskBase):
    task_assign_id: int

class SubtaskUpdate(SubtaskBase):
    pass

class SubtaskResponse(SubtaskBase):
    subtask_id: int
    task_assign_id: int
    
    class Config:
        from_attributes = True

class SubtaskWithRelations(SubtaskResponse):
    task_assign: Optional['TaskAssignResponse'] = None

class MemoBase(BaseModel):
    comment: Optional[str] = None
    
    class Config:
        from_attributes = True

class MemoCreate(MemoBase):
    task_assign_id: int
    user_id: int

class MemoUpdate(BaseModel):
    comment: Optional[str] = None
    
    class Config:
        from_attributes = True

class MemoResponse(MemoBase):
    memo_id: int
    create_date: Optional[date] = None
    task_assign_id: int
    user_id: int
    
    class Config:
        from_attributes = True

class MemoWithRelations(MemoResponse):
    task_assign: Optional['TaskAssignResponse'] = None
    user: Optional['UserResponse'] = None

class MemoList(BaseModel):
    memos: List[MemoResponse]
    total: int
    page: int
    per_page: int
