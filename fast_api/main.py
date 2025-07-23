from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from datetime import datetime
from sqlalchemy import text
from config import settings
from database import engine, Base
from routers import users, tasks, chatbot, companies, departments, forms, curriculum, mentorship, memo, docs, chat, auth, alarms, documents
import models  # 모델을 임포트하여 테이블 생성

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정 - 더 명확한 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 임시로 모든 origin 허용
    allow_credentials=True,
    # allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    # allow_headers=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(departments.router)
app.include_router(curriculum.router)
app.include_router(mentorship.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(memo.router)
app.include_router(docs.router)
app.include_router(chat.router)
app.include_router(documents.router)
# app.include_router(forms.router)  # 템플릿이 없어서 비활성화
app.include_router(chatbot.router)
app.include_router(alarms.router)
# app.include_router(rag.router)  # chat 라우터로 통합됨


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "FastAPI 통합 백엔드 서버",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "integration_status": "완전 통합 완료"
    }

@app.get("/health")
async def health():
    """서버 건강성 체크"""
    return {
        "status": "healthy",
        "message": "FastAPI server is running",
        "database": "PostgreSQL",
        "rag_available": True  # RAG 시스템 상태는 /api/rag/health에서 확인
    }

@app.get("/api/")
async def api_root():
    """API 루트 엔드포인트"""
    return {
        "message": "Onboarding Quest FastAPI 서버가 실행 중입니다! (PostgreSQL DB 기반)",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "database": "PostgreSQL",
        "endpoints": {
            "auth": "/api/auth",
            "companies": "/api/companies",
            "departments": "/api/departments", 
            "curriculum": "/api/curriculum",
            "mentorship": "/api/mentorship",
            "users": "/api/users",
            "tasks": "/api/tasks",
            "memo": "/api/memo",
            "docs": "/api/docs",
            "chat": "/api/chat",
            "documents": "/api/documents",
            "chatbot": "/api/chatbot",
            "alarms": "/api/alarms"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

