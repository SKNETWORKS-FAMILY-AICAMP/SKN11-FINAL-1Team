from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Company(Base):
    """회사 테이블"""
    __tablename__ = "core_company"
    
    company_id = Column(String(12), primary_key=True, index=True, comment="회사 고유 사업자번호(Primary Key)")
    company_name = Column(String(255), nullable=False, comment="회사명")
    
    # 관계 설정
    departments = relationship("Department", back_populates="company")
    users = relationship("User", back_populates="company")


class Department(Base):
    """부서 테이블"""
    __tablename__ = "core_department"
    
    department_id = Column(Integer, primary_key=True, index=True, comment="부서 고유 ID")
    department_name = Column(String(50), nullable=False, comment="부서명")
    description = Column(String(255), comment="부서 설명")
    company_id = Column(String(12), ForeignKey("core_company.company_id"), comment="소속 회사")
    is_active = Column(Boolean, default=True, comment="부서 활성화 여부")
    
    # 관계 설정
    company = relationship("Company", back_populates="departments")
    users = relationship("User", back_populates="department")
    docs = relationship("Docs", back_populates="department")
    curriculums = relationship("Curriculum", back_populates="department")


class User(Base):
    """사용자 테이블"""
    __tablename__ = "core_user"
    
    user_id = Column(Integer, primary_key=True, index=True, comment="유저 고유 ID")
    employee_number = Column(Integer, comment="사번")
    is_admin = Column(Boolean, default=False, comment="관리자 여부")
    is_superuser = Column(Boolean, default=False, nullable=False, comment="최고 관리자 여부")
    company_id = Column(String(12), ForeignKey("core_company.company_id"), comment="소속 회사")
    department_id = Column(Integer, ForeignKey("core_department.department_id"), comment="소속 부서")
    tag = Column(String(255), comment="유저 태그")
    role = Column(String(20), nullable=False, comment="역할(멘티/멘토)")
    join_date = Column(Date, comment="입사일")
    position = Column(String(50), nullable=False, comment="직위")
    job_part = Column(String(50), nullable=False, comment="직무")
    email = Column(String(255), nullable=False, unique=True, comment="이메일(로그인 ID)")
    password = Column(String(128), nullable=False, comment="비밀번호")
    last_name = Column(String(50), nullable=False, comment="성")
    first_name = Column(String(50), nullable=False, comment="이름")
    last_login = Column(DateTime, comment="마지막 로그인 시각")
    profile_image = Column(String(255), comment="프로필 이미지")
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    is_staff = Column(Boolean, default=False, comment="스태프 여부")
    
    # 관계 설정
    department = relationship("Department", back_populates="users")
    company = relationship("Company", back_populates="users")
    memos = relationship("Memo", back_populates="user")
    mentor_relationships = relationship("Mentorship", foreign_keys="[Mentorship.mentor_id]", back_populates="mentor")
    mentee_relationships = relationship("Mentorship", foreign_keys="[Mentorship.mentee_id]", back_populates="mentee")
    chat_sessions = relationship("ChatSession", back_populates="user")
    alarms = relationship("Alarm", back_populates="user")


class Alarm(Base):
    """알림 테이블"""
    __tablename__ = "core_alarm"
    
    id = Column(Integer, primary_key=True, index=True, comment="알림 고유 ID")
    user_id = Column(Integer, ForeignKey("core_user.user_id"), nullable=False, comment="알림 대상 유저")
    message = Column(Text, nullable=False, comment="알림 메시지")
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    
    # 관계 설정
    user = relationship("User", back_populates="alarms")


class Mentorship(Base):
    """멘토쉽 테이블"""
    __tablename__ = "core_mentorship"
    
    mentorship_id = Column(Integer, primary_key=True, index=True, comment="멘토쉽 고유 ID")
    mentor_id = Column(Integer, ForeignKey("core_user.user_id"), nullable=False, comment="멘토 User ID")
    mentee_id = Column(Integer, ForeignKey("core_user.user_id"), nullable=False, comment="멘티 User ID")
    start_date = Column(Date, comment="시작일")
    end_date = Column(Date, comment="종료일")
    is_active = Column(Boolean, default=True, comment="멘토쉽 활성화 여부")
    curriculum_title = Column(String(255), comment="커리큘럼 제목")
    total_weeks = Column(Integer, default=0, comment="총 주차 수")
    
    # 관계 설정
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="mentor_relationships")
    mentee = relationship("User", foreign_keys=[mentee_id], back_populates="mentee_relationships")
    task_assigns = relationship("TaskAssign", back_populates="mentorship")


class Curriculum(Base):
    """커리큘럼 테이블"""
    __tablename__ = "core_curriculum"
    
    curriculum_id = Column(Integer, primary_key=True, index=True, comment="커리큘럼 고유 ID")
    curriculum_description = Column(String(255), comment="커리큘럼 설명")
    curriculum_title = Column(String(255), nullable=False, comment="커리큘럼 제목")
    department_id = Column(Integer, ForeignKey("core_department.department_id"), comment="소속 부서")
    common = Column(Boolean, default=False, comment="공용 커리큘럼 여부")
    total_weeks = Column(Integer, default=0, comment="총 주차 수")
    week_schedule = Column(Text, comment="주차별 온보딩 일정(1주차: ~\n2주차: ~\n3주차: ~ 형식)")
    
    # 관계 설정
    department = relationship("Department", back_populates="curriculums")
    tasks = relationship("TaskManage", back_populates="curriculum")


