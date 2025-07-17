from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # FastAPI 서버 설정
    app_name: str = "Onboarding Quest API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8001
    
    # PostgreSQL 데이터베이스 설정
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "onboarding_quest"
    db_user: str = "bangsung-in"
    db_password: str = ""
    
    @property
    def database_url(self) -> str:
        if self.db_password:
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            return f"postgresql://{self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # 보안 설정
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS 설정
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://127.0.0.1:3000",
        "http://localhost:8001"
    ]
    
    # 로깅 설정
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 설정 인스턴스 생성
settings = Settings() 