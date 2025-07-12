from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Company(Base):
    """회사 테이블"""
    __tablename__ = "company"
    
    company_id = Column(Integer, primary_key=True, index=True, comment="사업자 번호")
    company_name = Column(String(255), nullable=False, comment="회사 이름")
    
    # 관계 설정
    departments = relationship("Department", back_populates="company")
    users = relationship("User", back_populates="company")


class Department(Base):
    """부서 테이블"""
    __tablename__ = "department"
    
    department_id = Column(Integer, primary_key=True, index=True, comment="부서 id")
    department_name = Column(String(255), nullable=False, unique=True, comment="부서 이름")
    description = Column(Text, comment="부서 설명")
    company_id = Column(Integer, ForeignKey("company.company_id"), comment="회사 아이디")
    
    # 관계 설정
    company = relationship("Company", back_populates="departments")
    templates = relationship("Template", back_populates="department")
    users = relationship("User", back_populates="department")
    docs = relationship("Docs", back_populates="department")


class User(Base):
    """사용자 테이블"""
    __tablename__ = "user"
    
    user_id = Column(Integer, primary_key=True, index=True, comment="유저 아이디(사번)")
    first_name = Column(String(100), nullable=False, comment="이름")
    last_name = Column(String(100), nullable=False, comment="성")
    email = Column(String(255), nullable=False, unique=True, comment="이메일")
    password = Column(String(255), nullable=False, comment="비밀번호")
    job_part = Column(String(100), nullable=False, comment="직무")
    position = Column(Integer, nullable=False, comment="직급")
    join_date = Column(Date, nullable=False, comment="입사일자")
    skill = Column(String(255), comment="자기소개 태그")
    role = Column(String(50), nullable=False, comment="mentor 또는 mentee")
    exp = Column(Integer, default=0, comment="경험치")
    admin = Column(Boolean, default=False, comment="관리자")
    department_id = Column(Integer, ForeignKey("department.department_id"), comment="부서 id")
    company_id = Column(Integer, ForeignKey("company.company_id"), comment="회사 id")
    
    # 관계 설정
    department = relationship("Department", back_populates="users")
    company = relationship("Company", back_populates="users")
    task_assignments = relationship("TaskAssign", back_populates="user")
    memos = relationship("Memo", back_populates="user")
    mentor_relationships = relationship("Mentorship", foreign_keys="[Mentorship.mentor_id]", back_populates="mentor")
    mentee_relationships = relationship("Mentorship", foreign_keys="[Mentorship.mentee_id]", back_populates="mentee")
    chat_sessions = relationship("ChatSession", back_populates="user")


class Template(Base):
    """템플릿 테이블"""
    __tablename__ = "template"
    
    template_id = Column(Integer, primary_key=True, index=True, comment="템플릿 id")
    template_title = Column(String(255), nullable=False, comment="템플릿 타이틀")
    template_description = Column(Text, comment="템플릿 설명")
    department_id = Column(Integer, ForeignKey("department.department_id"), comment="부서 id")
    
    # 관계 설정
    department = relationship("Department", back_populates="templates")
    task_manages = relationship("TaskManage", back_populates="template")


class TaskManage(Base):
    """태스크 관리 테이블"""
    __tablename__ = "task_manage"
    
    task_manage_id = Column(Integer, primary_key=True, index=True, comment="테스크 관리 id")
    title = Column(String(255), nullable=False, comment="제목")
    start_date = Column(Date, nullable=False, comment="시작일자")
    end_date = Column(Date, nullable=False, comment="완료일자")
    difficulty = Column(String(50), comment="난이도(5단계)")
    description = Column(Text, comment="설명")
    exp = Column(Integer, nullable=False, comment="경험치")
    order = Column(Integer, comment="정렬 순서")
    template_id = Column(Integer, ForeignKey("template.template_id"), comment="템플릿 id")
    
    # 관계 설정
    template = relationship("Template", back_populates="task_manages")
    task_assignments = relationship("TaskAssign", back_populates="task_manage")


