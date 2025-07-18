from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import crud
import schemas
from database import get_db
from config import settings

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

# JWT 설정
ALGORITHM = "HS256"
SECRET_KEY = settings.secret_key

# Bearer 토큰 설정
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # 해시 형식을 인식할 수 없는 경우 False 반환
        print(f"Password verification error: {e}")
        print(f"Hash format: {hashed_password[:50]}...")
        return False

def get_password_hash(password: str) -> str:
    """비밀번호 해시화"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰 검증"""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = {"email": email}
    except JWTError:
        raise credentials_exception
    
    return token_data

def get_current_user(db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    """현재 로그인된 사용자 정보 조회"""
    user = crud.get_user_by_email(db, email=token_data["email"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다"
        )
    return user

def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    """활성화된 사용자만 허용"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 사용자입니다")
    return current_user

def require_admin(current_user: schemas.User = Depends(get_current_active_user)):
    """관리자 권한 필요"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user

def require_mentor(current_user: schemas.User = Depends(get_current_active_user)):
    """멘토 권한 필요"""
    if current_user.role != "mentor" and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="멘토 권한이 필요합니다"
        )
    return current_user

def require_mentee(current_user: schemas.User = Depends(get_current_active_user)):
    """멘티 권한 필요"""
    if current_user.role != "mentee" and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="멘티 권한이 필요합니다"
        )
    return current_user
