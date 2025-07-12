from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """새 사용자 생성"""
    # 이메일 중복 확인
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    return crud.create_user(db=db, user=user)


@router.get("/", response_model=List[schemas.User])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """모든 사용자 조회"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/mentors/", response_model=List[schemas.User])
async def get_mentors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """멘토 목록 조회"""
    mentors = crud.get_mentors(db, skip=skip, limit=limit)
    return mentors


@router.get("/mentees/", response_model=List[schemas.User])
async def get_mentees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """멘티 목록 조회"""
    mentees = crud.get_mentees(db, skip=skip, limit=limit)
    return mentees


@router.get("/{user_id}", response_model=schemas.User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자 조회"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return db_user


@router.put("/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """사용자 정보 수정"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 이메일 변경 시 중복 확인
    if user.email != db_user.email:
        existing_user = crud.get_user_by_email(db, email=user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    return crud.update_user(db=db, user_id=user_id, user_update=user)


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 삭제"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    crud.delete_user(db, user_id=user_id)
    return {"message": "사용자가 성공적으로 삭제되었습니다"}


@router.get("/mentors/{mentor_id}/mentees", response_model=List[schemas.User])
async def get_mentor_mentees(mentor_id: int, db: Session = Depends(get_db)):
    """특정 멘토의 멘티 목록 조회"""
    # 멘토 존재 확인
    mentor = crud.get_user(db, user_id=mentor_id)
    if mentor is None or mentor.role != "mentor":
        raise HTTPException(status_code=404, detail="멘토를 찾을 수 없습니다")
    
    # 멘토-멘티 관계를 통해 멘티 목록 조회
    mentorships = crud.get_mentorships_by_mentor(db, mentor_id=mentor_id)
    mentees = []
    for mentorship in mentorships:
        mentee = crud.get_user(db, user_id=mentorship.mentee_id)
        if mentee:
            mentees.append(mentee)
    
    return mentees 