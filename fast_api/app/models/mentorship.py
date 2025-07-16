from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import re

Base = declarative_base()

class Mentorship(Base):
    __tablename__ = 'mentorships'
    
    mentorship_id = Column(Integer, primary_key=True, autoincrement=True, comment='멘토쉽 고유 ID')
    mentor_id = Column(Integer, nullable=False, comment='멘토 User ID')
    mentee_id = Column(Integer, nullable=False, comment='멘티 User ID')
    start_date = Column(Date, comment='시작일')
    end_date = Column(Date, comment='종료일')
    is_active = Column(Boolean, default=True, comment='멘토쉽 활성화 여부')
    curriculum_title = Column(String(255), nullable=False, comment='커리큘럼 제목')
    total_weeks = Column(Integer, default=0, comment='총 주차 수')
    
    # Relationships
    task_assigns = relationship("TaskAssign", back_populates="mentorship")
