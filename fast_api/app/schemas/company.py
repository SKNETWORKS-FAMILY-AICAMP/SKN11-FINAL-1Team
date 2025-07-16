# schemas/company.py
from pydantic import BaseModel, validator
from typing import Optional, List, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from .department import DepartmentResponse
    from .user import UserResponse

class CompanyBase(BaseModel):
    company_name: str
    
    class Config:
        from_attributes = True

class CompanyCreate(CompanyBase):
    company_id: str
    
    @validator('company_id')
    def validate_company_id(cls, v):
        pattern = r'^\d{3}-\d{2}-\d{5}$'
        if not re.match(pattern, v):
            raise ValueError('사업자번호는 000-00-00000 형식이어야 합니다.')
        return v

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class CompanyResponse(CompanyBase):
    company_id: str
    
    class Config:
        from_attributes = True

class CompanyWithRelations(CompanyResponse):
    departments: List['DepartmentResponse'] = []
    users: List['UserResponse'] = []

class CompanyList(BaseModel):
    companies: List[CompanyResponse]
    total: int
    page: int
    per_page: int

class CompanyStats(BaseModel):
    total_companies: int
    total_departments: int
    total_users: int
    active_departments: int