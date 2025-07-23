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
    """문자열을 boolean으로 변환"""
    return str(v).lower() in ("1", "true", "yes", "on")

def parse_list(v, delimiter=','):
    """문자열을 리스트로 변환"""
    if not v:
        return []
    return [item.strip() for item in v.split(delimiter) if item.strip()]

class Settings(BaseSettings):
    # =================================
    # 🌐 서버 설정
    # =================================
    host: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port: int = int(os.getenv("FASTAPI_PORT", "8001"))
    base_url: str = os.getenv("FASTAPI_BASE_URL", "http://localhost:8001")
    
    # Django 서버 정보
    django_host: str = os.getenv("DJANGO_HOST", "0.0.0.0")
    django_port: int = int(os.getenv("DJANGO_PORT", "8000"))
    django_base_url: str = os.getenv("DJANGO_BASE_URL", "http://localhost:8000")
    
    # =================================
    # 🗄️ PostgreSQL 데이터베이스 설정
    # =================================
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "onboarding_quest_db")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    @property
    def database_url(self) -> str:
        """PostgreSQL 연결 URL 생성"""
        if self.db_password:
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            return f"postgresql://{self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # =================================
    # 🔒 보안 설정
    # =================================
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    debug: bool = str2bool(os.getenv("DEBUG", "False"))
    
    # =================================
    # 🌍 CORS 설정
    # =================================
    allowed_hosts_str: str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
    allowed_origins_str: str = os.getenv("ALLOWED_ORIGINS", "")
    
    @property
    def allowed_hosts(self) -> List[str]:
        """Allowed hosts 파싱"""
        return parse_list(self.allowed_hosts_str)
    
    @property
    def allowed_origins(self) -> List[str]:
        """CORS allowed origins 생성"""
        if self.allowed_origins_str:
            return parse_list(self.allowed_origins_str)
        
        # 기본값 설정
        return [
            "http://localhost:3000",
            "http://localhost:8000",  # Django 서버
            "http://localhost:8001",  # FastAPI 서버
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8001"
        ]
    
    # =================================
    # 🤖 RAG 시스템 설정
    # =================================
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "rag_multiformat")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    rag_api_url: str = os.getenv("RAG_API_URL", "http://localhost:8001")
    
    # =================================
    # 📁 파일 업로드 설정
    # =================================
    upload_base_dir: str = os.getenv("UPLOAD_BASE_DIR", "uploaded_docs")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "50")) * 1024 * 1024  # MB to bytes
    media_root: str = os.getenv("MEDIA_ROOT", "media")
    media_url: str = os.getenv("MEDIA_URL", "/media/")
    
    # =================================
    # 📋 로깅 설정
    # =================================
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 추가 필드 무시

# 설정 인스턴스 생성
settings = Settings()