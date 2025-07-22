from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from datetime import datetime
from sqlalchemy import text
from config import settings
from database import engine, Base
from routers import users, tasks, chatbot, companies, departments, forms, curriculum, mentorship, memo, docs, chat, auth, alarms
import models  # 모델을 임포트하여 테이블 생성

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정 - 더 명확한 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",  # Django 서버
        "http://127.0.0.1:8001",  # FastAPI 서버
        "http://localhost:8000",  # Django 서버
        "http://localhost:8001"   # FastAPI 서버
    ],
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
# app.include_router(forms.router)  # 템플릿이 없어서 비활성화
app.include_router(chatbot.router)
app.include_router(alarms.router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "FastAPI Backend Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 데이터베이스 연결 테스트
        from database import SessionLocal
        db = SessionLocal()
        try:
            # 간단한 쿼리로 연결 확인 (SQLAlchemy 2.0+ 방식)
            result = db.execute(text("SELECT 1")).fetchone()
            db_status = "connected" if result else "disconnected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        finally:
            db.close()
            
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
            "companies": "/api/companies",
            "departments": "/api/departments", 
            "curriculum": "/api/curriculum",
            "mentorship": "/api/mentorship",
            "users": "/api/users",
            "tasks": "/api/tasks",
            "memo": "/api/memo",
            "docs": "/api/docs",
            "chat": "/api/chat",
            "forms": "/api/forms",
            "chatbot": "/api/chatbot",
            "alarms": "/api/alarms",
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

