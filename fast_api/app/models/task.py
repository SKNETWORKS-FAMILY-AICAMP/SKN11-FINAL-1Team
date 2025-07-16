from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import re

Base = declarative_base()

class TaskManage(Base):
    __tablename__ = 'task_manages'
    
    task_manage_id = Column(Integer, primary_key=True, autoincrement=True, comment='과제 관리 고유 ID')
    curriculum_id = Column(Integer, ForeignKey('curriculums.curriculum_id', ondelete='CASCADE'), nullable=False, comment='소속 커리큘럼')
    title = Column(String(255), nullable=False, comment='과제 제목')
    description = Column(String(255), comment='과제 설명')
    guideline = Column(String(255), comment='과제 가이드라인')
    week = Column(Integer, nullable=False, comment='몇 주차 과제인지')
    order = Column(Integer, comment='과제 순서')
    period = Column(Integer, comment='과제 기간')
    priority = Column(String(2), comment='과제 우선순위(상/중/하)')
    
    # Relationships
    curriculum = relationship("Curriculum", back_populates="tasks")
    
    def __str__(self):
        return f"{self.curriculum.curriculum_title} - {self.title} (Week {self.week})"
    
    def validate_priority(self):
        """우선순위 유효성 검사"""
        if self.priority and self.priority not in ['상', '중', '하']:
            raise ValueError('우선순위는 상, 중, 하 중 하나여야 합니다.')


class TaskAssign(Base):
    __tablename__ = 'task_assigns'
    
    task_assign_id = Column(Integer, primary_key=True, autoincrement=True, comment='과제 할당 고유 ID')
    mentorship_id = Column(Integer, ForeignKey('mentorships.mentorship_id', ondelete='CASCADE'), nullable=False, comment='멘토쉽')
    title = Column(String(255), comment='과제 할당 제목')
    description = Column(String(255), comment='설명')
    guideline = Column(String(255), comment='과제 가이드라인')
    week = Column(Integer, nullable=False, comment='몇 주차 과제인지')
    order = Column(Integer, comment='과제 순서')
    start_date = Column(Date, comment='시작일')
    end_date = Column(Date, comment='종료일')
    status = Column(String(10), comment='과제 상태(진행 전/진행 중/검토요청/완료)')
    priority = Column(String(2), comment='과제 우선순위(상/중/하)')
    
    # Relationships
    mentorship = relationship("Mentorship", back_populates="task_assigns")
    subtasks = relationship("Subtask", back_populates="task_assign")
    memos = relationship("Memo", back_populates="task_assign")
    
    def validate_status(self):
        """상태 유효성 검사"""
        valid_statuses = ['진행 전', '진행 중', '검토 요청', '완료']
        if self.status and self.status not in valid_statuses:
            raise ValueError(f'상태는 {", ".join(valid_statuses)} 중 하나여야 합니다.')
    
    def validate_priority(self):
        """우선순위 유효성 검사"""
        if self.priority and self.priority not in ['상', '중', '하']:
            raise ValueError('우선순위는 상, 중, 하 중 하나여야 합니다.')

class Subtask(Base):
    __tablename__ = 'subtasks'
    
    subtask_id = Column(Integer, primary_key=True, autoincrement=True, comment='서브태스크 고유 ID')
    task_assign_id = Column(Integer, ForeignKey('task_assigns.task_assign_id', ondelete='CASCADE'), nullable=False, comment='상위 과제 할당')
    
    # Relationships
    task_assign = relationship("TaskAssign", back_populates="subtasks")
