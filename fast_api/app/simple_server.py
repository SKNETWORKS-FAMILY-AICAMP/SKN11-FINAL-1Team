#!/usr/bin/env python3
"""
간단한 FastAPI 서버 실행 스크립트
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
sys.path.insert(0, '.')

from app.database import create_tables
from app.config import settings

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Onboarding Quest API",
    version="1.0.0",
    description="Django와 연동된 Onboarding Quest API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 라우트
@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상적으로 실행되었습니다!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "sqlite"}

@app.get("/api/v1/departments/")
def get_departments():
    """부서 목록 반환"""
    return {
        "departments": [
            {"department_id": 1, "department_name": "개발", "is_active": True},
            {"department_id": 2, "department_name": "영업", "is_active": True},
            {"department_id": 3, "department_name": "HR", "is_active": True}
        ],
        "total": 3
    }

# 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 데이터베이스 테이블 생성"""
    try:
        create_tables()
        print("✅ 데이터베이스 테이블이 생성되었습니다.")
    except Exception as e:
        print(f"❌ 데이터베이스 테이블 생성 실패: {e}")

if __name__ == "__main__":
    print("🚀 FastAPI 서버를 시작합니다...")
    print(f"📊 데이터베이스: {settings.DATABASE_URL}")
    print("🌐 서버 주소: http://localhost:8001")
    print("📚 API 문서: http://localhost:8001/docs")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    ) 