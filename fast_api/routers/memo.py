from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/memo", tags=["memo"])


@router.post("/", response_model=schemas.Memo)
async def create_memo(memo: schemas.MemoCreate, db: Session = Depends(get_db)):
    """새 메모 생성"""
    # 태스크 할당 존재 확인
    db_task_assign = crud.get_task_assign(db, task_id=memo.task_assign_id)
    if db_task_assign is None:
        raise HTTPException(status_code=404, detail="태스크 할당을 찾을 수 없습니다")
    
    # 사용자 존재 확인
    db_user = crud.get_user(db, user_id=memo.user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return crud.create_memo(db=db, memo=memo)


@router.get("/", response_model=List[schemas.Memo])
async def get_memos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """메모 목록 조회"""
    memos = crud.get_memos(db, skip=skip, limit=limit)
    return memos


@router.get("/{memo_id}", response_model=schemas.Memo)
async def get_memo(memo_id: int, db: Session = Depends(get_db)):
    """특정 메모 조회"""
    db_memo = crud.get_memo(db, memo_id=memo_id)
    if db_memo is None:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")
    return db_memo


@router.put("/{memo_id}", response_model=schemas.Memo)
async def update_memo(memo_id: int, memo: schemas.MemoCreate, db: Session = Depends(get_db)):
    """메모 정보 수정"""
    db_memo = crud.get_memo(db, memo_id=memo_id)
    if db_memo is None:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")
    return crud.update_memo(db=db, memo_id=memo_id, memo_update=memo)


@router.delete("/{memo_id}")
async def delete_memo(memo_id: int, db: Session = Depends(get_db)):
    """메모 삭제"""
    db_memo = crud.get_memo(db, memo_id=memo_id)
    if db_memo is None:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")
    
    crud.delete_memo(db, memo_id=memo_id)
    return {"message": "메모가 성공적으로 삭제되었습니다"}


@router.get("/task/{task_assign_id}", response_model=List[schemas.Memo])
async def get_memos_by_task(task_assign_id: int, db: Session = Depends(get_db)):
    """태스크별 메모 조회"""
    db_task_assign = crud.get_task_assign(db, task_id=task_assign_id)
    if db_task_assign is None:
        raise HTTPException(status_code=404, detail="태스크 할당을 찾을 수 없습니다")
    
    return crud.get_memos_by_task(db, task_assign_id=task_assign_id)


@router.get("/user/{user_id}", response_model=List[schemas.Memo])
async def get_memos_by_user(user_id: int, db: Session = Depends(get_db)):
    """사용자별 메모 조회"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return crud.get_memos_by_user(db, user_id=user_id)
