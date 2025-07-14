from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 기존 report_test.db 파일을 사용
DATABASE_URL = "sqlite:///../report_test.db"

# 데이터베이스 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite에서 필요한 설정
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 기존 데이터베이스 사용 - 테이블 생성 안함
def init_db():
    """기존 데이터베이스 파일 존재 여부 확인"""
    db_path = "../report_test.db"
    if os.path.exists(db_path):
        print(f"기존 데이터베이스 파일 사용: {db_path}")
    else:
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        raise FileNotFoundError(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}") 