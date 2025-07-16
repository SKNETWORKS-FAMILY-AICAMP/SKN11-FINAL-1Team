# schemas/__init__.py
from .user import (
    UserRole,
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithRelations,
    UserLogin,
    UserLoginResponse,
    PasswordChange,
    UserList,
    UserStats,
)

from .company import (
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyWithRelations,
    CompanyList,
    CompanyStats,
)

from .department import (
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentWithRelations,
    DepartmentList,
    DepartmentStats,
)

from .mentorship import (
    TaskStatus,
    TaskPriority,
    MentorshipBase,
    MentorshipCreate,
    MentorshipUpdate,
    MentorshipResponse,
    MentorshipWithRelations,
    MentorshipList,
    TaskAssignBase,
    TaskAssignCreate,
    TaskAssignUpdate,
    TaskAssignResponse,
    TaskAssignWithRelations,
    TaskAssignList,
    SubtaskBase,
    SubtaskCreate,
    SubtaskUpdate,
    SubtaskResponse,
    SubtaskWithRelations,
    MemoBase,
    MemoCreate,
    MemoUpdate,
    MemoResponse,
    MemoWithRelations,
    MemoList,
)

from .task import (
    CurriculumBase,
    CurriculumCreate,
    CurriculumUpdate,
    CurriculumResponse,
    CurriculumWithRelations,
    CurriculumList,
    CurriculumStats,
    TaskManageBase,
    TaskManageCreate,
    TaskManageUpdate,
    TaskManageResponse,
    TaskManageWithRelations,
    TaskManageList,
    TaskManageStats,
    DocsBase,
    DocsCreate,
    DocsUpdate,
    DocsResponse,
    DocsWithRelations,
    DocsList,
    DocsStats,
    ChatSessionBase,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatSessionWithRelations,
    ChatSessionList,
    ChatSessionStats,
    ChatMessageBase,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageResponse,
    ChatMessageWithRelations,
    ChatMessageList,
    ChatMessageStats,
)

# Forward references 해결
from .user import UserWithRelations
from .company import CompanyWithRelations
from .department import DepartmentWithRelations
from .mentorship import (
    MentorshipWithRelations,
    TaskAssignWithRelations,
    SubtaskWithRelations,
    MemoWithRelations,
)
from .task import (
    CurriculumWithRelations,
    TaskManageWithRelations,
    DocsWithRelations,
    ChatSessionWithRelations,
    ChatMessageWithRelations,
)

# 모든 With Relations 모델들의 forward references 업데이트
UserWithRelations.model_rebuild()
CompanyWithRelations.model_rebuild()
DepartmentWithRelations.model_rebuild()
MentorshipWithRelations.model_rebuild()
TaskAssignWithRelations.model_rebuild()
SubtaskWithRelations.model_rebuild()
MemoWithRelations.model_rebuild()
CurriculumWithRelations.model_rebuild()
TaskManageWithRelations.model_rebuild()
DocsWithRelations.model_rebuild()
ChatSessionWithRelations.model_rebuild()
ChatMessageWithRelations.model_rebuild()

__all__ = [
    # User schemas
    "UserRole",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserWithRelations",
    "UserLogin",
    "UserLoginResponse",
    "PasswordChange",
    "UserList",
    "UserStats",
    
    # Company schemas
    "CompanyBase",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyWithRelations",
    "CompanyList",
    "CompanyStats",
    
    # Department schemas
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentWithRelations",
    "DepartmentList",
    "DepartmentStats",
    
    # Mentorship schemas
    "TaskStatus",
    "TaskPriority",
    "MentorshipBase",
    "MentorshipCreate",
    "MentorshipUpdate",
    "MentorshipResponse",
    "MentorshipWithRelations",
    "MentorshipList",
    "MentorshipStats",
    "TaskAssignBase",
    "TaskAssignCreate",
    "TaskAssignUpdate",
    "TaskAssignResponse",
    "TaskAssignWithRelations",
    "TaskAssignList",
    "SubtaskBase",
    "SubtaskCreate",
    "SubtaskUpdate",
    "SubtaskResponse",
    "SubtaskWithRelations",

    "MemoBase",
    "MemoCreate",
    "MemoUpdate",
    "MemoResponse",
    "MemoWithRelations",
    "MemoList",
    
    # Task schemas
    "CurriculumBase",
    "CurriculumCreate",
    "CurriculumUpdate",
    "CurriculumResponse",
    "CurriculumWithRelations",
    "CurriculumList",
    "CurriculumStats",
    "TaskManageBase",
    "TaskManageCreate",
    "TaskManageUpdate",
    "TaskManageResponse",
    "TaskManageWithRelations",
    "TaskManageList",
    "TaskManageStats",
    "DocsBase",
    "DocsCreate",
    "DocsUpdate",
    "DocsResponse",
    "DocsWithRelations",
    "DocsList",
    "DocsStats",
    "ChatSessionBase",
    "ChatSessionCreate",
    "ChatSessionUpdate",
    "ChatSessionResponse",
    "ChatSessionWithRelations",
    "ChatSessionList",
    "ChatSessionStats",
    "ChatMessageBase",
    "ChatMessageCreate",
    "ChatMessageUpdate",
    "ChatMessageResponse",
    "ChatMessageWithRelations",
    "ChatMessageList",
    "ChatMessageStats",
]