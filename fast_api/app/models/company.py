from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import re

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    
    company_id = Column(String(12), primary_key=True, comment='회사 고유 사업자번호(Primary Key)')
    company_name = Column(String(255), nullable=False, comment='회사명')
    
    # Relationships
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company")
    
    def __str__(self):
        return self.company_name
    
    def validate_company_id(self):
        """사업자번호 유효성 검사"""
        pattern = r'^\d{3}-\d{2}-\d{5}$'
        if not re.match(pattern, self.company_id):
            raise ValueError('사업자번호는 000-00-00000 형식이어야 합니다.')
