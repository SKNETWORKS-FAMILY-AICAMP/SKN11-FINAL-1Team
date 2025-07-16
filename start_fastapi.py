#!/usr/bin/env python3
"""
FastAPI 서버 실행 스크립트
"""

import os
import sys
import uvicorn
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.absolute()
FASTAPI_APP_PATH = PROJECT_ROOT / "fast_api" / "app"

# Python 경로에 FastAPI 앱 디렉토리 추가
sys.path.insert(0, str(FASTAPI_APP_PATH))

# 작업 디렉토리 변경
os.chdir(str(FASTAPI_APP_PATH))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 직접 앱 생성
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

# 기본 라우트들
@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상적으로 실행되었습니다! 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "sqlite"}

@app.get("/api/v1/departments/")
def get_departments():
    """부서 목록 반환 (Django 호환)"""
    return {
        "departments": [
            {"department_id": 1, "department_name": "개발", "is_active": True},
            {"department_id": 2, "department_name": "영업", "is_active": True},
            {"department_id": 3, "department_name": "HR", "is_active": True}
        ],
        "total": 3,
        "page": 1,
        "per_page": 20
    }

@app.get("/api/v1/users/")
def get_users():
    """사용자 목록 반환 (Django 호환)"""
    return {
        "users": [
            {"user_id": 1, "email": "hr_admin@ezflow.com", "role": "mentor", "is_admin": True},
            {"user_id": 2, "email": "dev_mentor1@ezflow.com", "role": "mentor", "is_admin": False},
            {"user_id": 3, "email": "dev_mentee1@ezflow.com", "role": "mentee", "is_admin": False},
        ],
        "total": 3
    }

if __name__ == "__main__":
    print("🚀 FastAPI 서버를 시작합니다...")
    print(f"📁 작업 디렉토리: {FASTAPI_APP_PATH}")
    print(f"🌐 서버 주소: http://localhost:8001")
    print("📚 API 문서: http://localhost:8001/docs")
    print("💡 Django 연동 테스트: http://localhost:8001/api/v1/departments/")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    ) 