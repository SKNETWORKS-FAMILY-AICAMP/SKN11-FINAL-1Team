# schemas/department.py
from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .company import CompanyResponse
    from .user import UserResponse
    from .task import DocsResponse, CurriculumResponse

class DepartmentBase(BaseModel):
    department_name: str
    description: Optional[str] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True

class DepartmentCreate(DepartmentBase):
    company_id: str

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    class Config:
        from_attributes = True

class DepartmentResponse(DepartmentBase):
    department_id: int
    company_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class DepartmentWithRelations(DepartmentResponse):
    company: Optional['CompanyResponse'] = None
    users: List['UserResponse'] = []
    docs: List['DocsResponse'] = []
    curriculums: List['CurriculumResponse'] = []

class DepartmentList(BaseModel):
    departments: List[DepartmentResponse]
    total: int
    page: int
    per_page: int

class DepartmentStats(BaseModel):
    total_departments: int
    active_departments: int
    total_users: int
    total_docs: int
    total_curriculums: int