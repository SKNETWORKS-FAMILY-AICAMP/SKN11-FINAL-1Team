from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserList, UserStats, 
    PasswordChange, UserWithRelations
)
from app.servies.user_service import UserService
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()

@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """사용자 생성"""
    try:
        return user_service.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=UserList)
def get_users(
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[str] = None,
    department_id: Optional[int] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용자 목록 조회"""
    # 관리자가 아닌 경우 자신의 회사만 조회
    if not current_user.is_admin:
        company_id = current_user.company_id
    
    # 검색 조건에 따라 사용자 목록 조회
    if search:
        users = user_service.search_users(db, search, skip, limit)
        total = len(users)  # 검색 결과의 총 개수를 정확히 계산하려면 별도 카운트 쿼리 필요
    elif company_id:
        users = user_service.get_users_by_company(db, company_id, skip, limit)
        total = len(users)
    elif department_id:
        users = user_service.get_users_by_department(db, department_id, skip, limit)
        total = len(users)
    elif role:
        users = user_service.get_users_by_role(db, role, skip, limit)
        total = len(users)
    else:
        users = user_service.get_users(db, skip, limit)
        total = len(users)
    
    # 활성/비활성 필터링
    if is_active is not None:
        users = [user for user in users if user.is_active == is_active]
    
    return UserList(
        users=users,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/{user_id}", response_model=UserWithRelations)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용자 상세 조회"""
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 권한 확인 - 관리자가 아닌 경우 자신의 정보만 조회 가능
    if not current_user.is_admin and user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용자 수정"""
    # 권한 확인 - 관리자가 아닌 경우 자신의 정보만 수정 가능
    if not current_user.is_admin and user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    try:
        user = user_service.update_user(db, user_id, user_update)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """사용자 삭제"""
    # 자신을 삭제할 수 없음
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="자신을 삭제할 수 없습니다.")
    
    if not user_service.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return {"message": "사용자가 삭제되었습니다."}

@router.post("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """사용자 활성화"""
    user = user_service.activate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return user

@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """사용자 비활성화"""
    # 자신을 비활성화할 수 없음
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="자신을 비활성화할 수 없습니다.")
    
    user = user_service.deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return user

@router.post("/{user_id}/change-password")
def change_password(
    user_id: int,
    password_change: PasswordChange,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """비밀번호 변경"""
    # 권한 확인 - 관리자가 아닌 경우 자신의 비밀번호만 변경 가능
    if not current_user.is_admin and user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 현재 비밀번호 확인
    if not user.check_password(password_change.current_password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
    
    if not user_service.change_password(db, user_id, password_change.new_password):
        raise HTTPException(status_code=500, detail="비밀번호 변경에 실패했습니다.")
    
    return {"message": "비밀번호가 변경되었습니다."}

@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """비밀번호 초기화"""
    if not user_service.reset_password(db, user_id):
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return {"message": "비밀번호가 초기화되었습니다. (기본값: 123)"}

@router.get("/search/{search_term}", response_model=List[UserResponse])
def search_users(
    search_term: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용자 검색"""
    users = user_service.search_users(db, search_term, skip, limit)
    
    # 관리자가 아닌 경우 같은 회사만 검색
    if not current_user.is_admin:
        users = [user for user in users if user.company_id == current_user.company_id]
    
    return users

@router.get("/stats/overview", response_model=UserStats)
def get_user_stats(
    company_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용자 통계"""
    # 관리자가 아닌 경우 자신의 회사만 조회
    if not current_user.is_admin:
        company_id = current_user.company_id
    
    stats = user_service.get_user_stats(db, company_id)
    
    return UserStats(
        total_users=stats["total_users"],
        total_mentors=stats["total_mentors"],
        total_mentees=stats["total_mentees"],
        active_users=stats["active_users"],
        inactive_users=stats["inactive_users"]
    )

@router.get("/mentors/", response_model=List[UserResponse])
def get_mentors(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """멘토 목록 조회"""
    if department_id:
        mentors = user_service.get_users_by_department(db, department_id, skip, limit)
        mentors = [user for user in mentors if user.role == "mentor"]
    else:
        mentors = user_service.get_users_by_role(db, "mentor", skip, limit)
    
    # 관리자가 아닌 경우 같은 회사만 조회
    if not current_user.is_admin:
        mentors = [user for user in mentors if user.company_id == current_user.company_id]
    
    return mentors

@router.get("/mentees/", response_model=List[UserResponse])
def get_mentees(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """멘티 목록 조회"""
    if department_id:
        mentees = user_service.get_users_by_department(db, department_id, skip, limit)
        mentees = [user for user in mentees if user.role == "mentee"]
    else:
        mentees = user_service.get_users_by_role(db, "mentee", skip, limit)
    
    # 관리자가 아닌 경우 같은 회사만 조회
    if not current_user.is_admin:
        mentees = [user for user in mentees if user.company_id == current_user.company_id]
    
    return mentees