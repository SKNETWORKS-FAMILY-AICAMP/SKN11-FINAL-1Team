from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/mentorship", tags=["mentorship"])

@router.post("/create")
async def create_mentorship_from_django(request_data: dict, db: Session = Depends(get_db)):
    """Django에서 사용하는 멘토쉽 생성 엔드포인트"""
    try:
        # 요청 데이터 파싱
        mentor_id = request_data.get('mentor_id')
        mentee_id = int(request_data.get('mentee_id'))
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        curriculum_ids = request_data.get('curriculum_ids', [])
        
        # 단일 커리큘럼도 지원 (기존 호환성)
        if 'curriculum_id' in request_data and not curriculum_ids:
            curriculum_ids = [int(request_data.get('curriculum_id'))]
        elif isinstance(curriculum_ids, str):
            curriculum_ids = [int(curriculum_ids)]
        elif isinstance(curriculum_ids, list):
            curriculum_ids = [int(cid) for cid in curriculum_ids]
        
        if not curriculum_ids:
            return {"success": False, "message": "커리큘럼을 선택해주세요."}
        
        # 멘토와 멘티 존재 확인
        mentor = crud.get_user(db, user_id=mentor_id)
        mentee = crud.get_user(db, user_id=mentee_id)
        
        if mentor is None:
            return {"success": False, "message": "멘토를 찾을 수 없습니다."}
        if mentee is None:
            return {"success": False, "message": "멘티를 찾을 수 없습니다."}
        
        # 커리큘럼 정보 조회
        curriculum_titles = []
        max_weeks = 0
        
        for curriculum_id in curriculum_ids:
            curriculum = crud.get_curriculum(db, curriculum_id=curriculum_id)
            if curriculum:
                curriculum_titles.append(curriculum.curriculum_title)
                max_weeks = max(max_weeks, curriculum.total_weeks or 0)
        
        combined_title = ' + '.join(curriculum_titles)
        
        # 멘토쉽 생성 데이터
        mentorship_create = schemas.MentorshipCreate(
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            start_date=start_date,
            end_date=end_date,
            curriculum_title=combined_title,  # curriculum_id 대신 curriculum_title 사용
            total_weeks=max_weeks,
            is_active=True
        )
        
        # 멘토쉽 생성
        mentorship = crud.create_mentorship(db=db, mentorship=mentorship_create)
        
        # TaskManage에서 TaskAssign 생성
        mentorship_start = datetime.strptime(start_date, '%Y-%m-%d')
        
        for curriculum_id in curriculum_ids:
            # 해당 커리큘럼의 TaskManage 조회
            task_manages = crud.get_task_manages_by_curriculum(db, curriculum_id=curriculum_id)
            
            for task in task_manages:
                week = task.week or 1
                task_start = mentorship_start + timedelta(days=(week-1)*7)
                period = task.period or 1
                
                # TaskAssign 생성
                task_assign_data = {
                    'title': task.title,
                    'description': task.description,
                    'guideline': task.guideline,
                    'week': week,
                    'order': task.order,
                    'scheduled_start_date': task_start.date(),
                    'scheduled_end_date': (task_start + timedelta(days=period)).date(),
                    'status': '진행전',
                    'priority': task.priority,
                    'mentorship_id': mentorship.mentorship_id  # id 대신 mentorship_id 사용
                }
                
                crud.create_task_assign(db=db, task=task_assign_data)
        
        return {
            "success": True, 
            "message": "멘토쉽이 성공적으로 생성되었습니다!",
            "mentorship_id": mentorship.mentorship_id  # id 대신 mentorship_id 사용
        }
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 멘토쉽 생성 중 오류: {e}")
        return {"success": False, "message": f"서버 오류가 발생했습니다: {str(e)}"}

@router.post("/", response_model=schemas.Mentorship)
async def create_mentorship(mentorship: schemas.MentorshipCreate, db: Session = Depends(get_db)):
    """새 멘토십 생성"""
    # 멘토와 멘티 존재 확인
    mentor = crud.get_user(db, user_id=mentorship.mentor_id)
    mentee = crud.get_user(db, user_id=mentorship.mentee_id)
    
    if mentor is None:
        raise HTTPException(status_code=404, detail="멘토를 찾을 수 없습니다")
    if mentee is None:
        raise HTTPException(status_code=404, detail="멘티를 찾을 수 없습니다")
    
    # 멘토/멘티 역할 확인
    if mentor.role != 'mentor':
        raise HTTPException(status_code=400, detail="지정된 사용자가 멘토가 아닙니다")
    if mentee.role != 'mentee':
        raise HTTPException(status_code=400, detail="지정된 사용자가 멘티가 아닙니다")
    
    return crud.create_mentorship(db=db, mentorship=mentorship)


