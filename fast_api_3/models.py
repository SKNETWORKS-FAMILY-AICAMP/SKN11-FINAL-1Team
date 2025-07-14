from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from database import Base

class Company(Base):
    __tablename__ = "core_company"
    
    company_id = Column(String(12), primary_key=True, index=True)  # 사업자번호
    company_name = Column(String(255), nullable=False)
    
    # 관계 설정
    departments = relationship("Department", back_populates="company")
    users = relationship("User", back_populates="company")

class Department(Base):
    __tablename__ = "core_department"
    
    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(50), nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)
    company_id = Column(String(12), ForeignKey("core_company.company_id"))
    
    # 관계 설정
    company = relationship("Company", back_populates="departments")
    users = relationship("User", back_populates="department")
    curriculums = relationship("Curriculum", back_populates="department")
    docs = relationship("Docs", back_populates="department")

class User(Base):
    __tablename__ = "core_user"
    
    user_id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(Integer, unique=True)
    is_admin = Column(Boolean, default=False)
    mentorship_id = Column(Integer)
    tag = Column(String(255))
    exp = Column(Integer, default=0)
    role = Column(String(20), nullable=False)  # 'mentee' 또는 'mentor'
    join_date = Column(Date)
    position = Column(String(50), nullable=False)
    job_part = Column(String(50), nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    company_id = Column(String(12), ForeignKey("core_company.company_id"))
    department_id = Column(Integer, ForeignKey("core_department.department_id"))
    
    # 관계 설정
    company = relationship("Company", back_populates="users")
    department = relationship("Department", back_populates="users")
    chat_sessions = relationship("ChatSession", back_populates="user")
    task_assigns = relationship("TaskAssign", back_populates="user")
    memos = relationship("Memo", back_populates="user")
    
    # 멘토쉽 관계
    mentorships_as_mentor = relationship("Mentorship", foreign_keys="[Mentorship.mentor_id]", back_populates="mentor")
    mentorships_as_mentee = relationship("Mentorship", foreign_keys="[Mentorship.mentee_id]", back_populates="mentee")

class Curriculum(Base):
    __tablename__ = "core_curriculum"
    
    curriculum_id_id = Column(Integer, primary_key=True, index=True)  # 실제 스키마에 맞춤
    curriculum_description = Column(String(255))
    curriculum_title = Column(String(255), nullable=False)
    common = Column(Boolean, default=False)
    total_weeks = Column(Integer, default=0)
    week_schedule = Column(Text)
    department_id = Column(Integer, ForeignKey("core_department.department_id"))
    
    # 관계 설정
    department = relationship("Department", back_populates="curriculums")
    task_manages = relationship("TaskManage", back_populates="curriculum")

class Docs(Base):
    __tablename__ = "core_docs"
    
    docs_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255))
    file_path = Column(String(255), nullable=False)
    create_time = Column(DateTime)
    common_doc = Column(Boolean, default=False)
    department_id = Column(Integer, ForeignKey("core_department.department_id"))
    
    # 관계 설정
    department = relationship("Department", back_populates="docs")

class Mentorship(Base):
    __tablename__ = "core_mentorship"
    
    mentorship_id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("core_user.user_id"))
    mentee_id = Column(Integer, ForeignKey("core_user.user_id"))
    
    # 관계 설정
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="mentorships_as_mentor")
    mentee = relationship("User", foreign_keys=[mentee_id], back_populates="mentorships_as_mentee")
    task_assigns = relationship("TaskAssign", back_populates="mentorship")

class TaskManage(Base):
    __tablename__ = "core_taskmanage"
    
    task_manage_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255))
    guideline = Column(String(255))
    week = Column(Integer, nullable=False)
    order = Column(Integer)
    period = Column(Integer)
    priority = Column(String(2))  # '상', '중', '하'
    curriculum_id_id = Column(Integer, ForeignKey("core_curriculum.curriculum_id_id"))
    
    # 관계 설정
    curriculum = relationship("Curriculum", back_populates="task_manages")

class ChatSession(Base):
    __tablename__ = "core_chatsession"
    
    session_id = Column(Integer, primary_key=True, index=True)
    summary = Column(String(255))
    user_id = Column(Integer, ForeignKey("core_user.user_id"))
    
    # 관계 설정
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class TaskAssign(Base):
    __tablename__ = "core_taskassign"
    
    task_assign_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Integer, nullable=False)
    difficulty = Column(String(50))
    description = Column(String(255))
    exp = Column(Integer)
    order = Column(Integer)
    user_id = Column(Integer, ForeignKey("core_user.user_id"))
    mentorship_id = Column(Integer, ForeignKey("core_mentorship.mentorship_id"))
    
    # 관계 설정
    user = relationship("User", back_populates="task_assigns")
    mentorship = relationship("Mentorship", back_populates="task_assigns")
    subtasks = relationship("Subtask", back_populates="task_assign")
    memos = relationship("Memo", back_populates="task_assign")

class ChatMessage(Base):
    __tablename__ = "core_chatmessage"
    
    message_id = Column(Integer, primary_key=True, index=True)
    message_type = Column(String(10), nullable=False)  # 'user' 또는 'chatbot'
    message_text = Column(String(1000))
    create_time = Column(Date)
    session_id = Column(Integer, ForeignKey("core_chatsession.session_id"))
    
    # 관계 설정
    session = relationship("ChatSession", back_populates="messages")

class Subtask(Base):
    __tablename__ = "core_subtask"
    
    subtask_id = Column(Integer, primary_key=True, index=True)
    task_assign_id = Column(Integer, ForeignKey("core_taskassign.task_assign_id"))
    
    # 관계 설정
    task_assign = relationship("TaskAssign", back_populates="subtasks")

class Memo(Base):
    __tablename__ = "core_memo"
    
    memo_id = Column(Integer, primary_key=True, index=True)
    create_date = Column(Date)
    comment = Column(String(1000))
    user_id = Column(Integer, ForeignKey("core_user.user_id"))
    task_assign_id = Column(Integer, ForeignKey("core_taskassign.task_assign_id"))
    
    # 관계 설정
    user = relationship("User", back_populates="memos")
    task_assign = relationship("TaskAssign", back_populates="memos") 