# schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from enum import Enum

if TYPE_CHECKING:
    from .company import CompanyResponse
    from .department import DepartmentResponse

class UserRole(str, Enum):
    MENTEE = "mentee"
    MENTOR = "mentor"

class UserBase(BaseModel):
    employee_number: Optional[int] = None
    email: EmailStr
    first_name: str
    last_name: str
    position: str
    job_part: str
    role: UserRole
    tag: Optional[str] = None
    is_admin: bool = False
    
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str
    company_id: Optional[str] = None
    department_id: Optional[int] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다.')
        return v

class UserUpdate(BaseModel):
    employee_number: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    job_part: Optional[str] = None
    role: Optional[UserRole] = None
    tag: Optional[str] = None
    is_admin: Optional[bool] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    user_id: int
    company_id: Optional[str] = None
    department_id: Optional[int] = None
    join_date: Optional[date] = None
    last_login: Optional[datetime] = None
    is_active: bool
    is_staff: bool
    
    class Config:
        from_attributes = True

class UserWithRelations(UserResponse):
    company: Optional['CompanyResponse'] = None
    department: Optional['DepartmentResponse'] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('새 비밀번호는 8자 이상이어야 합니다.')
        return v

class UserList(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int

class UserStats(BaseModel):
    total_users: int
    total_mentors: int
    total_mentees: int
    active_users: int
    inactive_users: int