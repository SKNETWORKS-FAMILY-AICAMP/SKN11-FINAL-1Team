from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import re

Base = declarative_base()

class Department(Base):
    __tablename__ = 'departments'
    
    department_id = Column(Integer, primary_key=True, autoincrement=True, comment='부서 고유 ID')
    department_name = Column(String(50), nullable=False, comment='부서명')
    description = Column(String(255), comment='부서 설명')
    company_id = Column(String(12), ForeignKey('companies.company_id', ondelete='CASCADE'), comment='소속 회사')
    is_active = Column(Boolean, default=True, comment='부서 활성화 여부')
    
    # Relationships
    company = relationship("Company", back_populates="departments")
    users = relationship("User", back_populates="department")
    docs = relationship("Docs", back_populates="department")
    curriculums = relationship("Curriculum", back_populates="department")
    
    __table_args__ = (
        UniqueConstraint('department_name', 'company_id', name='unique_department_per_company'),
    )
    
    def __str__(self):
        return self.department_name