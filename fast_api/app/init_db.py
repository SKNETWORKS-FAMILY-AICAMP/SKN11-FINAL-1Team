"""
데이터베이스 초기 데이터 생성 스크립트

Django에서 FastAPI로 마이그레이션 후 초기 데이터를 생성합니다.
"""
import sys
import os
from pathlib import Path

# 현재 스크립트의 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# 두 가지 실행 방법을 모두 지원하도록 import
try:
    # FastAPI 서버에서 실행되는 경우
    from app.models import Base, Company, Department, User, Curriculum, TaskManage
    from app.config import settings
except ImportError:
    # 독립 스크립트로 실행되는 경우
    from app.models import Base, Company, Department, User, Curriculum, TaskManage
    from app.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """데이터베이스 초기화"""
    engine = create_engine(settings.DATABASE_URL)
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    logger.info("데이터베이스 테이블이 생성되었습니다.")
    
    # 세션 생성
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 샘플 데이터 생성
        create_sample_data(db)
        logger.info("샘플 데이터가 생성되었습니다.")
    except Exception as e:
        logger.error(f"샘플 데이터 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_data(db):
    """샘플 데이터 생성"""
    
    # 회사 생성 (기존 데이터 확인)
    company = db.query(Company).filter_by(company_id="123-45-67890").first()
    if not company:
        company = Company(
            company_id="123-45-67890",
            company_name="샘플 회사"
        )
        db.add(company)
        db.commit()
        logger.info(f"회사 생성: {company.company_name}")
    else:
        logger.info(f"회사 이미 존재: {company.company_name}")
    
    # 부서 생성 (기존 데이터 확인)
    dept_names = ["개발팀", "인사팀", "마케팅팀"]
    dept_descriptions = ["소프트웨어 개발 부서", "인사 관리 부서", "마케팅 및 홍보 부서"]
    
    departments = []
    for name, desc in zip(dept_names, dept_descriptions):
        dept = db.query(Department).filter_by(department_name=name, company_id=company.company_id).first()
        if not dept:
            dept = Department(
                department_name=name,
                description=desc,
                company_id=company.company_id,
                is_active=True
            )
            db.add(dept)
            departments.append(dept)
        else:
            departments.append(dept)
    
    db.commit()
    logger.info(f"부서 처리 완료: {[d.department_name for d in departments]}")
    
    # 사용자 생성 (기존 데이터 확인)
    users_data = [
        {
            "employee_number": 1001,
            "email": "admin@example.com",
            "first_name": "관리자",
            "last_name": "김",
            "position": "관리자",
            "job_part": "관리",
            "role": "mentor",
            "is_admin": True,
            "password": "admin123"
        },
        {
            "employee_number": 1002,
            "email": "mentor@example.com",
            "first_name": "멘토",
            "last_name": "이",
            "position": "시니어 개발자",
            "job_part": "백엔드 개발",
            "role": "mentor",
            "is_admin": False,
            "password": "mentor123"
        },
        {
            "employee_number": 1003,
            "email": "mentee@example.com",
            "first_name": "멘티",
            "last_name": "박",
            "position": "주니어 개발자",
            "job_part": "프론트엔드 개발",
            "role": "mentee",
            "is_admin": False,
            "password": "mentee123"
        }
    ]
    
    for user_data in users_data:
        existing_user = db.query(User).filter_by(email=user_data["email"]).first()
        if not existing_user:
            user = User(
                employee_number=user_data["employee_number"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                position=user_data["position"],
                job_part=user_data["job_part"],
                role=user_data["role"],
                is_admin=user_data["is_admin"],
                company_id=company.company_id,
                department_id=departments[0].department_id
            )
            user.set_password(user_data["password"])
            db.add(user)
            logger.info(f"사용자 생성: {user.email}")
        else:
            logger.info(f"사용자 이미 존재: {existing_user.email}")
    
    db.commit()
    logger.info("사용자 처리 완료")
    
    # 커리큘럼 생성 (기존 데이터 확인)
    curriculum = db.query(Curriculum).filter_by(curriculum_title="신입 개발자 온보딩").first()
    if not curriculum:
        curriculum = Curriculum(
            curriculum_title="신입 개발자 온보딩",
            curriculum_description="신입 개발자를 위한 4주 온보딩 프로그램",
            department_id=departments[0].department_id,
            common=False,
            total_weeks=4,
            week_schedule="""1주차: 회사 소개 및 환경 설정
2주차: 개발 환경 구축 및 기본 프로젝트 실습
3주차: 팀 프로젝트 참여 및 코드 리뷰
4주차: 개인 과제 수행 및 발표"""
        )
        db.add(curriculum)
        db.commit()
        logger.info(f"커리큘럼 생성: {curriculum.curriculum_title}")
    else:
        logger.info(f"커리큘럼 이미 존재: {curriculum.curriculum_title}")
    
    # 과제 템플릿 생성 (기존 데이터 확인)
    tasks_data = [
        {
            "title": "회사 소개 영상 시청",
            "description": "회사의 역사와 문화를 이해하기 위한 영상 시청",
            "guideline": "영상 시청 후 간단한 소감문 작성",
            "week": 1, "order": 1, "period": 1, "priority": "중"
        },
        {
            "title": "개발 환경 설정",
            "description": "개발에 필요한 도구들 설치 및 환경 설정",
            "guideline": "IDE, Git, 필수 라이브러리 설치",
            "week": 1, "order": 2, "period": 2, "priority": "상"
        },
        {
            "title": "Hello World 프로젝트",
            "description": "첫 번째 프로젝트로 간단한 Hello World 애플리케이션 구현",
            "guideline": "사용 기술 스택에 맞는 Hello World 프로젝트 생성",
            "week": 2, "order": 1, "period": 3, "priority": "상"
        },
        {
            "title": "코드 리뷰 참여",
            "description": "팀의 코드 리뷰 과정에 참여하여 코드 품질 향상 경험",
            "guideline": "최소 3개의 PR에 대한 리뷰 참여",
            "week": 3, "order": 1, "period": 5, "priority": "중"
        },
        {
            "title": "개인 프로젝트 발표",
            "description": "개인 프로젝트 결과 발표 및 회고",
            "guideline": "프로젝트 개요, 구현 과정, 학습 내용 발표",
            "week": 4, "order": 1, "period": 2, "priority": "상"
        }
    ]
    
    created_tasks = 0
    for task_data in tasks_data:
        existing_task = db.query(TaskManage).filter_by(
            curriculum_id=curriculum.curriculum_id,
            title=task_data["title"]
        ).first()
        
        if not existing_task:
            task = TaskManage(
                curriculum_id=curriculum.curriculum_id,
                title=task_data["title"],
                description=task_data["description"],
                guideline=task_data["guideline"],
                week=task_data["week"],
                order=task_data["order"],
                period=task_data["period"],
                priority=task_data["priority"]
            )
            db.add(task)
            created_tasks += 1
    
    db.commit()
    logger.info(f"과제 템플릿 처리 완료: {created_tasks}개 생성")
    
    logger.info("샘플 데이터 생성 완료!")
    logger.info("로그인 정보:")
    logger.info("  관리자: admin@example.com / admin123")
    logger.info("  멘토: mentor@example.com / mentor123")
    logger.info("  멘티: mentee@example.com / mentee123")

if __name__ == "__main__":
    init_database() 