class TaskAssign(Base):
    """태스크 할당 테이블"""
    __tablename__ = "task_assign"
    
    task_assign_id = Column(Integer, primary_key=True, index=True, comment="테스크 할당 id")
    title = Column(String(255), comment="제목")
    start_date = Column(Date, comment="시작일자")
    end_date = Column(Date, comment="완료일자")
    status = Column(Integer, nullable=False, comment="상태")
    difficulty = Column(String(50), comment="난이도(5단계)")
    description = Column(Text, comment="설명")
    exp = Column(Integer, comment="경험치")
    order = Column(Integer, comment="태스크 할당 순서")
    user_id = Column(Integer, ForeignKey("user.user_id"), comment="유저 아이디(사번)")
    task_manage_id = Column(Integer, ForeignKey("task_manage.task_manage_id"), comment="테스크 관리 id")
    mentorship_id = Column(Integer, ForeignKey("mentorship.mentorship_id"), comment="멘토쉽 id")
    
    # 관계 설정
    user = relationship("User", back_populates="task_assignments")
    task_manage = relationship("TaskManage", back_populates="task_assignments")
    mentorship = relationship("Mentorship", back_populates="task_assigns")
    subtasks = relationship("Subtask", back_populates="task_assign")
    memos = relationship("Memo", back_populates="task_assign")


class Subtask(Base):
    """하위 태스크 테이블"""
    __tablename__ = "subtask"
    
    subtask_id = Column(Integer, primary_key=True, index=True, comment="하위task id")
    task_assign_id = Column(Integer, ForeignKey("task_assign.task_assign_id"), comment="테스크 할당 id")
    
    # 관계 설정
    task_assign = relationship("TaskAssign", back_populates="subtasks")


class Mentorship(Base):
    """멘토링 테이블"""
    __tablename__ = "mentorship"
    
    mentorship_id = Column(Integer, primary_key=True, index=True, comment="멘토쉽 id")
    mentor_id = Column(Integer, ForeignKey("user.user_id"), comment="멘토 id")
    mentee_id = Column(Integer, ForeignKey("user.user_id"), comment="멘티 id")
    
    # 관계 설정
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="mentor_relationships")
    mentee = relationship("User", foreign_keys=[mentee_id], back_populates="mentee_relationships")
    task_assigns = relationship("TaskAssign", back_populates="mentorship")


class Memo(Base):
    """메모 테이블"""
    __tablename__ = "memo"
    
    memo_id = Column(Integer, primary_key=True, index=True, comment="id")
    create_date = Column(Date, comment="메모 생성일")
    comment = Column(Text, comment="메모 내용")
    task_assign_id = Column(Integer, ForeignKey("task_assign.task_assign_id"), comment="테스크 할당 id")
    user_id = Column(Integer, ForeignKey("user.user_id"), comment="유저 아이디")
    
    # 관계 설정
    task_assign = relationship("TaskAssign", back_populates="memos")
    user = relationship("User", back_populates="memos")


class ChatSession(Base):
    """채팅 세션 테이블"""
    __tablename__ = "chat_session"
    
    session_id = Column(Integer, primary_key=True, index=True, comment="검색 기록 고유 id")
    user_id = Column(Integer, ForeignKey("user.user_id"), comment="유저 아이디(사번)")
    summary = Column(Text, comment="채팅 내용 요약")

    
    # 관계 설정
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """채팅 메시지 테이블"""
    __tablename__ = "chat_message"
    
    message_id = Column(Integer, primary_key=True, index=True, comment="메세지 id")
    message_type = Column(String(50), comment="사용자 / 챗봇 구분")
    message_text = Column(Text, comment="메세지 내용")
    create_time = Column(DateTime, default=func.now(), comment="메세지 생성 시간")
    session_id = Column(Integer, ForeignKey("chat_session.session_id"), comment="검색 기록 고유 id")
    
    # 관계 설정
    session = relationship("ChatSession", back_populates="messages")


class Docs(Base):
    """문서 테이블"""
    __tablename__ = "docs"
    
    docs_id = Column(Integer, primary_key=True, index=True, comment="문서 id")
    title = Column(String(255), nullable=False, comment="제목")
    description = Column(Text, comment="문서 설명")
    file_path = Column(String(500), nullable=False, comment="파일 위치")
    create_time = Column(DateTime, default=func.now(), comment="문서 업로드 시점")
    common_doc = Column(Boolean, default=False, comment="공용 문서 여부")
    department_id = Column(Integer, ForeignKey("department.department_id"), comment="업로드한 부서 id")
    
    # 관계 설정
    department = relationship("Department", back_populates="docs") 