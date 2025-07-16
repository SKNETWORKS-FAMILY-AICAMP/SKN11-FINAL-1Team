from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import User
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not user.check_password(password):
            return None
        return user

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def create_user(self, db: Session, user_data: dict) -> User:
        """사용자 생성"""
        user = User(**user_data)
        user.set_password(user_data["password"])
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def change_password(self, db: Session, user: User, new_password: str) -> bool:
        """비밀번호 변경"""
        try:
            user.set_password(new_password)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def reset_password(self, db: Session, user: User, new_password: str = "123") -> bool:
        """비밀번호 초기화"""
        try:
            user.set_password(new_password)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False