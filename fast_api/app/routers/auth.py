from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.servies.auth_service import AuthService
from app.schemas.user import UserResponse, UserLogin, UserLoginResponse
from app.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()

@router.post("/login", response_model=UserLoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """로그인"""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.email})
    
    # 마지막 로그인 시간 업데이트
    user.last_login = datetime.utcnow()
    db.commit()
    
    return UserLoginResponse(
        user=user,
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/login-json", response_model=UserLoginResponse)
def login_json(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """JSON 로그인"""
    user = auth_service.authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.email})
    
    # 마지막 로그인 시간 업데이트
    user.last_login = datetime.utcnow()
    db.commit()
    
    return UserLoginResponse(
        user=user,
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/logout")
def logout(current_user = Depends(get_current_user)):
    """로그아웃"""
    # JWT는 stateless하므로 클라이언트에서 토큰 삭제
    return {"message": "로그아웃 되었습니다."}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_user)):
    """현재 사용자 정보 조회"""
    return current_user

@router.get("/verify-token")
def verify_token(current_user = Depends(get_current_user)):
    """토큰 검증"""
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "is_admin": current_user.is_admin
    }

@router.post("/refresh-token")
def refresh_token(current_user = Depends(get_current_user)):
    """토큰 갱신"""
    access_token = auth_service.create_access_token(data={"sub": current_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/user-role")
def get_user_role(current_user = Depends(get_current_user)):
    """사용자 역할 반환"""
    return {
        "role": current_user.role,
        "is_admin": current_user.is_admin,
        "redirect_url": get_redirect_url(current_user)
    }

def get_redirect_url(user):
    """사용자 역할에 따른 리다이렉트 URL 반환"""
    if user.is_admin:
        return "/admin/dashboard"
    elif user.role == "mentor":
        return "/mentor/dashboard"
    elif user.role == "mentee":
        return "/mentee/dashboard"
    else:
        return "/dashboard"