@router.get("/", response_model=List[schemas.MentorshipResponse])
async def get_mentorships(
    skip: int = 0, 
    limit: int = 100, 
    mentor_id: Optional[int] = Query(None, description="멘토 ID로 필터링"),
    mentee_id: Optional[int] = Query(None, description="멘티 ID로 필터링"),
    search: Optional[str] = Query(None, description="멘티 이름 또는 커리큘럼으로 검색"),
    db: Session = Depends(get_db)
):
    """멘토십 목록 조회 (필터링 및 검색 지원)"""
    mentorships = crud.get_mentorships_with_filters(
        db=db, 
        mentor_id=mentor_id,
        mentee_id=mentee_id,
        search=search,
        skip=skip, 
        limit=limit
    )
    
    # 멘토십 정보를 풍부한 형태로 변환
    enriched_mentorships = []
    for mentorship in mentorships:
        # 멘티 정보
        mentee = crud.get_user(db, user_id=mentorship.mentee_id)
        # 멘토 정보
        mentor = crud.get_user(db, user_id=mentorship.mentor_id)
        
        # 태스크 정보 (진척도 계산용)
        tasks = crud.get_tasks_by_mentorship(db, mentorship_id=mentorship.mentorship_id)
        completed_tasks = [task for task in tasks if task.status == 'completed']
        
        enriched_mentorship = {
            "id": mentorship.mentorship_id,  # Django 모델의 기본키
            "mentor_id": mentorship.mentor_id,
            "mentee_id": mentorship.mentee_id,
            "curriculum_id": None,  # Django 모델에는 curriculum_id가 없음
            "start_date": mentorship.start_date,
            "end_date": mentorship.end_date,
            "status": "active" if mentorship.is_active else "inactive",  # Django 모델 구조
            "created_at": None,  # Django 모델에 없는 필드
            "updated_at": None,  # Django 모델에 없는 필드
            # 추가 정보
            "mentee_name": f"{mentee.first_name} {mentee.last_name}" if mentee else "Unknown",
            "mentor_name": f"{mentor.first_name} {mentor.last_name}" if mentor else "Unknown", 
            "curriculum_title": mentorship.curriculum_title or "기본 커리큘럼",  # Django 모델의 curriculum_title 사용
            "total_weeks": mentorship.total_weeks or 12,  # Django 모델의 total_weeks 사용
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "tags": [mentee.department.department_name if mentee and mentee.department else "", 
                    mentee.position if mentee else ""] if mentee else [],
        }
        
        enriched_mentorships.append(enriched_mentorship)
    
    return enriched_mentorships


@router.get("/{mentorship_id}", response_model=schemas.Mentorship)
async def get_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """특정 멘토십 조회"""
    db_mentorship = crud.get_mentorship(db, mentorship_id=mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    return db_mentorship


@router.put("/{mentorship_id}", response_model=schemas.Mentorship)
async def update_mentorship(mentorship_id: int, mentorship: schemas.MentorshipCreate, db: Session = Depends(get_db)):
    """멘토십 정보 수정"""
    db_mentorship = crud.get_mentorship(db, mentorship_id=mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    return crud.update_mentorship(db=db, mentorship_id=mentorship_id, mentorship_update=mentorship)


@router.delete("/{mentorship_id}")
async def delete_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십 삭제"""
    db_mentorship = crud.get_mentorship(db, mentorship_id=mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    
    crud.delete_mentorship(db, mentorship_id=mentorship_id)
    return {"message": "멘토십이 성공적으로 삭제되었습니다"}


@router.get("/mentor/{mentor_id}", response_model=List[schemas.Mentorship])
async def get_mentorships_by_mentor(mentor_id: int, db: Session = Depends(get_db)):
    """멘토별 멘토십 조회"""
    mentor = crud.get_user(db, user_id=mentor_id)
    if mentor is None:
        raise HTTPException(status_code=404, detail="멘토를 찾을 수 없습니다")
    
    return crud.get_mentorships_by_mentor(db, mentor_id=mentor_id)


@router.get("/mentee/{mentee_id}", response_model=List[schemas.Mentorship])
async def get_mentorships_by_mentee(mentee_id: int, db: Session = Depends(get_db)):
    """멘티별 멘토십 조회"""
    mentee = crud.get_user(db, user_id=mentee_id)
    if mentee is None:
        raise HTTPException(status_code=404, detail="멘티를 찾을 수 없습니다")
    
    return crud.get_mentorships_by_mentee(db, mentee_id=mentee_id)


@router.patch("/{mentorship_id}/activate")
async def activate_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십 활성화"""
    db_mentorship = crud.get_mentorship(db, mentorship_id=mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    
    crud.update_mentorship_status(db, mentorship_id=mentorship_id, is_active=True)
    return {"message": "멘토십이 활성화되었습니다"}


@router.patch("/{mentorship_id}/deactivate")
async def deactivate_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십 비활성화"""
    db_mentorship = crud.get_mentorship(db, mentorship_id=mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    
    crud.update_mentorship_status(db, mentorship_id=mentorship_id, is_active=False)
    return {"message": "멘토십이 비활성화되었습니다"}
