from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/mentorships", tags=["mentorships"])

@router.post("/", response_model=schemas.Mentorship)
def create_mentorship(mentorship: schemas.MentorshipCreate, db: Session = Depends(get_db)):
    """멘토십 생성"""
    # 멘토 존재 확인
    db_mentor = crud.get_user(db=db, user_id=mentorship.mentor_id)
    if not db_mentor:
        raise HTTPException(status_code=400, detail="존재하지 않는 멘토입니다.")
    
    # 멘토 역할 확인
    if db_mentor.role != "mentor":
        raise HTTPException(status_code=400, detail="멘토 역할의 사용자만 멘토가 될 수 있습니다.")
    
    # 멘티 존재 확인
    db_mentee = crud.get_user(db=db, user_id=mentorship.mentee_id)
    if not db_mentee:
        raise HTTPException(status_code=400, detail="존재하지 않는 멘티입니다.")
    
    # 멘티 역할 확인
    if db_mentee.role != "mentee":
        raise HTTPException(status_code=400, detail="멘티 역할의 사용자만 멘티가 될 수 있습니다.")
    
    # 자기 자신을 멘토/멘티로 설정하는 것 방지
    if mentorship.mentor_id == mentorship.mentee_id:
        raise HTTPException(status_code=400, detail="자기 자신을 멘토/멘티로 설정할 수 없습니다.")
    
    return crud.create_mentorship(db=db, mentorship=mentorship)

@router.get("/", response_model=List[schemas.Mentorship])
def read_mentorships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """멘토십 목록 조회"""
    mentorships = crud.get_mentorships(db=db, skip=skip, limit=limit)
    return mentorships

@router.get("/{mentorship_id}", response_model=schemas.Mentorship)
def read_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십 조회"""
    db_mentorship = crud.get_mentorship(db=db, mentorship_id=mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다.")
    return db_mentorship

@router.put("/{mentorship_id}", response_model=schemas.Mentorship)
def update_mentorship(mentorship_id: int, mentorship: schemas.MentorshipUpdate, db: Session = Depends(get_db)):
    """멘토십 수정"""
    # 멘토 존재 확인 (mentor_id가 변경되는 경우)
    if mentorship.mentor_id:
        db_mentor = crud.get_user(db=db, user_id=mentorship.mentor_id)
        if not db_mentor:
            raise HTTPException(status_code=400, detail="존재하지 않는 멘토입니다.")
        if db_mentor.role != "mentor":
            raise HTTPException(status_code=400, detail="멘토 역할의 사용자만 멘토가 될 수 있습니다.")
    
    # 멘티 존재 확인 (mentee_id가 변경되는 경우)
    if mentorship.mentee_id:
        db_mentee = crud.get_user(db=db, user_id=mentorship.mentee_id)
        if not db_mentee:
            raise HTTPException(status_code=400, detail="존재하지 않는 멘티입니다.")
        if db_mentee.role != "mentee":
            raise HTTPException(status_code=400, detail="멘티 역할의 사용자만 멘티가 될 수 있습니다.")
    
    # 자기 자신을 멘토/멘티로 설정하는 것 방지
    if mentorship.mentor_id and mentorship.mentee_id and mentorship.mentor_id == mentorship.mentee_id:
        raise HTTPException(status_code=400, detail="자기 자신을 멘토/멘티로 설정할 수 없습니다.")
    
    db_mentorship = crud.update_mentorship(db=db, mentorship_id=mentorship_id, mentorship=mentorship)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다.")
    return db_mentorship

@router.delete("/{mentorship_id}")
def delete_mentorship(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십 삭제"""
    db_mentorship = crud.delete_mentorship(db=db, mentorship_id=mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다.")
    return {"message": "멘토십이 성공적으로 삭제되었습니다."}

@router.get("/mentor/{mentor_id}", response_model=List[schemas.Mentorship])
def read_mentorships_by_mentor(mentor_id: int, db: Session = Depends(get_db)):
    """멘토별 멘토십 목록 조회"""
    mentorships = crud.get_mentorships_by_mentor(db=db, mentor_id=mentor_id)
    return mentorships

@router.get("/mentee/{mentee_id}", response_model=List[schemas.Mentorship])
def read_mentorships_by_mentee(mentee_id: int, db: Session = Depends(get_db)):
    """멘티별 멘토십 목록 조회"""
    mentorships = crud.get_mentorships_by_mentee(db=db, mentee_id=mentee_id)
    return mentorships

@router.get("/{mentorship_id}/task-assigns", response_model=List[schemas.TaskAssign])
def read_mentorship_task_assigns(mentorship_id: int, db: Session = Depends(get_db)):
    """멘토십별 과제 할당 목록 조회"""
    task_assigns = crud.get_task_assigns_by_mentorship(db=db, mentorship_id=mentorship_id)
    return task_assigns 