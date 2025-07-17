from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/mentorship", tags=["mentorship"])


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


@router.get("/", response_model=List[schemas.Mentorship])
async def get_mentorships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """멘토십 목록 조회"""
    mentorships = crud.get_mentorships(db, skip=skip, limit=limit)
    return mentorships


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
