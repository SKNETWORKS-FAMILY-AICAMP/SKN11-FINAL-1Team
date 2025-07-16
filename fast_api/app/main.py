from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from pathlib import Path

from app.config import settings
from app.routers import auth, user, department, mentorship, task, docs, mentor, mentee, account, common

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Django와 연동된 Onboarding Quest API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정 (Django와 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",  # Django 서버
        "http://127.0.0.1:8000",
        "http://localhost:8080",  # Django 서버 (변경된 포트)
        "http://127.0.0.1:8080",
        "http://localhost:8081",  # Django 서버 (현재 포트)
        "http://127.0.0.1:8081",
        "http://localhost:8001",  # FastAPI 서버 (자기 자신)
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["인증"])
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/users", tags=["사용자"])
app.include_router(department.router, prefix=f"{settings.API_V1_STR}/departments", tags=["부서"])
app.include_router(mentorship.router, prefix=f"{settings.API_V1_STR}/mentorship", tags=["멘토쉽"])
app.include_router(task.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["과제"])
app.include_router(docs.router, prefix=f"{settings.API_V1_STR}/docs", tags=["문서"])
app.include_router(mentor.router, prefix=f"{settings.API_V1_STR}/mentor", tags=["멘토"])
app.include_router(mentee.router, prefix=f"{settings.API_V1_STR}/mentee", tags=["멘티"])
app.include_router(account.router, prefix=f"{settings.API_V1_STR}/account", tags=["계정"])
app.include_router(common.router, prefix=f"{settings.API_V1_STR}/common", tags=["공통"])

# 정적 파일 서빙 (업로드 파일 등)
if Path(settings.UPLOAD_DIR).exists():
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Django + FastAPI 통합 온보딩 퀘스트 API",
        "version": "1.0.0",
        "django_integration": True,
        "docs_url": "/docs",
        "api_base": settings.API_V1_STR
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "django_connected": True,
        "database": "connected"
    }

@app.get("/api/info")
async def api_info():
    """API 정보 엔드포인트"""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "api_version": settings.API_V1_STR,
        "django_base_url": settings.DJANGO_BASE_URL,
        "database_type": "sqlite",
        "cors_enabled": True
    }

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    print("🚀 FastAPI 서버 시작 중...")
    print(f"📊 데이터베이스: {settings.DATABASE_URL}")
    print(f"🔗 Django 연동: {settings.DJANGO_BASE_URL}")
    
    # 데이터베이스 테이블은 Django에서 관리
    print("✅ FastAPI 서버 시작 완료")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    print("🛑 FastAPI 서버 종료 중...")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )