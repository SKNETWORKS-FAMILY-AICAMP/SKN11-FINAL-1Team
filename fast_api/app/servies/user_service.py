from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import User, Company, Department
from app.schemas.user import UserCreate, UserUpdate
from app.servies.auth_service import AuthService

class UserService:
    def __init__(self):
        self.auth_service = AuthService()

    def create_user(self, db: Session, user: UserCreate) -> User:
        """사용자 생성"""
        # 이메일 중복 확인
        if self.get_user_by_email(db, user.email):
            raise ValueError("이미 존재하는 이메일입니다.")
        
        # 사번 중복 확인
        if user.employee_number and self.get_user_by_employee_number(db, user.employee_number):
            raise ValueError("이미 존재하는 사번입니다.")
        
        # 회사 존재 확인
        if user.company_id:
            company = db.query(Company).filter(Company.company_id == user.company_id).first()
            if not company:
                raise ValueError("존재하지 않는 회사입니다.")
        
        # 부서 존재 확인
        if user.department_id:
            department = db.query(Department).filter(Department.department_id == user.department_id).first()
            if not department:
                raise ValueError("존재하지 않는 부서입니다.")
        
        # 사용자 생성
        user_data = user.dict()
        password = user_data.pop("password")
        
        db_user = User(**user_data)
        db_user.set_password(password)
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        """사용자 조회"""
        return db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()

    def get_user_by_employee_number(self, db: Session, employee_number: int) -> Optional[User]:
        """사번으로 사용자 조회"""
        return db.query(User).filter(User.employee_number == employee_number).first()

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """사용자 목록 조회"""
        return db.query(User).offset(skip).limit(limit).all()

    def get_users_by_company(self, db: Session, company_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """회사별 사용자 목록 조회"""
        return db.query(User).filter(User.company_id == company_id).offset(skip).limit(limit).all()

    def get_users_by_department(self, db: Session, department_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """부서별 사용자 목록 조회"""
        return db.query(User).filter(User.department_id == department_id).offset(skip).limit(limit).all()

    def get_users_by_role(self, db: Session, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """역할별 사용자 목록 조회"""
        return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()

    def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """사용자 수정"""
        user = self.get_user(db, user_id)
        if not user:
            return None
        
        # 업데이트할 필드들 검증
        update_data = user_update.dict(exclude_unset=True)
        
        # 사번 중복 확인
        if "employee_number" in update_data and update_data["employee_number"] != user.employee_number:
            if self.get_user_by_employee_number(db, update_data["employee_number"]):
                raise ValueError("이미 존재하는 사번입니다.")
        
        # 부서 존재 확인
        if "department_id" in update_data and update_data["department_id"]:
            department = db.query(Department).filter(Department.department_id == update_data["department_id"]).first()
            if not department:
                raise ValueError("존재하지 않는 부서입니다.")
        
        # 필드 업데이트
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: int) -> bool:
        """사용자 삭제"""
        user = self.get_user(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True

    def activate_user(self, db: Session, user_id: int) -> Optional[User]:
        """사용자 활성화"""
        user = self.get_user(db, user_id)
        if not user:
            return None
        
        user.is_active = True
        db.commit()
        db.refresh(user)
        return user

    def deactivate_user(self, db: Session, user_id: int) -> Optional[User]:
        """사용자 비활성화"""
        user = self.get_user(db, user_id)
        if not user:
            return None
        
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user

    def change_password(self, db: Session, user_id: int, new_password: str) -> bool:
        """비밀번호 변경"""
        user = self.get_user(db, user_id)
        if not user:
            return False
        
        return self.auth_service.change_password(db, user, new_password)

    def reset_password(self, db: Session, user_id: int) -> bool:
        """비밀번호 초기화 (기본값: 123)"""
        user = self.get_user(db, user_id)
        if not user:
            return False
        
        return self.auth_service.reset_password(db, user)

    def search_users(self, db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """사용자 검색"""
        return db.query(User).filter(
            (User.first_name.contains(search_term)) |
            (User.last_name.contains(search_term)) |
            (User.email.contains(search_term))
        ).offset(skip).limit(limit).all()

    def get_user_stats(self, db: Session, company_id: Optional[str] = None) -> dict:
        """사용자 통계"""
        query = db.query(User)
        
        if company_id:
            query = query.filter(User.company_id == company_id)
        
        total_users = query.count()
        active_users = query.filter(User.is_active == True).count()
        inactive_users = total_users - active_users
        
        total_mentors = query.filter(User.role == "mentor").count()
        total_mentees = query.filter(User.role == "mentee").count()
        total_admins = query.filter(User.is_admin == True).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "total_mentors": total_mentors,
            "total_mentees": total_mentees,
            "total_admins": total_admins
        }