class TaskManage(Base):
    """태스크 관리 테이블"""
    __tablename__ = "core_taskmanage"
    
    task_manage_id = Column(Integer, primary_key=True, index=True, comment="과제 관리 고유 ID")
    curriculum_id = Column(Integer, ForeignKey("core_curriculum.curriculum_id"), comment="소속 커리큘럼")
    title = Column(String(255), nullable=False, comment="과제 제목")
    description = Column(String(255), comment="과제 설명")
    guideline = Column(String(255), comment="과제 가이드라인")
    week = Column(Integer, nullable=False, comment="몇 주차 과제인지")
    order = Column(Integer, comment="과제 순서")
    period = Column(Integer, comment="과제 기간")
    priority = Column(String(2), comment="과제 우선순위(상/중/하)")
    
    # 관계 설정
    curriculum = relationship("Curriculum", back_populates="tasks")


class TaskAssign(Base):
    """태스크 할당 테이블"""
    __tablename__ = "core_taskassign"
    
    task_assign_id = Column(Integer, primary_key=True, index=True, comment="과제 할당 고유 ID")
    parent_id = Column(Integer, ForeignKey("core_taskassign.task_assign_id"), comment="상위 과제(TaskAssign)")
    mentorship_id = Column("mentorship_id_id", Integer, ForeignKey("core_mentorship.mentorship_id"), nullable=False, comment="멘토쉽")
    title = Column(String(255), comment="과제 할당 제목")
    description = Column(String(255), comment="설명")
    guideline = Column(String(255), comment="과제 가이드라인")
    week = Column(Integer, nullable=False, comment="몇 주차 과제인지")
    order = Column(Integer, comment="과제 순서")
    scheduled_start_date = Column(Date, comment="예정 시작일")
    scheduled_end_date = Column(Date, comment="예정 종료일")
    real_start_date = Column(Date, comment="실제 시작일")
    real_end_date = Column(Date, comment="실제 종료일")
    status = Column(String(10), comment="과제 상태(진행전/진행중/검토요청/완료)")
    priority = Column(String(2), comment="과제 우선순위(상/중/하)")
    
    # 관계 설정
    parent = relationship("TaskAssign", remote_side=[task_assign_id], back_populates="subtasks")
    subtasks = relationship("TaskAssign", back_populates="parent")
    mentorship = relationship("Mentorship", back_populates="task_assigns")
    memos = relationship("Memo", back_populates="task_assign")



class Memo(Base):
    """메모 테이블"""
    __tablename__ = "core_memo"
    
    memo_id = Column(Integer, primary_key=True, index=True, comment="메모 고유 ID")
    create_date = Column(Date, comment="생성일")
    comment = Column(String(1000), comment="메모 내용")
    task_assign_id = Column(Integer, ForeignKey("core_taskassign.task_assign_id"), nullable=False, comment="과제 할당")
    user_id = Column(Integer, ForeignKey("core_user.user_id"), comment="유저")
    
    # 관계 설정
    task_assign = relationship("TaskAssign", back_populates="memos")
    user = relationship("User", back_populates="memos")


class ChatSession(Base):
    """채팅 세션 테이블"""
    __tablename__ = "core_chatsession"
    
    session_id = Column(Integer, primary_key=True, index=True, comment="채팅 세션 고유 ID")
    user_id = Column(Integer, ForeignKey("core_user.user_id", ondelete="CASCADE"), nullable=False, comment="사용자")
    summary = Column(String(255), comment="세션 요약")
    is_active = Column(Boolean, default=True, comment="세션 활성화 여부")
    
    # 관계 설정
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """채팅 메시지 테이블"""
    __tablename__ = "core_chatmessage"
    
    message_id = Column(Integer, primary_key=True, index=True, comment="메시지 고유 ID")
    message_type = Column(String(10), nullable=False, comment="메시지 타입(user/chatbot)")
    message_text = Column(String(1000), comment="메시지 내용")
    create_time = Column(Date, comment="메시지 생성일")
    is_active = Column(Boolean, default=True, comment="메시지 활성화 여부")
    session_id = Column(
        Integer,
        ForeignKey("core_chatsession.session_id", ondelete="CASCADE"),  # ← CASCADE 추가
        nullable=False,
        comment="채팅 세션"
    )
    
    # 관계 설정
    session = relationship("ChatSession", back_populates="messages")


class Docs(Base):
    """문서 테이블"""
    __tablename__ = "core_docs"
    
    docs_id = Column(Integer, primary_key=True, index=True, comment="문서 고유 ID")
    title = Column(String(255), nullable=False, comment="문서 제목")
    description = Column(String(255), comment="문서 설명")
    file_path = Column(String(255), nullable=False, comment="파일 경로")
    create_time = Column(DateTime, default=func.now(), comment="생성일")
    common_doc = Column(Boolean, default=False, comment="공용 문서 여부")
    department_id = Column(Integer, ForeignKey("core_department.department_id"), nullable=False, comment="소속 부서")
    original_file_name = Column(String(255), comment="원본 파일명")
    
    # 관계 설정
    department = relationship("Department", back_populates="docs") 