from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from config import settings
from database import engine, Base
from routers import users, tasks, chatbot, companies, departments, templates as templates_router, forms
import models  # 모델을 임포트하여 테이블 생성

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    description="멘토링 온보딩 퀘스트를 위한 FastAPI 서버 - PostgreSQL 기반 CRUD 구현",
    version=settings.app_version,
    debug=settings.debug
)

# 정적 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(companies.router)
app.include_router(departments.router)
app.include_router(templates_router.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(forms.router)
app.include_router(chatbot.router)

@app.get("/")
async def root():
    """루트 엔드포인트 - 폼 관리 홈으로 리다이렉트"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/forms/")


@app.get("/api/")
async def api_root():
    """API 루트 엔드포인트"""
    return {
        "message": "Onboarding Quest FastAPI 서버가 실행 중입니다! (PostgreSQL DB 기반)",
        "version": settings.app_version,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "database": "PostgreSQL",
        "endpoints": {
            "companies": "/api/companies",
            "departments": "/api/departments", 
            "templates": "/api/templates",
            "users": "/api/users",
            "tasks": "/api/tasks",
            "chatbot": "/api/chatbot"
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "message": "서버가 정상적으로 작동중입니다",
        "version": settings.app_version,
        "database": "PostgreSQL"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 