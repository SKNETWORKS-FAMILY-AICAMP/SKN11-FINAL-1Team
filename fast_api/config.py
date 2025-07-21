from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv
from pathlib import Path

# 프로젝트 루트의 .env 파일 로드
current_dir = Path(__file__).parent
project_root = current_dir.parent
env_path = project_root / '.env'
load_dotenv(env_path)

def str2bool(v):
    return str(v).lower() in ("1", "true", "yes", "on")

class Settings(BaseSettings):
    # 서버 설정 (환경변수에서 가져오기)
    host: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port: int = int(os.getenv("FASTAPI_PORT", "8000"))
    
    # PostgreSQL 데이터베이스 설정 (환경변수에서 가져오기)
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "onboarding_quest_db")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    @property
    def database_url(self) -> str:
        if self.db_password:
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            return f"postgresql://{self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # 보안 설정 (환경변수에서 가져오기)
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS 설정
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",  # Django 서버
        "http://localhost:8080", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",  # Django 서버
        "http://127.0.0.1:8001"   # FastAPI 자체
    ]
    

    # 디버그 모드 (환경변수에서 가져오기)
    debug: bool = str2bool(os.getenv("DEBUG", "0"))

    # 로깅 설정
    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 설정 인스턴스 생성
settings = Settings() 