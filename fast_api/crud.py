from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import models
import schemas
from passlib.context import CryptContext

# 비밀번호 암호화 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """비밀번호 해시화"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# Company CRUD
def create_company(db: Session, company: schemas.CompanyCreate):
    """회사 생성"""
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_company(db: Session, company_id: int):
    """회사 단일 조회"""
    return db.query(models.Company).filter(models.Company.company_id == company_id).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    """회사 목록 조회"""
    return db.query(models.Company).offset(skip).limit(limit).all()

def update_company(db: Session, company_id: int, company_update: schemas.CompanyCreate):
    """회사 정보 업데이트"""
    db_company = get_company(db, company_id)
    if db_company:
        for key, value in company_update.dict().items():
            setattr(db_company, key, value)
        db.commit()
        db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: int):
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

def update_department(db: Session, department_id: int, department_update: schemas.DepartmentCreate):
    """부서 정보 업데이트"""
    db_department = get_department(db, department_id)
    if db_department:
        for key, value in department_update.dict().items():
            setattr(db_department, key, value)
        db.commit()
        db.refresh(db_department)
    return db_department

# Department CRUD - 수정된 함수들
def get_department_by_company(db: Session, department_id: int, company_id: int):
    """회사별 부서 조회 (검증용)"""
    return db.query(models.Department).filter(
        and_(
            models.Department.department_id == department_id,
            models.Department.company_id == company_id
        )
    ).first()

def delete_department_with_company(db: Session, department_id: int, company_id: int):
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
def get_user_by_company_department(db: Session, user_id: int, company_id: int, department_id: int):
    """회사, 부서별 사용자 조회 (검증용)"""
    return db.query(models.User).filter(
        and_(
            models.User.user_id == user_id,
            models.User.company_id == company_id,
            models.User.department_id == department_id
        )
    ).first()

def delete_user_with_company_department(db: Session, user_id: int, company_id: int, department_id: int):
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
    
    # 5. 할당된 태스크 확인
    assigned_tasks = db.query(models.TaskAssign).filter(
        models.TaskAssign.user_id == user_id
    ).first()
    if assigned_tasks:
        return None, "할당된 태스크가 있는 사용자는 삭제할 수 없습니다."
    
    # 6. 삭제 실행
    db.delete(db_user)
    db.commit()
    return db_user, "사용자가 성공적으로 삭제되었습니다."

# 기존 delete 함수들은 유지 (하위 호환성)
def delete_user(db: Session, user_id: int):
    """사용자 삭제 (기존 함수 - 하위 호환성 유지)"""
    db_user = get_user(db, user_id)
    if db_user:
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


# Template CRUD
def create_template(db: Session, template: schemas.TemplateCreate):
    """템플릿 생성"""
    db_template = models.Template(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_template(db: Session, template_id: int):
    """템플릿 단일 조회"""
    return db.query(models.Template).filter(models.Template.template_id == template_id).first()

def get_templates(db: Session, skip: int = 0, limit: int = 100):
    """템플릿 목록 조회"""
    return db.query(models.Template).offset(skip).limit(limit).all()

def update_template(db: Session, template_id: int, template_update: schemas.TemplateCreate):
    """템플릿 정보 업데이트"""
    db_template = get_template(db, template_id)
    if db_template:
        for key, value in template_update.dict().items():
            setattr(db_template, key, value)
        db.commit()
        db.refresh(db_template)
    return db_template

def delete_template(db: Session, template_id: int):
    """템플릿 삭제"""
    db_template = get_template(db, template_id)
    if db_template:
        db.delete(db_template)
        db.commit()
    return db_template


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
def create_task_assign(db: Session, task: schemas.TaskAssignCreate):
    """태스크 할당 생성"""
    db_task = models.TaskAssign(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task_assign(db: Session, task_id: int):
    """태스크 할당 단일 조회"""
    return db.query(models.TaskAssign).filter(models.TaskAssign.task_assign_id == task_id).first()

def get_task_assigns(db: Session, skip: int = 0, limit: int = 100):
    """태스크 할당 목록 조회"""
    return db.query(models.TaskAssign).offset(skip).limit(limit).all()

def get_task_assigns_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """사용자별 태스크 할당 목록 조회"""
    return db.query(models.TaskAssign).filter(models.TaskAssign.user_id == user_id).offset(skip).limit(limit).all()

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