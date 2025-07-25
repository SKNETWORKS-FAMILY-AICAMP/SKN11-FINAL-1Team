from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pydantic import BaseModel
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


from fastapi.responses import JSONResponse
import traceback

@router.post("/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        print("🔥 받은 요청 데이터:", user.dict())
        
        # 데이터베이스 연결 확인
        try:
            db.execute(text("SELECT 1")).fetchone()
            print("✅ 데이터베이스 연결 성공")
        except Exception as db_error:
            print(f"❌ 데이터베이스 연결 실패: {db_error}")
            raise HTTPException(status_code=500, detail=f"데이터베이스 연결 실패: {str(db_error)}")
        
        # 이메일 중복 확인
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            print(f"❌ 이메일 중복: {user.email}")
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
        
        # 사용자 생성
        print("🚀 사용자 생성 시작...")
        created_user = crud.create_user(db=db, user=user)
        print(f"✅ 사용자 생성 성공: {created_user.user_id}")
        
        # 생성된 사용자 검증
        verify_user = crud.get_user(db, created_user.user_id)
        if verify_user:
            print(f"✅ 사용자 검증 성공: {verify_user.email}")
        else:
            print("❌ 사용자 검증 실패: 생성 후 조회 불가")
            
        return created_user
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        print("❌ 예외 발생:")
        print(f"예외 타입: {type(e).__name__}")
        print(f"예외 메시지: {str(e)}")
        traceback.print_exc()  # 상세 스택 트레이스 출력
        
        # 더 자세한 에러 정보 반환
        return JSONResponse(
            status_code=500, 
            content={
                "success": False, 
                "error": str(e),
                "error_type": type(e).__name__,
                "detail": f"사용자 생성 중 오류 발생: {str(e)}"
            }
        )


@router.get("/", response_model=List[schemas.User])
async def get_users(
    skip: int = 0, 
    limit: int = 100, 
    company_id: str = None,
    department_id: int = None,
    search: str = None,
    role: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """사용자 목록 조회 - 필터링 옵션 포함"""
    users = crud.get_users_with_filters(
        db, 
        skip=skip, 
        limit=limit,
        company_id=company_id,
        department_id=department_id,
        search=search,
        role=role,
        is_active=is_active
    )
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
async def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    """사용자 정보 수정"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 이메일 변경 시 중복 확인
    if user.email and user.email != db_user.email:
        existing_user = crud.get_user_by_email(db, email=user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    # 사용자 업데이트 전 현재 상태 확인
    was_inactive = not db_user.is_active
    
    # 사용자 정보 업데이트
    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user)
    
    # 사용자가 비활성화 -> 활성화로 변경되는 경우
    # 한번 비활성화된 멘토십은 계속 비활성화 상태 유지
    if was_inactive and updated_user.is_active:
        print(f"🔄 사용자 {user_id}가 활성화되었지만, 기존 비활성화된 멘토십은 유지됩니다.")
        # 멘토십 상태는 변경하지 않음 (비활성화 유지)
    
    # 사용자가 활성화 -> 비활성화로 변경되는 경우에만 멘토십도 비활성화
    elif not was_inactive and not updated_user.is_active:
        print(f"🔄 사용자 {user_id}가 비활성화되어 관련 멘토십도 비활성화합니다.")
        # 이 경우에는 관련 멘토십을 비활성화해야 함
        # (crud.py의 update_mentorship에서 자동으로 처리됨)
    
    return updated_user


@router.delete("/{user_id}/company/{company_id}/department/{department_id}")
async def delete_user_with_validation(
    user_id: int, 
    company_id: int, 
    department_id: int, 
    db: Session = Depends(get_db)
):
    """회사, 부서 정보 검증 후 사용자 삭제"""
    user, message = crud.delete_user_with_company_department(
        db=db, 
        user_id=user_id, 
        company_id=company_id, 
        department_id=department_id
    )
    
    if user is None:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 삭제 (기본 방식) - 멘토링 관계 확인 후 안전하게 삭제"""
    try:
        print(f"🗑️ 사용자 삭제 요청: user_id={user_id}")
        
        # 사용자 존재 확인
        db_user = crud.get_user(db, user_id=user_id)
        if db_user is None:
            print(f"❌ 사용자를 찾을 수 없음: user_id={user_id}")
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        print(f"✅ 삭제할 사용자 찾음: {db_user.email}")
        
        # 사용자 삭제 실행 (crud.py에서 트랜잭션 처리)
        deleted_user = crud.delete_user(db, user_id=user_id)
        
        if deleted_user:
            print(f"✅ 사용자 삭제 성공: {deleted_user.email}")
            return {"message": f"사용자 '{deleted_user.email}'가 성공적으로 삭제되었습니다"}
        else:
            print(f"❌ 사용자 삭제 실패: user_id={user_id}")
            raise HTTPException(status_code=500, detail="사용자 삭제 처리 중 오류가 발생했습니다")
            
    except ValueError as ve:
        # 멘토링 관계 확인 오류 (경고 메시지)
        error_msg = str(ve)
        print(f"⚠️ 삭제 차단: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        print(f"❌ 사용자 삭제 중 예상치 못한 예외: {str(e)}")
        import traceback
        print(f"❌ 스택 트레이스:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"사용자 삭제 중 시스템 오류가 발생했습니다: {str(e)}"
        )

class UserIds(BaseModel):
    user_ids: List[int]

@router.delete("/")
async def delete_multiple_users(user_ids_payload: UserIds, db: Session = Depends(get_db)):
    """다중 사용자 삭제 - 멘토링 관계 확인 후 안전하게 삭제"""
    user_ids = user_ids_payload.user_ids
    if not user_ids:
        raise HTTPException(status_code=400, detail="삭제할 사용자 ID가 없습니다.")

    success_count = 0
    error_count = 0
    errors = []
    deleted_users = []
    blocked_users = []  # 멘토링 관계로 인해 삭제가 차단된 사용자들

    print(f"🗑️ 다중 사용자 삭제 시작: {len(user_ids)}명")

    for user_id in user_ids:
        try:
            # 각 사용자별로 개별 트랜잭션 처리 (안정성 향상)
            deleted_user = crud.delete_user(db, user_id=user_id)
            if deleted_user:
                success_count += 1
                deleted_users.append(f"{deleted_user.email} (ID: {user_id})")
                print(f"  ✅ 사용자 삭제 성공: {deleted_user.email}")
            else:
                error_count += 1
                error_msg = f"User ID {user_id}: 삭제 처리 실패"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")
                
        except ValueError as ve:
            # 멘토링 관계로 인한 삭제 차단
            error_count += 1
            user_info = crud.get_user(db, user_id)
            user_email = user_info.email if user_info else f"ID:{user_id}"
            blocked_msg = f"{user_email}: 멘토링 관계가 있어 삭제할 수 없습니다"
            blocked_users.append(blocked_msg)
            errors.append(blocked_msg)
            print(f"  ⚠️ 삭제 차단: {blocked_msg}")
        except Exception as e:
            error_count += 1
            error_msg = f"User ID {user_id}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ 사용자 삭제 중 오류: {error_msg}")

    # 결과 정리
    result_message = f"총 {len(user_ids)}명 중 {success_count}명 삭제 성공"
    if error_count > 0:
        result_message += f", {error_count}명 실패"
    if blocked_users:
        result_message += f" (멘토링 관계로 {len(blocked_users)}명 차단됨)"
    
    print(f"🏁 다중 삭제 완료: {result_message}")

    response_data = {
        "message": result_message,
        "success_count": success_count,
        "error_count": error_count,
        "deleted_users": deleted_users,
        "errors": errors if errors else None
    }
    
    # 멘토링 관계가 있는 사용자들에 대한 추가 안내
    if blocked_users:
        response_data["warning"] = "일부 사용자는 멘토링 관계가 있어 삭제되지 않았습니다. 먼저 멘토링 관계를 종료하거나 비활성화를 고려해주세요."
        response_data["blocked_users"] = blocked_users

    if success_count == 0 and error_count > 0:
        raise HTTPException(
            status_code=400,  # 멘토링 관계 오류는 400으로 변경
            content=response_data
        )

    return response_data

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