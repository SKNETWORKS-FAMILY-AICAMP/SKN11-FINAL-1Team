from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("/", response_model=schemas.Company)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    """회사 생성"""
    # 중복 검사
    db_company = crud.get_company(db=db, company_id=company.company_id)
    if db_company:
        raise HTTPException(status_code=400, detail="이미 존재하는 사업자번호입니다.")
    
    return crud.create_company(db=db, company=company)

@router.get("/", response_model=List[schemas.Company])
def read_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """회사 목록 조회"""
    companies = crud.get_companies(db=db, skip=skip, limit=limit)
    return companies

@router.get("/{company_id}", response_model=schemas.Company)
def read_company(company_id: str, db: Session = Depends(get_db)):
    """회사 조회"""
    db_company = crud.get_company(db=db, company_id=company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    return db_company

@router.put("/{company_id}", response_model=schemas.Company)
def update_company(company_id: str, company: schemas.CompanyUpdate, db: Session = Depends(get_db)):
    """회사 수정"""
    db_company = crud.update_company(db=db, company_id=company_id, company=company)
    if db_company is None:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    return db_company

@router.delete("/{company_id}")
def delete_company(company_id: str, db: Session = Depends(get_db)):
    """회사 삭제"""
    db_company = crud.delete_company(db=db, company_id=company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    return {"message": "회사가 성공적으로 삭제되었습니다."}

@router.get("/{company_id}/departments", response_model=List[schemas.Department])
def read_company_departments(company_id: str, db: Session = Depends(get_db)):
    """회사 소속 부서 목록 조회"""
    departments = crud.get_departments_by_company(db=db, company_id=company_id)
    return departments

@router.get("/{company_id}/users", response_model=List[schemas.User])
def read_company_users(company_id: str, db: Session = Depends(get_db)):
    """회사 소속 사용자 목록 조회"""
    users = crud.get_users_by_company(db=db, company_id=company_id)
    return users 