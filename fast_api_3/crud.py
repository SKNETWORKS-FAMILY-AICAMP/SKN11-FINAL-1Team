from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from passlib.context import CryptContext
from datetime import datetime, date
import models
import schemas

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Company CRUD
def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(
        company_id=company.company_id,
        company_name=company.company_name
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_company(db: Session, company_id: str):
    return db.query(models.Company).filter(models.Company.company_id == company_id).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()

def update_company(db: Session, company_id: str, company: schemas.CompanyUpdate):
    db_company = db.query(models.Company).filter(models.Company.company_id == company_id).first()
    if db_company:
        update_data = company.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_company, key, value)
        db.commit()
        db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: str):
    db_company = db.query(models.Company).filter(models.Company.company_id == company_id).first()
    if db_company:
        db.delete(db_company)
        db.commit()
    return db_company

# Department CRUD
def create_department(db: Session, department: schemas.DepartmentCreate):
    db_department = models.Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def get_department(db: Session, department_id: int):
    return db.query(models.Department).filter(models.Department.department_id == department_id).first()

def get_departments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Department).offset(skip).limit(limit).all()

def get_departments_by_company(db: Session, company_id: str):
    return db.query(models.Department).filter(models.Department.company_id == company_id).all()

def update_department(db: Session, department_id: int, department: schemas.DepartmentUpdate):
    db_department = db.query(models.Department).filter(models.Department.department_id == department_id).first()
    if db_department:
        update_data = department.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_department, key, value)
        db.commit()
        db.refresh(db_department)
    return db_department

def delete_department(db: Session, department_id: int):
    db_department = db.query(models.Department).filter(models.Department.department_id == department_id).first()
    if db_department:
        db.delete(db_department)
        db.commit()
    return db_department

# User CRUD
def create_user(db: Session, user: schemas.UserCreate):
    user_dict = user.dict()
    user_dict['password'] = hash_password(user_dict.pop('password'))
    db_user = models.User(**user_dict)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_employee_number(db: Session, employee_number: int):
    return db.query(models.User).filter(models.User.employee_number == employee_number).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_users_by_company(db: Session, company_id: str):
    return db.query(models.User).filter(models.User.company_id == company_id).all()

def get_users_by_department(db: Session, department_id: int):
    return db.query(models.User).filter(models.User.department_id == department_id).all()

def get_users_by_role(db: Session, role: str):
    return db.query(models.User).filter(models.User.role == role).all()

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user:
        update_data = user.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# Curriculum CRUD
def create_curriculum(db: Session, curriculum: schemas.CurriculumCreate):
    db_curriculum = models.Curriculum(**curriculum.dict())
    db.add(db_curriculum)
    db.commit()
    db.refresh(db_curriculum)
    return db_curriculum

def get_curriculum(db: Session, curriculum_id: int):
    return db.query(models.Curriculum).filter(models.Curriculum.curriculum_id_id == curriculum_id).first()

def get_curriculums(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Curriculum).offset(skip).limit(limit).all()

def get_curriculums_by_department(db: Session, department_id: int):
    return db.query(models.Curriculum).filter(models.Curriculum.department_id == department_id).all()

def update_curriculum(db: Session, curriculum_id: int, curriculum: schemas.CurriculumUpdate):
    db_curriculum = db.query(models.Curriculum).filter(models.Curriculum.curriculum_id_id == curriculum_id).first()
    if db_curriculum:
        update_data = curriculum.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_curriculum, key, value)
        db.commit()
        db.refresh(db_curriculum)
    return db_curriculum

def delete_curriculum(db: Session, curriculum_id: int):
    db_curriculum = db.query(models.Curriculum).filter(models.Curriculum.curriculum_id_id == curriculum_id).first()
    if db_curriculum:
        db.delete(db_curriculum)
        db.commit()
    return db_curriculum

# TaskManage CRUD
def create_task_manage(db: Session, task_manage: schemas.TaskManageCreate):
    db_task_manage = models.TaskManage(**task_manage.dict())
    db.add(db_task_manage)
    db.commit()
    db.refresh(db_task_manage)
    return db_task_manage

def get_task_manage(db: Session, task_manage_id: int):
    return db.query(models.TaskManage).filter(models.TaskManage.task_manage_id == task_manage_id).first()

