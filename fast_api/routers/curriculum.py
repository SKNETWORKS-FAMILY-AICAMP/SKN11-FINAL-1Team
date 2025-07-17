from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


@router.post("/", response_model=schemas.Curriculum)
async def create_curriculum(curriculum: schemas.CurriculumCreate, db: Session = Depends(get_db)):
    """새 커리큘럼 생성"""
    if curriculum.department_id:
        # 부서 존재 확인
        db_department = crud.get_department(db, department_id=curriculum.department_id)
        if db_department is None:
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    return crud.create_curriculum(db=db, curriculum=curriculum)


@router.get("/", response_model=List[schemas.Curriculum])
async def get_curricula(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """커리큘럼 목록 조회"""
    curricula = crud.get_curricula(db, skip=skip, limit=limit)
    return curricula


@router.get("/{curriculum_id}", response_model=schemas.Curriculum)
async def get_curriculum(curriculum_id: int, db: Session = Depends(get_db)):
    """특정 커리큘럼 조회"""
    db_curriculum = crud.get_curriculum(db, curriculum_id=curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다")
    return db_curriculum


@router.put("/{curriculum_id}", response_model=schemas.Curriculum)
async def update_curriculum(curriculum_id: int, curriculum: schemas.CurriculumCreate, db: Session = Depends(get_db)):
    """커리큘럼 정보 수정"""
    db_curriculum = crud.get_curriculum(db, curriculum_id=curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다")
    return crud.update_curriculum(db=db, curriculum_id=curriculum_id, curriculum_update=curriculum)


@router.delete("/{curriculum_id}")
async def delete_curriculum(curriculum_id: int, db: Session = Depends(get_db)):
    """커리큘럼 삭제"""
    db_curriculum = crud.get_curriculum(db, curriculum_id=curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다")
    
    crud.delete_curriculum(db, curriculum_id=curriculum_id)
    return {"message": "커리큘럼이 성공적으로 삭제되었습니다"}


@router.get("/department/{department_id}", response_model=List[schemas.Curriculum])
async def get_curricula_by_department(department_id: int, db: Session = Depends(get_db)):
    """부서별 커리큘럼 조회"""
    db_department = crud.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    
    return crud.get_curricula_by_department(db, department_id=department_id)


@router.get("/common/", response_model=List[schemas.Curriculum])
async def get_common_curricula(db: Session = Depends(get_db)):
    """공용 커리큘럼 조회"""
    return crud.get_common_curricula(db)
