from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("/", response_model=schemas.Company)
async def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    """새 회사 생성"""
    return crud.create_company(db=db, company=company)


@router.get("/", response_model=List[schemas.Company])
async def get_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """회사 목록 조회"""
    companies = crud.get_companies(db, skip=skip, limit=limit)
    return companies


@router.get("/{company_id}", response_model=schemas.Company)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """특정 회사 조회"""
    db_company = crud.get_company(db, company_id=company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다")
    return db_company


@router.put("/{company_id}", response_model=schemas.Company)
async def update_company(company_id: int, company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    """회사 정보 수정"""
    db_company = crud.get_company(db, company_id=company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다")
    return crud.update_company(db=db, company_id=company_id, company_update=company)


@router.delete("/{company_id}")
async def delete_company(company_id: int, db: Session = Depends(get_db)):
    """회사 삭제"""
    db_company = crud.get_company(db, company_id=company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다")
    
    crud.delete_company(db, company_id=company_id)
    return {"message": "회사가 성공적으로 삭제되었습니다"} 