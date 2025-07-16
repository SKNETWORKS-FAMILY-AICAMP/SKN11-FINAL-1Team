from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Department, User, Company
from app.schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    DepartmentWithRelations, DepartmentList, DepartmentStats
)
from app.dependencies import get_current_user, require_admin
from sqlalchemy import func

router = APIRouter(prefix="/departments", tags=["departments"])

@router.post("/", response_model=DepartmentResponse)
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """부서 생성"""
    # 회사 존재 확인
    company = db.query(Company).filter(Company.company_id == department.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    
    # 같은 회사 내에서 부서명 중복 확인
    existing_dept = db.query(Department).filter(
        Department.department_name == department.department_name,
        Department.company_id == department.company_id,
        Department.is_active == True
    ).first()
    
    if existing_dept:
        raise HTTPException(status_code=400, detail="이미 존재하는 부서명입니다.")
    
    # 비활성화된 부서가 있으면 되살리기
    inactive_dept = db.query(Department).filter(
        Department.department_name == department.department_name,
        Department.company_id == department.company_id,
        Department.is_active == False
    ).first()
    
    if inactive_dept:
        inactive_dept.is_active = True
        inactive_dept.description = department.description
        db.commit()
        db.refresh(inactive_dept)
        return inactive_dept
    
    # 새로운 부서 생성
    db_department = Department(**department.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

@router.get("/", response_model=DepartmentList)
def get_departments(
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """부서 목록 조회"""
    query = db.query(Department)
    
    # 관리자가 아닌 경우 자신의 회사만 조회
    if not current_user.is_admin:
        query = query.filter(Department.company_id == current_user.company_id)
    elif company_id:
        query = query.filter(Department.company_id == company_id)
    
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    
    if search:
        query = query.filter(Department.department_name.contains(search))
    
    total = query.count()
    departments = query.offset(skip).limit(limit).all()
    
    return DepartmentList(
        departments=departments,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/{department_id}", response_model=DepartmentWithRelations)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """부서 상세 조회"""
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    
    # 권한 확인
    if not current_user.is_admin and department.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return department

@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """부서 수정"""
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    
    # 부서명 변경 시 중복 확인
    if department_update.department_name and department_update.department_name != department.department_name:
        existing = db.query(Department).filter(
            Department.department_name == department_update.department_name,
            Department.company_id == department.company_id,
            Department.department_id != department_id,
            Department.is_active == True
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 부서명입니다.")
    
    # 업데이트
    for field, value in department_update.dict(exclude_unset=True).items():
        setattr(department, field, value)
    
    db.commit()
    db.refresh(department)
    return department

@router.delete("/{department_id}")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """부서 삭제"""
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    
    # 부서에 사용자가 있는지 확인
    users_count = db.query(User).filter(User.department_id == department_id).count()
    if users_count > 0:
        raise HTTPException(status_code=400, detail="부서에 사용자가 있어 삭제할 수 없습니다.")
    
    db.delete(department)
    db.commit()
    return {"message": "부서가 삭제되었습니다."}

@router.get("/{department_id}/users", response_model=List[dict])
def get_department_users(
    department_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """부서 소속 사용자 목록"""
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    
    # 권한 확인
    if not current_user.is_admin and department.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    users = db.query(User).filter(User.department_id == department_id).offset(skip).limit(limit).all()
    return users

@router.get("/{department_id}/stats", response_model=DepartmentStats)
def get_department_stats(
    department_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """부서 통계"""
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    
    # 권한 확인
    if not current_user.is_admin and department.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    # 통계 계산
    total_users = db.query(User).filter(User.department_id == department_id).count()
    total_docs = db.query(func.count()).select_from(department.docs).scalar() or 0
    total_curriculums = db.query(func.count()).select_from(department.curriculums).scalar() or 0
    
    return DepartmentStats(
        total_departments=1,
        active_departments=1 if department.is_active else 0,
        total_users=total_users,
        total_docs=total_docs,
        total_curriculums=total_curriculums
    )
