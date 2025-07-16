#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 실행 중입니다!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "서버가 정상적으로 실행 중입니다."}

if __name__ == "__main__":
    uvicorn.run(
        "main_minimal:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    ) 