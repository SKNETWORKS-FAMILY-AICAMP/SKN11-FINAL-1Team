from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import models
import schemas
from passlib.context import CryptContext

# 비밀번호 암호화 설정
pwd_context = CryptContext(
    schemes=[
        "bcrypt", 
        "pbkdf2_sha256", 
        "django_pbkdf2_sha256",
        "django_pbkdf2_sha1",
        "django_bcrypt",
        "argon2"
    ],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """비밀번호 해시화"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # 해시 형식을 인식할 수 없는 경우 False 반환
        print(f"Password verification error: {e}")
        print(f"Hash format: {hashed_password[:50]}...")
        return False


# Company CRUD
def create_company(db: Session, company: schemas.CompanyCreate):
    """회사 생성"""
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_company(db: Session, company_id: str):
    """회사 단일 조회"""
    return db.query(models.Company).filter(models.Company.company_id == company_id).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    """회사 목록 조회"""
    return db.query(models.Company).offset(skip).limit(limit).all()

def update_company(db: Session, company_id: str, company_update: schemas.CompanyCreate):
    """회사 정보 업데이트"""
    db_company = get_company(db, company_id)
    if db_company:
        for key, value in company_update.dict().items():
            setattr(db_company, key, value)
        db.commit()
        db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: str):
    """회사 삭제"""
    db_company = get_company(db, company_id)
    if db_company:
        db.delete(db_company)
        db.commit()
    return db_company


# Department CRUD
def create_department(db: Session, department: schemas.DepartmentCreate):
    """부서 생성"""
    db_department = models.Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def get_department(db: Session, department_id: int):
    """부서 단일 조회"""
    return db.query(models.Department).filter(models.Department.department_id == department_id).first()

def get_departments(db: Session, skip: int = 0, limit: int = 100):
    """부서 목록 조회"""
    return db.query(models.Department).offset(skip).limit(limit).all()

def update_department(db: Session, department_id: int, department_update: schemas.DepartmentUpdate):
    """부서 정보 업데이트"""
    db_department = get_department(db, department_id)
    if db_department:
        for key, value in department_update.dict(exclude_unset=True).items():
            setattr(db_department, key, value)
        db.commit()
        db.refresh(db_department)
    return db_department

# Department CRUD - 수정된 함수들
def get_department_by_company(db: Session, department_id: int, company_id: str):
    """회사별 부서 조회 (검증용)"""
    return db.query(models.Department).filter(
        and_(
            models.Department.department_id == department_id,
            models.Department.company_id == company_id
        )
    ).first()

def delete_department_with_company(db: Session, department_id: int, company_id: str):
    """회사 정보를 검증하여 부서 삭제"""
    # 1. 회사 존재 확인
    company = get_company(db, company_id)
    if not company:
        return None, "회사를 찾을 수 없습니다."
    
    # 2. 해당 회사의 부서인지 확인
    db_department = get_department_by_company(db, department_id, company_id)
    if not db_department:
        return None, "해당 회사의 부서를 찾을 수 없습니다."
    
    # 3. 부서에 속한 사용자가 있는지 확인
    users_in_department = db.query(models.User).filter(
        models.User.department_id == department_id
    ).first()
    if users_in_department:
        return None, "부서에 속한 사용자가 있어 삭제할 수 없습니다."
    
    # 4. 삭제 실행
    db.delete(db_department)
    db.commit()
    return db_department, "부서가 성공적으로 삭제되었습니다."

# 기존 delete 함수들은 유지 (하위 호환성)
def delete_department(db: Session, department_id: int):
    """부서 삭제 (기존 함수 - 하위 호환성 유지)"""
    db_department = get_department(db, department_id)
    if db_department:
        db.delete(db_department)
        db.commit()
    return db_department


# User CRUD
def create_user(db: Session, user: schemas.UserCreate):
    """사용자 생성"""
    hashed_password = hash_password(user.password)
    user_data = user.dict()
    user_data['password'] = hashed_password
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    """사용자 단일 조회"""
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 조회"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """사용자 목록 조회"""
    return db.query(models.User).offset(skip).limit(limit).all()

def get_users_with_filters(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    company_id: str = None,
    department_id: int = None,
    search: str = None,
    role: str = None,
    is_active: bool = None
):
    """필터링 옵션이 있는 사용자 목록 조회"""
    query = db.query(models.User)
    
    if company_id:
        query = query.filter(models.User.company_id == company_id)
    
    if department_id:
        query = query.filter(models.User.department_id == department_id)
    
    if search:
        query = query.filter(
            (models.User.username.contains(search)) |
            (models.User.email.contains(search)) |
            (models.User.full_name.contains(search))
        )
    
    if role:
        query = query.filter(models.User.role == role)
    
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

def get_mentors(db: Session, skip: int = 0, limit: int = 100):
    """멘토 목록 조회"""
    return db.query(models.User).filter(models.User.role == "mentor").offset(skip).limit(limit).all()

def get_mentees(db: Session, skip: int = 0, limit: int = 100):
    """멘티 목록 조회"""
    return db.query(models.User).filter(models.User.role == "mentee").offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user_update: schemas.UserCreate):
    """사용자 정보 업데이트"""
    db_user = get_user(db, user_id)
    if db_user:
        user_data = user_update.dict()
        if 'password' in user_data:
            user_data['password'] = hash_password(user_data['password'])
        for key, value in user_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

# User CRUD - 수정된 함수들
def get_user_by_company_department(db: Session, user_id: int, company_id: str, department_id: int):
    """회사, 부서별 사용자 조회 (검증용)"""
    return db.query(models.User).filter(
        and_(
            models.User.user_id == user_id,
            models.User.company_id == company_id,
            models.User.department_id == department_id
        )
    ).first()

def delete_user_with_company_department(db: Session, user_id: int, company_id: str, department_id: int):
    """회사, 부서 정보를 검증하여 사용자 삭제"""
    # 1. 회사 존재 확인
    company = get_company(db, company_id)
    if not company:
        return None, "회사를 찾을 수 없습니다."
    
    # 2. 부서 존재 확인
    department = get_department_by_company(db, department_id, company_id)
    if not department:
        return None, "해당 회사의 부서를 찾을 수 없습니다."
    
    # 3. 해당 회사/부서의 사용자인지 확인
    db_user = get_user_by_company_department(db, user_id, company_id, department_id)
    if not db_user:
        return None, "해당 회사/부서의 사용자를 찾을 수 없습니다."
    
    # 4. 멘토링 관계 확인
    mentorship_as_mentor = db.query(models.Mentorship).filter(
        models.Mentorship.mentor_id == user_id
    ).first()
    mentorship_as_mentee = db.query(models.Mentorship).filter(
        models.Mentorship.mentee_id == user_id
    ).first()
    
    if mentorship_as_mentor or mentorship_as_mentee:
        return None, "멘토링 관계가 있는 사용자는 삭제할 수 없습니다."
    
    # 5. 멘토십을 통한 할당된 태스크 확인
    assigned_tasks = db.query(models.TaskAssign).join(models.Mentorship).filter(
        or_(
            models.Mentorship.mentor_id == user_id,
            models.Mentorship.mentee_id == user_id
        )
    ).first()
    if assigned_tasks:
        return None, "할당된 태스크가 있는 사용자는 삭제할 수 없습니다."
    
    # 6. 삭제 실행
    db.delete(db_user)
    db.commit()
    return db_user, "사용자가 성공적으로 삭제되었습니다."

# 기존 delete 함수들은 유지 (하위 호환성)
def delete_user(db: Session, user_id: int):
    """사용자 삭제 (관련 ChatSession/ChatMessage도 함께 삭제)"""
    # 1. 사용자 조회
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    # 2. 관련 ChatMessage 삭제
    db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id.in_(
            db.query(models.ChatSession.session_id).filter(models.ChatSession.user_id == user_id)
        )
    ).delete(synchronize_session=False)

    # 3. 관련 ChatSession 삭제
    db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id).delete(synchronize_session=False)

    # 4. 사용자 삭제
    db.delete(db_user)
    db.commit()
    return db_user


def delete_mentorship(db: Session, mentorship_id: int):
    """멘토쉽 삭제"""
    db_mentorship = get_mentorship(db, mentorship_id)
    if db_mentorship:
        db.delete(db_mentorship)
        db.commit()
    return db_mentorship


# TaskManage CRUD
def create_task_manage(db: Session, task: schemas.TaskManageCreate):
    """태스크 관리 생성"""
    db_task = models.TaskManage(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task_manage(db: Session, task_id: int):
    """태스크 관리 단일 조회"""
    return db.query(models.TaskManage).filter(models.TaskManage.task_manage_id == task_id).first()

def get_task_manages(db: Session, skip: int = 0, limit: int = 100):
    """태스크 관리 목록 조회"""
    return db.query(models.TaskManage).offset(skip).limit(limit).all()

def get_task_manages_by_curriculum(db: Session, curriculum_id: int):
    """커리큘럼별 태스크 관리 조회"""
    return db.query(models.TaskManage).filter(models.TaskManage.curriculum_id == curriculum_id).all()

def update_task_manage(db: Session, task_id: int, task_update: schemas.TaskManageCreate):
    """태스크 관리 정보 업데이트"""
    db_task = get_task_manage(db, task_id)
    if db_task:
        for key, value in task_update.dict().items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task_manage(db: Session, task_id: int):
    """태스크 관리 삭제"""
    db_task = get_task_manage(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task


# TaskAssign CRUD
def create_task_assign(db: Session, task):
    """태스크 할당 생성 - dict 또는 TaskAssignCreate 스키마 모두 지원"""
    if isinstance(task, dict):
        db_task = models.TaskAssign(**task)
    else:
        db_task = models.TaskAssign(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task_assign(db: Session, task_id: int):
    """태스크 할당 단일 조회"""
    return db.query(models.TaskAssign).filter(models.TaskAssign.task_assign_id == task_id).first()

def get_tasks_by_mentorship(db: Session, mentorship_id: int):
    """특정 멘토십의 모든 태스크 조회"""
    return db.query(models.TaskAssign).filter(
        models.TaskAssign.mentorship_id == mentorship_id
    ).all()

def get_task_assigns_filtered(db: Session, mentorship_id: int = None, user_id: int = None, status: str = None, week: int = None, skip: int = 0, limit: int = 100):
    """필터링된 태스크 할당 목록 조회"""
    query = db.query(models.TaskAssign)
    
    if mentorship_id:
        query = query.filter(models.TaskAssign.mentorship_id == mentorship_id)
    
    if user_id:
        # 멘토십을 통해 사용자와 연관된 태스크 조회
        query = query.join(models.Mentorship).filter(
            or_(
                models.Mentorship.mentor_id == user_id,
                models.Mentorship.mentee_id == user_id
            )
        )
    
    if status:
        query = query.filter(models.TaskAssign.status == status)
    
    if week:
        query = query.filter(models.TaskAssign.week == week)
    
    return query.offset(skip).limit(limit).all()

def get_task_assigns(db: Session, skip: int = 0, limit: int = 100):
    """태스크 할당 목록 조회"""
    return db.query(models.TaskAssign).offset(skip).limit(limit).all()

def get_task_assigns_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """사용자별 태스크 할당 목록 조회 (멘토십을 통해)"""
    return db.query(models.TaskAssign).join(models.Mentorship).filter(
        or_(
            models.Mentorship.mentor_id == user_id,
            models.Mentorship.mentee_id == user_id
        )
    ).offset(skip).limit(limit).all()

def get_task_assigns_by_mentorship(db: Session, mentorship_id: int, skip: int = 0, limit: int = 100):
    """멘토십별 태스크 할당 목록 조회"""
    return db.query(models.TaskAssign).filter(
        models.TaskAssign.mentorship_id == mentorship_id
    ).offset(skip).limit(limit).all()

def update_task_assign(db: Session, task_id: int, task_update: schemas.TaskAssignCreate):
    """태스크 할당 정보 업데이트"""
    db_task = get_task_assign(db, task_id)
    if db_task:
        for key, value in task_update.dict().items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task_assign(db: Session, task_id: int):
    """태스크 할당 삭제"""
    db_task = get_task_assign(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task


# Mentorship CRUD
def create_mentorship(db: Session, mentorship: schemas.MentorshipCreate):
    """멘토링 생성"""
    db_mentorship = models.Mentorship(**mentorship.dict())
    db.add(db_mentorship)
    db.commit()
    db.refresh(db_mentorship)
    return db_mentorship

def get_mentorship(db: Session, mentorship_id: int):
    """멘토링 단일 조회"""
    return db.query(models.Mentorship).filter(models.Mentorship.mentorship_id == mentorship_id).first()

def get_mentorships_with_filters(
    db: Session, 
    mentor_id: int = None,
    mentee_id: int = None,
    search: str = None,
    skip: int = 0, 
    limit: int = 100
):
    """멘토십 목록 조회 (필터링 및 검색 지원)"""
    query = db.query(models.Mentorship)
    
    # 멘토 ID 필터
    if mentor_id:
        query = query.filter(models.Mentorship.mentor_id == mentor_id)
    
    # 멘티 ID 필터
    if mentee_id:
        query = query.filter(models.Mentorship.mentee_id == mentee_id)
    
    # 검색 기능 (멘티 이름 또는 커리큘럼 제목으로 검색)
    if search:
        # 멘티 정보와 조인하여 검색 - Django 모델 구조에 맞게 수정
        query = query.join(models.User, models.Mentorship.mentee_id == models.User.user_id)
        
        # 멘티 이름 또는 커리큘럼 제목으로 검색 - Django 모델 필드명 사용
        search_filter = (
            models.User.first_name.ilike(f"%{search}%") |
            models.User.last_name.ilike(f"%{search}%") |
            models.Mentorship.curriculum_title.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    return query.offset(skip).limit(limit).all()

def get_mentorships(db: Session, skip: int = 0, limit: int = 100):
    """멘토링 목록 조회"""
    return db.query(models.Mentorship).offset(skip).limit(limit).all()

def get_mentorships_by_mentor(db: Session, mentor_id: int):
    """멘토별 멘토링 목록 조회"""
    return db.query(models.Mentorship).filter(models.Mentorship.mentor_id == mentor_id).all()

def get_mentorships_by_mentee(db: Session, mentee_id: int):
    """멘티별 멘토링 목록 조회"""
    return db.query(models.Mentorship).filter(models.Mentorship.mentee_id == mentee_id).all()

def delete_mentorship(db: Session, mentorship_id: int):
    """멘토링 삭제"""
    db_mentorship = get_mentorship(db, mentorship_id)
    if db_mentorship:
        db.delete(db_mentorship)
        db.commit()
    return db_mentorship


# Curriculum CRUD
def create_curriculum(db: Session, curriculum: schemas.CurriculumCreate):
    """커리큘럼 생성"""
    db_curriculum = models.Curriculum(**curriculum.dict())
    db.add(db_curriculum)
    db.commit()
    db.refresh(db_curriculum)
    return db_curriculum

def get_curriculum(db: Session, curriculum_id: int):
    """커리큘럼 단일 조회"""
    return db.query(models.Curriculum).filter(models.Curriculum.curriculum_id == curriculum_id).first()

def get_curricula(db: Session, skip: int = 0, limit: int = 100):
    """커리큘럼 목록 조회"""
    return db.query(models.Curriculum).offset(skip).limit(limit).all()

def get_curricula_by_department(db: Session, department_id: int):
    """부서별 커리큘럼 조회"""
    return db.query(models.Curriculum).filter(models.Curriculum.department_id == department_id).all()

def get_common_curricula(db: Session):
    """공용 커리큘럼 조회"""
    return db.query(models.Curriculum).filter(models.Curriculum.common == True).all()

def get_filtered_curricula(db: Session, department_id: Optional[int] = None):
    """공통 커리큘럼 + 특정 부서 커리큘럼 조회"""
    query = db.query(models.Curriculum)
    
    if department_id is not None:
        # 공통 커리큘럼 또는 특정 부서 커리큘럼
        query = query.filter(
            or_(
                models.Curriculum.common == True,
                models.Curriculum.department_id == department_id
            )
        )
    else:
        # 부서가 지정되지 않은 경우 공통 커리큘럼만
        query = query.filter(models.Curriculum.common == True)
    
    return query.all()

def update_curriculum(db: Session, curriculum_id: int, curriculum_update: schemas.CurriculumCreate):
    """커리큘럼 정보 업데이트"""
    db_curriculum = get_curriculum(db, curriculum_id)
    if db_curriculum:
        for key, value in curriculum_update.dict().items():
            setattr(db_curriculum, key, value)
        db.commit()
        db.refresh(db_curriculum)
    return db_curriculum

def delete_curriculum(db: Session, curriculum_id: int):
    """커리큘럼 삭제"""
    db_curriculum = get_curriculum(db, curriculum_id)
    if db_curriculum:
        db.delete(db_curriculum)
        db.commit()
    return db_curriculum


# Mentorship 추가 CRUD
def get_mentorships_by_mentor(db: Session, mentor_id: int):
    """멘토별 멘토십 조회"""
    return db.query(models.Mentorship).filter(models.Mentorship.mentor_id == mentor_id).all()

def get_mentorships_by_mentee(db: Session, mentee_id: int):
    """멘티별 멘토십 조회"""
    return db.query(models.Mentorship).filter(models.Mentorship.mentee_id == mentee_id).all()

def update_mentorship_status(db: Session, mentorship_id: int, is_active: bool):
    """멘토십 활성화 상태 업데이트"""
    db_mentorship = get_mentorship(db, mentorship_id)
    if db_mentorship:
        db_mentorship.is_active = is_active
        db.commit()
        db.refresh(db_mentorship)
    return db_mentorship


def update_mentorship(db: Session, mentorship_id: int, mentorship_update: schemas.MentorshipCreate):
    """멘토십 정보 업데이트"""
    db_mentorship = get_mentorship(db, mentorship_id)
    if db_mentorship:
        for key, value in mentorship_update.dict().items():
            setattr(db_mentorship, key, value)
        db.commit()
        db.refresh(db_mentorship)
    return db_mentorship


# Memo CRUD
def create_memo(db: Session, memo: schemas.MemoCreate):
    """메모 생성"""
    try:
        db_memo = models.Memo(**memo.dict())
        db.add(db_memo)
        db.commit()
        db.refresh(db_memo)
        return db_memo
    except Exception as e:
        db.rollback()
        raise e

def get_memo(db: Session, memo_id: int):
    """메모 단일 조회 - 사용자 정보 포함"""
    try:
        return db.query(models.Memo).join(models.User).filter(
            models.Memo.memo_id == memo_id
        ).first()
    except Exception as e:
        raise e

def get_memos(db: Session, skip: int = 0, limit: int = 100):
    """메모 목록 조회 - 사용자 정보 포함"""
    try:
        return db.query(models.Memo).join(models.User).offset(skip).limit(limit).all()
    except Exception as e:
        raise e

def get_memos_by_task(db: Session, task_assign_id: int):
    """과제별 메모 조회 - 사용자 정보 포함"""
    try:
        return db.query(models.Memo).join(models.User).filter(
            models.Memo.task_assign_id == task_assign_id
        ).all()
    except Exception as e:
        raise e

def get_memos_by_user(db: Session, user_id: int):
    """사용자별 메모 조회 - 사용자 정보 포함"""
    try:
        return db.query(models.Memo).join(models.User).filter(
            models.Memo.user_id == user_id
        ).all()
    except Exception as e:
        raise e

def update_memo(db: Session, memo_id: int, memo_update: schemas.MemoCreate):
    """메모 정보 업데이트"""
    try:
        db_memo = get_memo(db, memo_id)
        if db_memo:
            for key, value in memo_update.dict().items():
                setattr(db_memo, key, value)
            db.commit()
            db.refresh(db_memo)
        return db_memo
    except Exception as e:
        db.rollback()
        raise e

def delete_memo(db: Session, memo_id: int):
    """메모 삭제"""
    try:
        db_memo = get_memo(db, memo_id)
        if db_memo:
            db.delete(db_memo)
            db.commit()
        return db_memo
    except Exception as e:
        db.rollback()
        raise e


# Docs CRUD
def create_docs(db: Session, docs: schemas.DocsCreate):
    """문서 생성"""
    from datetime import datetime
    db_docs = models.Docs(
        department_id=docs.department_id,
        title=docs.title,
        description=docs.description,
        file_path=docs.file_path,
        common_doc=docs.common_doc,
        create_time=datetime.now(),
        original_file_name=getattr(docs, 'original_file_name', None)
    )
    db.add(db_docs)
    db.commit()
    db.refresh(db_docs)
    return db_docs

def get_docs(db: Session, docs_id: int):
    """문서 단일 조회"""
    return db.query(models.Docs).filter(models.Docs.docs_id == docs_id).first()

def get_all_docs(db: Session, skip: int = 0, limit: int = 100):
    """문서 목록 조회"""
    return db.query(models.Docs).offset(skip).limit(limit).all()

def get_docs_by_department(db: Session, department_id: int):
    """부서별 문서 조회"""
    return db.query(models.Docs).filter(models.Docs.department_id == department_id).all()

def get_common_docs(db: Session):
    """공용 문서 조회"""
    return db.query(models.Docs).filter(models.Docs.common_doc == True).all()

def update_docs(db: Session, docs_id: int, docs_update: schemas.DocsCreate):
    """문서 정보 업데이트"""
    db_docs = get_docs(db, docs_id)
    if db_docs:
        for key, value in docs_update.dict().items():
            setattr(db_docs, key, value)
        db.commit()
        db.refresh(db_docs)
    return db_docs

def delete_docs(db: Session, docs_id: int):
    """문서 삭제"""
    db_docs = get_docs(db, docs_id)
    if db_docs:
        db.delete(db_docs)
        db.commit()
    return db_docs


# ChatSession CRUD
def create_chat_session(db: Session, chat_session: schemas.ChatSessionCreate):
    """채팅 세션 생성"""
    db_session = models.ChatSession(
        user_id=chat_session.user_id,
        summary=chat_session.summary,
        is_active=True
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_chat_session(db: Session, session_id: int):
    """채팅 세션 단일 조회"""
    return db.query(models.ChatSession).filter(models.ChatSession.session_id == session_id).first()

def get_chat_sessions_by_user(db: Session, user_id: int):
    """사용자별 채팅 세션 조회"""
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id).all()

def update_chat_session(db: Session, session_id: int, session_update: schemas.ChatSessionCreate):
    """채팅 세션 정보 업데이트"""
    db_session = get_chat_session(db, session_id)
    if db_session:
        for key, value in session_update.dict().items():
            setattr(db_session, key, value)
        db.commit()
        db.refresh(db_session)
    return db_session

def delete_chat_session(db: Session, session_id: int):
    """채팅 세션 삭제"""
    db_session = get_chat_session(db, session_id)
    if db_session:
        db.delete(db_session)
        db.commit()
    return db_session


# ChatMessage CRUD
def create_chat_message(db: Session, chat_message: schemas.ChatMessageCreate):
    """채팅 메시지 생성"""
    from datetime import datetime
    db_message = models.ChatMessage(
        session_id=chat_message.session_id,
        message_text=chat_message.message_text,
        message_type=chat_message.message_type,
        create_time=datetime.now().date(),
        is_active=True
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_message(db: Session, message_id: int):
    """채팅 메시지 단일 조회"""
    return db.query(models.ChatMessage).filter(models.ChatMessage.message_id == message_id).first()

def get_chat_messages_by_session(db: Session, session_id: int):
    """세션별 채팅 메시지 조회"""
    return db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.create_time).all()

def delete_chat_message(db: Session, message_id: int):
    """채팅 메시지 삭제"""
    db_message = get_chat_message(db, message_id)
    if db_message:
        db.delete(db_message)
        db.commit()
    return db_message


# Alarm CRUD
def create_alarm(db: Session, alarm: schemas.AlarmCreate):
    """알람 생성"""
    db_alarm = models.Alarm(**alarm.dict())
    db.add(db_alarm)
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def get_alarm(db: Session, alarm_id: int):
    """알람 단일 조회"""
    return db.query(models.Alarm).filter(models.Alarm.id == alarm_id).first()

def get_alarms(db: Session, skip: int = 0, limit: int = 100):
    """알람 목록 조회"""
    return db.query(models.Alarm).offset(skip).limit(limit).all()

def get_alarms_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """사용자별 알람 목록 조회"""
    return db.query(models.Alarm).filter(models.Alarm.user_id == user_id).offset(skip).limit(limit).all()

def get_active_alarms_by_user(db: Session, user_id: int):
    """사용자의 활성 알람 조회"""
    return db.query(models.Alarm).filter(
        and_(
            models.Alarm.user_id == user_id,
            models.Alarm.is_active == True
        )
    ).order_by(models.Alarm.created_at.desc()).all()

def update_alarm(db: Session, alarm_id: int, alarm_update: schemas.AlarmCreate):
    """알람 정보 업데이트"""
    db_alarm = get_alarm(db, alarm_id)
    if db_alarm:
        for key, value in alarm_update.dict().items():
            setattr(db_alarm, key, value)
        db.commit()
        db.refresh(db_alarm)
    return db_alarm

def update_alarm_status(db: Session, alarm_id: int, is_active: bool):
    """알람 활성 상태 업데이트"""
    db_alarm = get_alarm(db, alarm_id)
    if db_alarm:
        db_alarm.is_active = is_active
        db.commit()
        db.refresh(db_alarm)
    return db_alarm

def delete_alarm(db: Session, alarm_id: int):
    """알람 삭제"""
    db_alarm = get_alarm(db, alarm_id)
    if db_alarm:
        db.delete(db_alarm)
        db.commit()
    return db_alarm

def mark_all_alarms_read(db: Session, user_id: int):
    """사용자의 모든 알람을 읽음 처리"""
    db.query(models.Alarm).filter(
        and_(
            models.Alarm.user_id == user_id,
            models.Alarm.is_active == True
        )
    ).update({"is_active": False})
    db.commit()
    return True


# RAG/Chat 추가 CRUD Functions
def get_user_by_id(db: Session, user_id: int):
    """사용자 ID로 사용자 조회"""
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_department_by_id(db: Session, department_id: int):
    """부서 ID로 부서 조회"""
    return db.query(models.Department).filter(models.Department.department_id == department_id).first()

def get_user_chat_sessions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """사용자의 채팅 세션 목록 조회 (활성 세션만)"""
    return db.query(models.ChatSession).filter(
        and_(
            models.ChatSession.user_id == user_id,
            models.ChatSession.is_active == True
        )
    ).order_by(models.ChatSession.session_id.desc()).offset(skip).limit(limit).all()

def get_chat_messages(db: Session, session_id: int, skip: int = 0, limit: int = 100):
    """채팅 세션의 메시지 목록 조회 (활성 메시지만)"""
    return db.query(models.ChatMessage).filter(
        and_(
            models.ChatMessage.session_id == session_id,
            models.ChatMessage.is_active == True
        )
    ).order_by(models.ChatMessage.create_time.asc()).offset(skip).limit(limit).all()

def create_document(db: Session, department_id: int, title: str, description: str, file_path: str, common_doc: bool = False, original_file_name: str = None):
    """문서 생성"""
    from datetime import datetime
    db_doc = models.Docs(
        department_id=department_id,
        title=title,
        description=description,
        file_path=file_path,
        common_doc=common_doc,
        create_time=datetime.now(),
        original_file_name=original_file_name
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def get_document(db: Session, docs_id: int):
    """문서 조회"""
    return db.query(models.Docs).filter(models.Docs.docs_id == docs_id).first()

def get_department_documents(db: Session, department_id: int, include_common: bool = True):
    """부서별 문서 목록 조회"""
    query = db.query(models.Docs)
    if include_common:
        query = query.filter(
            or_(
                models.Docs.department_id == department_id,
                models.Docs.common_doc == True
            )
        )
    else:
        query = query.filter(models.Docs.department_id == department_id)
    
    return query.all()

def update_document(db: Session, docs_id: int, **kwargs):
    """문서 정보 업데이트"""
    db_doc = get_document(db, docs_id)
    if db_doc:
        for key, value in kwargs.items():
            if hasattr(db_doc, key):
                setattr(db_doc, key, value)
        db.commit()
        db.refresh(db_doc)
    return db_doc

def delete_document(db: Session, docs_id: int):
    """문서 삭제"""
    db_doc = get_document(db, docs_id)
    if db_doc:
        db.delete(db_doc)
        db.commit()
    return db_doc