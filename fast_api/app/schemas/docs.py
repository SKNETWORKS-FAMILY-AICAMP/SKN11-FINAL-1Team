from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocsBase(BaseModel):
    title: str
    description: Optional[str] = None
    common_doc: bool = False
    department_id: Optional[int] = None

class DocsCreate(DocsBase):
    pass

class DocsUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    common_doc: Optional[bool] = None
    department_id: Optional[int] = None

class DocsResponse(DocsBase):
    docs_id: int
    file_path: str
    create_time: datetime
    
    class Config:
        from_attributes = True 