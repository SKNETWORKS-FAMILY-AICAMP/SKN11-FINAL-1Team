from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(
    prefix="/api/alarms",
    tags=["alarms"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.Alarm)
def create_alarm(
    alarm: schemas.AlarmCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """알람 생성"""
    # 관리자이거나 자신의 알람을 생성하는 경우만 허용
    if not current_user.is_admin and alarm.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 알람만 생성할 수 있습니다"
        )
    
    return crud.create_alarm(db=db, alarm=alarm)


@router.get("/", response_model=List[schemas.Alarm])
def read_alarms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """알람 목록 조회 (관리자 전용)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자만 전체 알람을 조회할 수 있습니다"
        )
    
    alarms = crud.get_alarms(db, skip=skip, limit=limit)
    return alarms


@router.get("/count")
def get_alarm_count(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """내 활성 알람 개수 조회"""
    count = crud.get_active_alarm_count_by_user(db, user_id=current_user.user_id)
    return {"success": True, "count": count}

@router.get("/my", response_model=List[schemas.Alarm])
def read_my_alarms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """내 알람 목록 조회"""
    alarms = crud.get_alarms_by_user(db, user_id=current_user.user_id, skip=skip, limit=limit)
    return alarms


@router.get("/my/active", response_model=List[schemas.Alarm])
def read_my_active_alarms(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """내 활성 알람 조회"""
    alarms = crud.get_active_alarms_by_user(db, user_id=current_user.user_id)
    return alarms


@router.get("/{alarm_id}", response_model=schemas.Alarm)
def read_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """알람 단일 조회"""
    db_alarm = crud.get_alarm(db, alarm_id=alarm_id)
    if db_alarm is None:
        raise HTTPException(status_code=404, detail="알람을 찾을 수 없습니다")
    
    # 관리자이거나 자신의 알람인 경우만 조회 허용
    if not current_user.is_admin and db_alarm.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 알람만 조회할 수 있습니다"
        )
    
    return db_alarm


@router.put("/{alarm_id}", response_model=schemas.Alarm)
def update_alarm(
    alarm_id: int,
    alarm: schemas.AlarmCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """알람 업데이트"""
    db_alarm = crud.get_alarm(db, alarm_id=alarm_id)
    if db_alarm is None:
        raise HTTPException(status_code=404, detail="알람을 찾을 수 없습니다")
    
    # 관리자이거나 자신의 알람인 경우만 수정 허용
    if not current_user.is_admin and db_alarm.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 알람만 수정할 수 있습니다"
        )
    
    return crud.update_alarm(db=db, alarm_id=alarm_id, alarm_update=alarm)


@router.patch("/{alarm_id}/status")
def update_alarm_status(
    alarm_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """알람 상태 업데이트 (읽음/안읽음)"""
    db_alarm = crud.get_alarm(db, alarm_id=alarm_id)
    if db_alarm is None:
        raise HTTPException(status_code=404, detail="알람을 찾을 수 없습니다")
    
    # 관리자이거나 자신의 알람인 경우만 상태 변경 허용
    if not current_user.is_admin and db_alarm.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 알람만 수정할 수 있습니다"
        )
    
    updated_alarm = crud.update_alarm_status(db=db, alarm_id=alarm_id, is_active=is_active)
    return {"message": "알람 상태가 업데이트되었습니다", "is_active": updated_alarm.is_active}


@router.patch("/my/mark-all-read")
def mark_all_my_alarms_read(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """내 모든 알람을 읽음 처리"""
    success = crud.mark_all_alarms_read(db=db, user_id=current_user.user_id)
    if success:
        return {"message": "모든 알람이 읽음 처리되었습니다"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알람 상태 업데이트에 실패했습니다"
        )


@router.delete("/{alarm_id}")
def delete_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """알람 삭제"""
    db_alarm = crud.get_alarm(db, alarm_id=alarm_id)
    if db_alarm is None:
        raise HTTPException(status_code=404, detail="알람을 찾을 수 없습니다")
    
    # 관리자이거나 자신의 알람인 경우만 삭제 허용
    if not current_user.is_admin and db_alarm.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="자신의 알람만 삭제할 수 있습니다"
        )
    
    crud.delete_alarm(db=db, alarm_id=alarm_id)
    return {"message": "알람이 삭제되었습니다"}