def get_task_manages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TaskManage).offset(skip).limit(limit).all()

def get_task_manages_by_curriculum(db: Session, curriculum_id: int):
    return db.query(models.TaskManage).filter(models.TaskManage.curriculum_id_id == curriculum_id).all()

def get_task_manages_by_week(db: Session, week: int):
    return db.query(models.TaskManage).filter(models.TaskManage.week == week).all()

def update_task_manage(db: Session, task_manage_id: int, task_manage: schemas.TaskManageUpdate):
    db_task_manage = db.query(models.TaskManage).filter(models.TaskManage.task_manage_id == task_manage_id).first()
    if db_task_manage:
        update_data = task_manage.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task_manage, key, value)
        db.commit()
        db.refresh(db_task_manage)
    return db_task_manage

def delete_task_manage(db: Session, task_manage_id: int):
    db_task_manage = db.query(models.TaskManage).filter(models.TaskManage.task_manage_id == task_manage_id).first()
    if db_task_manage:
        db.delete(db_task_manage)
        db.commit()
    return db_task_manage

# TaskAssign CRUD
def create_task_assign(db: Session, task_assign: schemas.TaskAssignCreate):
    db_task_assign = models.TaskAssign(**task_assign.dict())
    db.add(db_task_assign)
    db.commit()
    db.refresh(db_task_assign)
    return db_task_assign

def get_task_assign(db: Session, task_assign_id: int):
    return db.query(models.TaskAssign).filter(models.TaskAssign.task_assign_id == task_assign_id).first()

def get_task_assigns(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TaskAssign).offset(skip).limit(limit).all()

def get_task_assigns_by_user(db: Session, user_id: int):
    return db.query(models.TaskAssign).filter(models.TaskAssign.user_id == user_id).all()

def get_task_assigns_by_mentorship(db: Session, mentorship_id: int):
    return db.query(models.TaskAssign).filter(models.TaskAssign.mentorship_id == mentorship_id).all()

def get_task_assigns_by_status(db: Session, status: int):
    return db.query(models.TaskAssign).filter(models.TaskAssign.status == status).all()

def update_task_assign(db: Session, task_assign_id: int, task_assign: schemas.TaskAssignUpdate):
    db_task_assign = db.query(models.TaskAssign).filter(models.TaskAssign.task_assign_id == task_assign_id).first()
    if db_task_assign:
        update_data = task_assign.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task_assign, key, value)
        db.commit()
        db.refresh(db_task_assign)
    return db_task_assign

def delete_task_assign(db: Session, task_assign_id: int):
    db_task_assign = db.query(models.TaskAssign).filter(models.TaskAssign.task_assign_id == task_assign_id).first()
    if db_task_assign:
        db.delete(db_task_assign)
        db.commit()
    return db_task_assign

# Mentorship CRUD
def create_mentorship(db: Session, mentorship: schemas.MentorshipCreate):
    db_mentorship = models.Mentorship(**mentorship.dict())
    db.add(db_mentorship)
    db.commit()
    db.refresh(db_mentorship)
    return db_mentorship

def get_mentorship(db: Session, mentorship_id: int):
    return db.query(models.Mentorship).filter(models.Mentorship.mentorship_id == mentorship_id).first()

def get_mentorships(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Mentorship).offset(skip).limit(limit).all()

def get_mentorships_by_mentor(db: Session, mentor_id: int):
    return db.query(models.Mentorship).filter(models.Mentorship.mentor_id == mentor_id).all()

def get_mentorships_by_mentee(db: Session, mentee_id: int):
    return db.query(models.Mentorship).filter(models.Mentorship.mentee_id == mentee_id).all()

def update_mentorship(db: Session, mentorship_id: int, mentorship: schemas.MentorshipUpdate):
    db_mentorship = db.query(models.Mentorship).filter(models.Mentorship.mentorship_id == mentorship_id).first()
    if db_mentorship:
        update_data = mentorship.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_mentorship, key, value)
        db.commit()
        db.refresh(db_mentorship)
    return db_mentorship

def delete_mentorship(db: Session, mentorship_id: int):
    db_mentorship = db.query(models.Mentorship).filter(models.Mentorship.mentorship_id == mentorship_id).first()
    if db_mentorship:
        db.delete(db_mentorship)
        db.commit()
    return db_mentorship 