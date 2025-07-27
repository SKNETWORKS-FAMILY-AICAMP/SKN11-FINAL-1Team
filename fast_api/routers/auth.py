from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, date
import schemas
import crud
from database import get_db
from auth import (
    verify_password, 
    create_access_token, 
    get_current_active_user,
    get_current_user
)
from config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class LoginData(schemas.BaseModel):
    email: str
    password: str

@router.post("/login", response_model=schemas.Token)
async def login(login_data: LoginData, db: Session = Depends(get_db)):    
    """사용자 로그인"""
    # 이메일로 사용자 조회
    user = crud.get_user_by_email(db, email=login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 비밀번호 검증
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 비활성화된 사용자 체크
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다",
        )
    # 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # user 필드 기본값 처리
    if not user.job_part:
        user.job_part = "기본"
    if not user.position:
        user.position = "기본"
    if not user.role:
        user.role = "mentee"
    if not user.join_date:
        user.join_date = date(2024, 1, 1)
    
    # user를 딕셔너리로 변환해서 반환
    user_dict = schemas.User.from_orm(user).dict()
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict
    }

@router.post("/logout")
async def logout(current_user: schemas.User = Depends(get_current_active_user)):
    """사용자 로그아웃"""
    # JWT는 stateless이므로 클라이언트에서 토큰을 삭제하도록 안내
    return {"message": "성공적으로 로그아웃되었습니다. 클라이언트에서 토큰을 삭제하세요."}

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    """현재 로그인된 사용자 정보 조회"""
    return current_user

@router.post("/refresh")
async def refresh_token(current_user: schemas.User = Depends(get_current_user)):
    """토큰 갱신"""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": current_user  # 이미 Pydantic 모델이므로 그대로 반환
    }

@router.get("/check")
async def check_auth(current_user: schemas.User = Depends(get_current_active_user)):
    """인증 상태 확인"""
    return {
        "authenticated": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "is_admin": current_user.is_admin
    }
