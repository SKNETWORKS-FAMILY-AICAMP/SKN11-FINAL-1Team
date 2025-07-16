from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # 데이터베이스 설정 - Django와 동일한 데이터베이스 사용
    DATABASE_URL: str = "sqlite:///./../../django_prj/onboarding_quest/db.sqlite3"
    
    # Django 연동 설정
    DJANGO_BASE_URL: str = "http://localhost:8000"
    DJANGO_SECRET_KEY: str = "django-insecure-do7ud-c7h49ny)48^c-&j408=@r599!d-j_j4)lzxl1(fz(k#+"
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # 애플리케이션 설정
    DEBUG: bool = True
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Onboarding Quest API"
    
    # JWT 설정
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 페이지네이션 설정
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 로그 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # AI/ML 설정
    OPENAI_API_KEY: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    
    # 이메일 설정
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Redis 설정 (캐시, 세션 등)
    REDIS_URL: Optional[str] = None
    
    # 환경 설정
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_database_url(self) -> str:
        """데이터베이스 URL 반환"""
        return self.DATABASE_URL

    def is_production(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """개발 환경 여부 확인"""
        return self.ENVIRONMENT.lower() == "development"

settings = Settings()

# 업로드 디렉토리 생성
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)