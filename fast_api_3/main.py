from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging

from database import init_db
from routers import companies, departments, users, task_assigns, mentorships

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI 애플리케이션 시작")
    # 기존 데이터베이스 파일 확인
    try:
        init_db()
        logger.info("기존 데이터베이스 연결 성공")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        raise
    yield
    logger.info("FastAPI 애플리케이션 종료")

# FastAPI 앱 생성
app = FastAPI(
    title="온보딩 퀘스트 API v3",
    description="신입사원 온보딩 프로세스 관리 시스템 - 기존 데이터베이스 사용",
    version="3.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(companies.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(task_assigns.router, prefix="/api/v1")
app.include_router(mentorships.router, prefix="/api/v1")

# 루트 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "온보딩 퀘스트 API v3에 오신 것을 환영합니다!",
        "version": "3.0.0",
        "status": "정상 작동",
        "database": "report_test.db (기존 데이터베이스 사용)",
        "endpoints": {
            "companies": "/api/v1/companies",
            "departments": "/api/v1/departments",
            "users": "/api/v1/users",
            "task_assigns": "/api/v1/task-assigns",
            "mentorships": "/api/v1/mentorships"
        },
        "features": [
            "회사 관리 (사업자번호 형식 지원)",
            "부서 관리",
            "사용자 관리 (멘토/멘티 역할 지원)",
            "과제 할당 관리",
            "멘토십 관리",
            "기존 데이터베이스 연동"
        ]
    }

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "서버가 정상적으로 작동 중입니다",
        "version": "3.0.0",
        "database": "report_test.db",
        "database_status": "connected"
    }

# 데이터베이스 스키마 정보 엔드포인트
@app.get("/schema")
async def get_schema_info():
    return {
        "message": "데이터베이스 스키마 정보",
        "tables": {
            "core_company": {
                "primary_key": "company_id (VARCHAR(12))",
                "description": "회사 정보 (사업자번호 형식)"
            },
            "core_department": {
                "primary_key": "department_id (INTEGER)",
                "description": "부서 정보"
            },
            "core_user": {
                "primary_key": "user_id (INTEGER)",
                "description": "사용자 정보 (멘토/멘티 역할)"
            },
            "core_taskassign": {
                "primary_key": "task_assign_id (INTEGER)",
                "description": "과제 할당 정보"
            },
            "core_mentorship": {
                "primary_key": "mentorship_id (INTEGER)",
                "description": "멘토십 정보"
            }
        },
        "key_features": [
            "company_id는 문자열 타입 (사업자번호 형식: 000-00-00000)",
            "모든 Primary Key는 정수 타입",
            "외래키 관계 완전 지원",
            "Date, DateTime 타입 지원",
            "Boolean 타입 지원"
        ]
    }

# 에러 핸들러
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "요청한 리소스를 찾을 수 없습니다", "error": "Not Found"}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"서버 오류: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "서버 내부 오류가 발생했습니다", "error": "Internal Server Error"}
    )

@app.exception_handler(400)
async def bad_request_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": "잘못된 요청입니다", "error": "Bad Request"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # 다른 포트 사용
        reload=True,
        log_level="info"
    ) 