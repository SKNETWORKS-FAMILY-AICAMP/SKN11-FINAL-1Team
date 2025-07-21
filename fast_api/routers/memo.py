from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db
import logging

# 로거 설정
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memo", tags=["memo"])


@router.post("/", response_model=schemas.Memo)
async def create_memo(memo: schemas.MemoCreate, db: Session = Depends(get_db)):
    """새 메모 생성"""
    try:
        # 태스크 할당 존재 확인
        db_task_assign = crud.get_task_assign(db, task_id=memo.task_assign_id)
        if db_task_assign is None:
            raise HTTPException(status_code=404, detail="태스크 할당을 찾을 수 없습니다")
        
        # 사용자 존재 확인
        db_user = crud.get_user(db, user_id=memo.user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return crud.create_memo(db=db, memo=memo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메모 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메모 생성 중 오류 발생: {str(e)}")


@router.get("/", response_model=List[schemas.Memo])
async def get_memos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """메모 목록 조회"""
    try:
        memos = crud.get_memos(db, skip=skip, limit=limit)
        return memos
    except Exception as e:
        logger.error(f"메모 목록 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메모 목록 조회 중 오류 발생: {str(e)}")


@router.get("/{memo_id}", response_model=schemas.Memo)
async def get_memo(memo_id: int, db: Session = Depends(get_db)):
    """특정 메모 조회"""
    try:
        db_memo = crud.get_memo(db, memo_id=memo_id)
        if db_memo is None:
            raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")
        return db_memo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메모 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메모 조회 중 오류 발생: {str(e)}")


@router.put("/{memo_id}", response_model=schemas.Memo)
async def update_memo(memo_id: int, memo: schemas.MemoCreate, db: Session = Depends(get_db)):
    """메모 정보 수정"""
    try:
        db_memo = crud.get_memo(db, memo_id=memo_id)
        if db_memo is None:
            raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")
        return crud.update_memo(db=db, memo_id=memo_id, memo_update=memo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메모 수정 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메모 수정 중 오류 발생: {str(e)}")


@router.delete("/{memo_id}")
async def delete_memo(memo_id: int, db: Session = Depends(get_db)):
    """메모 삭제"""
    try:
        db_memo = crud.get_memo(db, memo_id=memo_id)
        if db_memo is None:
            raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")
        
        crud.delete_memo(db, memo_id=memo_id)
        return {"message": "메모가 성공적으로 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메모 삭제 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메모 삭제 중 오류 발생: {str(e)}")


@router.get("/task/{task_assign_id}", response_model=List[schemas.Memo])
async def get_memos_by_task(task_assign_id: int, db: Session = Depends(get_db)):
    """태스크별 메모 조회"""
    try:
        logger.info(f"태스크 할당 ID {task_assign_id}의 메모 조회 요청")
        
        # 태스크 할당 존재 확인
        db_task_assign = crud.get_task_assign(db, task_id=task_assign_id)
        if db_task_assign is None:
            logger.warning(f"태스크 할당 ID {task_assign_id}를 찾을 수 없음")
            raise HTTPException(status_code=404, detail=f"태스크 할당 ID {task_assign_id}를 찾을 수 없습니다")
        
        # 메모 목록 조회
        memos = crud.get_memos_by_task(db, task_assign_id=task_assign_id)
        logger.info(f"태스크 할당 ID {task_assign_id}에 대해 {len(memos) if memos else 0}개의 메모를 찾음")
        
        return memos if memos else []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"태스크 할당 ID {task_assign_id} 메모 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메모 조회 중 오류 발생: {str(e)}")


@router.get("/user/{user_id}", response_model=List[schemas.Memo])
async def get_memos_by_user(user_id: int, db: Session = Depends(get_db)):
    """사용자별 메모 조회"""
    try:
        db_user = crud.get_user(db, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return crud.get_memos_by_user(db, user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 ID {user_id} 메모 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메모 조회 중 오류 발생: {str(e)}")
