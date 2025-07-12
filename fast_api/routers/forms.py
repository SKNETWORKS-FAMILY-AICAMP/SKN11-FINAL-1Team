from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
import models
from database import get_db
import aiofiles
import os
from datetime import datetime
import shutil

router = APIRouter(prefix="/forms", tags=["forms"])
templates = Jinja2Templates(directory="templates")

# 정적 파일 업로드 디렉토리
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def forms_home(request: Request):
    """폼 페이지 홈"""
    return templates.TemplateResponse("forms/index.html", {"request": request})


# 회사 관리 폼
@router.get("/companies", response_class=HTMLResponse)
async def company_form(request: Request, db: Session = Depends(get_db)):
    """회사 생성 폼"""
    companies = crud.get_companies(db)
    return templates.TemplateResponse("forms/company_form.html", {
        "request": request,
        "companies": companies
    })


@router.post("/companies")
async def create_company_form(
    request: Request,
    company_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """회사 생성 폼 처리"""
    try:
        company_data = schemas.CompanyCreate(company_name=company_name)
        company = crud.create_company(db=db, company=company_data)
        return RedirectResponse(url="/forms/companies?success=true", status_code=303)
    except Exception as e:
        companies = crud.get_companies(db)
        return templates.TemplateResponse("forms/company_form.html", {
            "request": request,
            "companies": companies,
            "error": str(e)
        })


# 부서 관리 폼
@router.get("/departments", response_class=HTMLResponse)
async def department_form(request: Request, db: Session = Depends(get_db)):
    """부서 생성 폼"""
    companies = crud.get_companies(db)
    departments = crud.get_departments(db)
    return templates.TemplateResponse("forms/department_form.html", {
        "request": request,
        "companies": companies,
        "departments": departments
    })


@router.post("/departments")
async def create_department_form(
    request: Request,
    department_name: str = Form(...),
    description: Optional[str] = Form(None),
    company_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """부서 생성 폼 처리"""
    try:
        department_data = schemas.DepartmentCreate(
            department_name=department_name,
            description=description,
            company_id=company_id
        )
        department = crud.create_department(db=db, department=department_data)
        return RedirectResponse(url="/forms/departments?success=true", status_code=303)
    except Exception as e:
        companies = crud.get_companies(db)
        departments = crud.get_departments(db)
        return templates.TemplateResponse("forms/department_form.html", {
            "request": request,
            "companies": companies,
            "departments": departments,
            "error": str(e)
        })


# 사용자 관리 폼
@router.get("/users", response_class=HTMLResponse)
async def user_form(request: Request, db: Session = Depends(get_db)):
    """사용자 생성 폼"""
    companies = crud.get_companies(db)
    departments = crud.get_departments(db)
    users = crud.get_users(db)
    return templates.TemplateResponse("forms/user_form.html", {
        "request": request,
        "companies": companies,
        "departments": departments,
        "users": users
    })


@router.post("/users")
async def create_user_form(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    job_part: str = Form(...),
    position: int = Form(...),
    join_date: str = Form(...),
    skill: Optional[str] = Form(None),
    role: str = Form(...),
    exp: Optional[int] = Form(0),
    level: Optional[int] = Form(1),
    admin: Optional[bool] = Form(False),
    department_id: int = Form(...),
    company_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """사용자 생성 폼 처리"""
    try:
        from datetime import datetime
        join_date_obj = datetime.strptime(join_date, "%Y-%m-%d").date()
        
        user_data = schemas.UserCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            job_part=job_part,
            position=position,
            join_date=join_date_obj,
            skill=skill,
            role=role,
            exp=exp,
            level=level,
            admin=admin,
            department_id=department_id,
            company_id=company_id
        )
        user = crud.create_user(db=db, user=user_data)
        return RedirectResponse(url="/forms/users?success=true", status_code=303)
    except Exception as e:
        companies = crud.get_companies(db)
        departments = crud.get_departments(db)
        users = crud.get_users(db)
        return templates.TemplateResponse("forms/user_form.html", {
            "request": request,
            "companies": companies,
            "departments": departments,
            "users": users,
            "error": str(e)
        })


# 템플릿 관리 폼
@router.get("/templates", response_class=HTMLResponse)
async def template_form(request: Request, db: Session = Depends(get_db)):
    """템플릿 생성 폼"""
    departments = crud.get_departments(db)
    templates_list = crud.get_templates(db)
    return templates.TemplateResponse("forms/template_form.html", {
        "request": request,
        "departments": departments,
        "templates_list": templates_list
    })


@router.post("/templates")
async def create_template_form(
    request: Request,
    template_title: str = Form(...),
    template_description: Optional[str] = Form(None),
    department_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """템플릿 생성 폼 처리"""
    try:
        template_data = schemas.TemplateCreate(
            template_title=template_title,
            template_description=template_description,
            department_id=department_id
        )
        template = crud.create_template(db=db, template=template_data)
        return RedirectResponse(url="/forms/templates?success=true", status_code=303)
    except Exception as e:
        departments = crud.get_departments(db)
        templates_list = crud.get_templates(db)
        return templates.TemplateResponse("forms/template_form.html", {
            "request": request,
            "departments": departments,
            "templates_list": templates_list,
            "error": str(e)
        })


# 태스크 관리 폼
@router.get("/tasks", response_class=HTMLResponse)
async def task_form(request: Request, db: Session = Depends(get_db)):
    """태스크 생성 폼"""
    templates_list = crud.get_templates(db)
    tasks = crud.get_task_manages(db)
    return templates.TemplateResponse("forms/task_form.html", {
        "request": request,
        "templates_list": templates_list,
        "tasks": tasks
    })


@router.post("/tasks")
async def create_task_form(
    request: Request,
    title: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    difficulty: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    exp: int = Form(...),
    order: Optional[int] = Form(None),
    template_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """태스크 생성 폼 처리"""
    try:
        from datetime import datetime
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        task_data = schemas.TaskManageCreate(
            title=title,
            start_date=start_date_obj,
            end_date=end_date_obj,
            difficulty=difficulty,
            description=description,
            exp=exp,
            order=order,
            template_id=template_id
        )
        task = crud.create_task_manage(db=db, task=task_data)
        return RedirectResponse(url="/forms/tasks?success=true", status_code=303)
    except Exception as e:
        templates_list = crud.get_templates(db)
        tasks = crud.get_task_manages(db)
        return templates.TemplateResponse("forms/task_form.html", {
            "request": request,
            "templates_list": templates_list,
            "tasks": tasks,
            "error": str(e)
        })


# 파일 업로드 폼
@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    """파일 업로드 폼"""
    return templates.TemplateResponse("forms/upload_form.html", {"request": request})


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """파일 업로드 처리"""
    try:
        # 파일 확장자 검증
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"허용되지 않는 파일 형식입니다. 허용되는 형식: {', '.join(allowed_extensions)}"
            )
        
        # 파일 크기 검증 (10MB 제한)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="파일 크기가 너무 큽니다. 최대 10MB까지 업로드 가능합니다."
            )
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        upload_response = {
            "filename": filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": file_size,
            "content_type": file.content_type,
            "upload_time": datetime.now(),
            "description": description
        }
        
        return templates.TemplateResponse("forms/upload_success.html", {
            "request": request,
            "upload_info": upload_response
        })
        
    except Exception as e:
        return templates.TemplateResponse("forms/upload_form.html", {
            "request": request,
            "error": str(e)
        })


# 업로드된 파일 목록
@router.get("/uploads", response_class=HTMLResponse)
async def uploaded_files(request: Request):
    """업로드된 파일 목록"""
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "path": file_path
                    })
        
        return templates.TemplateResponse("forms/uploaded_files.html", {
            "request": request,
            "files": files
        })
    except Exception as e:
        return templates.TemplateResponse("forms/uploaded_files.html", {
            "request": request,
            "files": [],
            "error": str(e)
        }) 