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

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True, comment='유저 고유 ID')
    employee_number = Column(Integer, unique=True, comment='사번')
    is_admin = Column(Boolean, default=False, comment='관리자 여부')
    mentorship_id = Column(Integer, comment='멘토쉽 ID(옵션)')
    company_id = Column(String(12), ForeignKey('companies.company_id', ondelete='SET NULL'), comment='소속 회사')
    department_id = Column(Integer, ForeignKey('departments.department_id', ondelete='SET NULL'), comment='소속 부서')
    tag = Column(String(255), comment='유저 태그')
    role = Column(String(20), comment='역할(멘티/멘토)')  # 'mentee' or 'mentor'
    join_date = Column(Date, default=func.current_date(), comment='입사일')
    position = Column(String(50), nullable=False, comment='직위')
    job_part = Column(String(50), nullable=False, comment='직무')
    email = Column(String(255), unique=True, nullable=False, comment='이메일(로그인 ID)')
    password_hash = Column(String(128), nullable=False, comment='비밀번호 해시')
    
    last_name = Column(String(50), nullable=False, comment='성')
    first_name = Column(String(50), nullable=False, comment='이름')
    last_login = Column(DateTime, default=func.now(), comment='마지막 로그인 시각')
    
    is_active = Column(Boolean, default=True, comment='활성화 여부')
    is_staff = Column(Boolean, default=False, comment='스태프 여부')
    
    # Relationships
    company = relationship("Company", back_populates="users")
    department = relationship("Department", back_populates="users")
    chat_sessions = relationship("ChatSession", back_populates="user")
    memos = relationship("Memo", back_populates="user")
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_full_name(self):
        """전체 이름 반환"""
        return f'{self.last_name} {self.first_name}'
    
    def set_password(self, password):
        """비밀번호 해시 저장"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password_hash, password)
    
    def validate_role(self):
        """역할 유효성 검사"""
        if self.role not in ['mentee', 'mentor']:
            raise ValueError('역할은 mentee 또는 mentor여야 합니다.')

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    session_id = Column(Integer, primary_key=True, autoincrement=True, comment='채팅 세션 고유 ID')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='사용자')
    summary = Column(String(255), comment='세션 요약')
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True, comment='메시지 고유 ID')
    message_type = Column(String(10), nullable=False, comment='메시지 타입(user/chatbot)')
    message_text = Column(String(1000), comment='메시지 내용')
    create_time = Column(Date, default=func.current_date(), comment='메시지 생성일')
    session_id = Column(Integer, ForeignKey('chat_sessions.session_id', ondelete='CASCADE'), nullable=False, comment='채팅 세션')
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def validate_message_type(self):
        """메시지 타입 유효성 검사"""
        if self.message_type not in ['user', 'chatbot']:
            raise ValueError('메시지 타입은 user 또는 chatbot이어야 합니다.')

class Docs(Base):
    __tablename__ = 'docs'
    
    docs_id = Column(Integer, primary_key=True, autoincrement=True, comment='문서 고유 ID')
    department_id = Column(Integer, ForeignKey('departments.department_id', ondelete='CASCADE'), nullable=False, comment='소속 부서')
    title = Column(String(255), nullable=False, comment='문서 제목')
    description = Column(String(255), comment='문서 설명')
    file_path = Column(String(255), nullable=False, comment='파일 경로')
    create_time = Column(DateTime, default=func.now(), comment='생성일')
    common_doc = Column(Boolean, default=False, comment='공용 문서 여부')
    
    # Relationships
    department = relationship("Department", back_populates="docs")

class Curriculum(Base):
    __tablename__ = 'curriculums'
    
    curriculum_id = Column(Integer, primary_key=True, autoincrement=True, comment='커리큘럼 고유 ID')
    curriculum_description = Column(String(255), comment='커리큘럼 설명')
    curriculum_title = Column(String(255), nullable=False, comment='커리큘럼 제목')
    department_id = Column(Integer, ForeignKey('departments.department_id', ondelete='CASCADE'), comment='소속 부서')
    common = Column(Boolean, default=False, comment='공용 커리큘럼 여부')
    total_weeks = Column(Integer, default=0, comment='총 주차 수')
    week_schedule = Column(Text, comment='주차별 온보딩 일정(1주차: ~\n2주차: ~\n3주차: ~ 형식)')
    
    # Relationships
    department = relationship("Department", back_populates="curriculums")
    tasks = relationship("TaskManage", back_populates="curriculum")
    
    def __str__(self):
        return self.curriculum_title

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

class Memo(Base):
    __tablename__ = 'memos'
    
    memo_id = Column(Integer, primary_key=True, autoincrement=True, comment='메모 고유 ID')
    create_date = Column(Date, default=func.current_date(), comment='생성일')
    comment = Column(String(1000), comment='메모 내용')
    task_assign_id = Column(Integer, ForeignKey('task_assigns.task_assign_id', ondelete='CASCADE'), nullable=False, comment='과제 할당')
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='유저')
    
    # Relationships
    task_assign = relationship("TaskAssign", back_populates="memos")
    user = relationship("User", back_populates="memos")