from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
from config import settings

# PostgreSQL 데이터베이스 URL
DATABASE_URL = settings.database_url

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=True,  # SQL 쿼리 로깅 (개발 환경에서만 사용)
    # pool_pre_ping=True,
    # pool_recycle=300
)

# 세션 로컬 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

# 데이터베이스 세션 의존성
def get_db() -> Generator:
    """
    데이터베이스 세션을 생성하고 반환하는 의존성 함수
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 