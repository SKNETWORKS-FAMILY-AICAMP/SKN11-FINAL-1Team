# schemas/task.py
from pydantic import BaseModel, validator
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from .mentorship import TaskPriority

if TYPE_CHECKING:
    from .department import DepartmentResponse
    from .user import UserResponse

class CurriculumBase(BaseModel):
    curriculum_title: str
    curriculum_description: Optional[str] = None
    common: bool = False
    total_weeks: int = 0
    week_schedule: Optional[str] = None
    
    class Config:
        from_attributes = True

class CurriculumCreate(CurriculumBase):
    department_id: Optional[int] = None
    
    @validator('total_weeks')
    def validate_total_weeks(cls, v):
        if v < 0:
            raise ValueError('총 주차 수는 0 이상이어야 합니다.')
        return v

class CurriculumUpdate(BaseModel):
    curriculum_title: Optional[str] = None
    curriculum_description: Optional[str] = None
    common: Optional[bool] = None
    total_weeks: Optional[int] = None
    week_schedule: Optional[str] = None
    department_id: Optional[int] = None
    
    @validator('total_weeks')
    def validate_total_weeks(cls, v):
        if v is not None and v < 0:
            raise ValueError('총 주차 수는 0 이상이어야 합니다.')
        return v
    
    class Config:
        from_attributes = True

class CurriculumResponse(CurriculumBase):
    curriculum_id: int
    department_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class CurriculumWithRelations(CurriculumResponse):
    department: Optional['DepartmentResponse'] = None
    tasks: List['TaskManageResponse'] = []

class CurriculumList(BaseModel):
    curriculums: List[CurriculumResponse]
    total: int
    page: int
    per_page: int

class CurriculumStats(BaseModel):
    total_curriculums: int
    common_curriculums: int
    department_curriculums: int
    total_tasks: int
    avg_weeks_per_curriculum: float

class TaskManageBase(BaseModel):
    title: str
    description: Optional[str] = None
    guideline: Optional[str] = None
    week: int
    order: Optional[int] = None
    period: Optional[int] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    
    class Config:
        from_attributes = True

class TaskManageCreate(TaskManageBase):
    curriculum_id: int
    
    @validator('week')
    def validate_week(cls, v):
        if v < 1:
            raise ValueError('주차는 1 이상이어야 합니다.')
        return v
    
    @validator('period')
    def validate_period(cls, v):
        if v is not None and v < 1:
            raise ValueError('기간은 1 이상이어야 합니다.')
        return v

class TaskManageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    guideline: Optional[str] = None
    week: Optional[int] = None
    order: Optional[int] = None
    period: Optional[int] = None
    priority: Optional[TaskPriority] = None
    
    @validator('week')
    def validate_week(cls, v):
        if v is not None and v < 1:
            raise ValueError('주차는 1 이상이어야 합니다.')
        return v
    
    @validator('period')
    def validate_period(cls, v):
        if v is not None and v < 1:
            raise ValueError('기간은 1 이상이어야 합니다.')
        return v
    
    class Config:
        from_attributes = True

class TaskManageResponse(TaskManageBase):
    task_manage_id: int
    curriculum_id: int
    
    class Config:
        from_attributes = True

class TaskManageWithRelations(TaskManageResponse):
    curriculum: Optional['CurriculumResponse'] = None

class TaskManageList(BaseModel):
    tasks: List[TaskManageResponse]
    total: int
    page: int
    per_page: int

class TaskManageStats(BaseModel):
    total_tasks: int
    high_priority_tasks: int
    medium_priority_tasks: int
    low_priority_tasks: int
    avg_period_per_task: float

class DocsBase(BaseModel):
    title: str
    description: Optional[str] = None
    file_path: str
    common_doc: bool = False
    
    class Config:
        from_attributes = True

class DocsCreate(DocsBase):
    department_id: int
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not v.strip():
            raise ValueError('파일 경로는 비어있을 수 없습니다.')
        return v

class DocsUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    common_doc: Optional[bool] = None
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if v is not None and not v.strip():
            raise ValueError('파일 경로는 비어있을 수 없습니다.')
        return v
    
    class Config:
        from_attributes = True

class DocsResponse(DocsBase):
    docs_id: int
    department_id: int
    create_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DocsWithRelations(DocsResponse):
    department: Optional['DepartmentResponse'] = None

class DocsList(BaseModel):
    docs: List[DocsResponse]
    total: int
    page: int
    per_page: int

class DocsStats(BaseModel):
    total_docs: int
    common_docs: int
    department_docs: int
    recent_docs: int  # 최근 7일 내 생성된 문서 수

class ChatSessionBase(BaseModel):
    summary: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatSessionCreate(ChatSessionBase):
    user_id: int
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError('사용자 ID는 양수여야 합니다.')
        return v

class ChatSessionUpdate(BaseModel):
    summary: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatSessionResponse(ChatSessionBase):
    session_id: int
    user_id: int
    
    class Config:
        from_attributes = True

class ChatSessionWithRelations(ChatSessionResponse):
    user: Optional['UserResponse'] = None
    messages: List['ChatMessageResponse'] = []

class ChatSessionList(BaseModel):
    sessions: List[ChatSessionResponse]
    total: int
    page: int
    per_page: int

class ChatSessionStats(BaseModel):
    total_sessions: int
    active_sessions: int
    total_messages: int
    avg_messages_per_session: float

class ChatMessageBase(BaseModel):
    message_type: str  # 'user' or 'chatbot'
    message_text: Optional[str] = None
    
    @validator('message_type')
    def validate_message_type(cls, v):
        if v not in ['user', 'chatbot']:
            raise ValueError('메시지 타입은 user 또는 chatbot이어야 합니다.')
        return v
    
    class Config:
        from_attributes = True

class ChatMessageCreate(ChatMessageBase):
    session_id: int
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if v <= 0:
            raise ValueError('세션 ID는 양수여야 합니다.')
        return v

class ChatMessageUpdate(BaseModel):
    message_text: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatMessageResponse(ChatMessageBase):
    message_id: int
    session_id: int
    create_time: Optional[date] = None
    
    class Config:
        from_attributes = True

class ChatMessageWithRelations(ChatMessageResponse):
    session: Optional['ChatSessionResponse'] = None

class ChatMessageList(BaseModel):
    messages: List[ChatMessageResponse]
    total: int
    page: int
    per_page: int

class ChatMessageStats(BaseModel):
    total_messages: int
    user_messages: int
    chatbot_messages: int
    recent_messages: int  # 최근 24시간 내 메시지 수