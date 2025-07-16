#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Onboarding Quest API",
    version="1.0.0",
    description="Django와 연동된 Onboarding Quest API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델들
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "mentee"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

class MentorshipCreate(BaseModel):
    mentor_id: int
    mentee_id: int
    start_date: str
    end_date: str

class MentorshipResponse(BaseModel):
    id: int
    mentor_id: int
    mentee_id: int
    start_date: str
    end_date: str
    status: str

class TaskCreate(BaseModel):
    title: str
    description: str
    assigned_to: int
    due_date: str

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    assigned_to: int
    due_date: str
    status: str

# 메모리 저장소 (실제로는 데이터베이스)
users_db = []
mentorships_db = []
tasks_db = []

# 기본 엔드포인트
@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 실행 중입니다!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "서버가 정상적으로 실행 중입니다."}

# 사용자 API
@app.post("/api/v1/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    """사용자 생성"""
    user_id = len(users_db) + 1
    new_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": True
    }
    users_db.append(new_user)
    return new_user

@app.get("/api/v1/users/", response_model=List[UserResponse])
def get_users():
    """사용자 목록 조회"""
    return users_db

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """사용자 상세 조회"""
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

@app.put("/api/v1/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate):
    """사용자 수정"""
    for i, existing_user in enumerate(users_db):
        if existing_user["id"] == user_id:
            users_db[i].update({
                "username": user.username,
                "email": user.email,
                "role": user.role
            })
            return users_db[i]
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

@app.delete("/api/v1/users/{user_id}")
def delete_user(user_id: int):
    """사용자 삭제"""
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            del users_db[i]
            return {"message": "사용자가 삭제되었습니다."}
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

# 멘토십 API
@app.post("/api/v1/mentorships/", response_model=MentorshipResponse)
def create_mentorship(mentorship: MentorshipCreate):
    """멘토십 생성"""
    mentorship_id = len(mentorships_db) + 1
    new_mentorship = {
        "id": mentorship_id,
        "mentor_id": mentorship.mentor_id,
        "mentee_id": mentorship.mentee_id,
        "start_date": mentorship.start_date,
        "end_date": mentorship.end_date,
        "status": "active"
    }
    mentorships_db.append(new_mentorship)
    return new_mentorship

@app.get("/api/v1/mentorships/", response_model=List[MentorshipResponse])
def get_mentorships():
    """멘토십 목록 조회"""
    return mentorships_db

@app.get("/api/v1/mentorships/{mentorship_id}", response_model=MentorshipResponse)
def get_mentorship(mentorship_id: int):
    """멘토십 상세 조회"""
    for mentorship in mentorships_db:
        if mentorship["id"] == mentorship_id:
            return mentorship
    raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다.")

# 과제 API
@app.post("/api/v1/tasks/", response_model=TaskResponse)
def create_task(task: TaskCreate):
    """과제 생성"""
    task_id = len(tasks_db) + 1
    new_task = {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date,
        "status": "pending"
    }
    tasks_db.append(new_task)
    return new_task

@app.get("/api/v1/tasks/", response_model=List[TaskResponse])
def get_tasks():
    """과제 목록 조회"""
    return tasks_db

@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    """과제 상세 조회"""
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")

@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskCreate):
    """과제 수정"""
    for i, existing_task in enumerate(tasks_db):
        if existing_task["id"] == task_id:
            tasks_db[i].update({
                "title": task.title,
                "description": task.description,
                "assigned_to": task.assigned_to,
                "due_date": task.due_date
            })
            return tasks_db[i]
    raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")

@app.delete("/api/v1/tasks/{task_id}")
def delete_task(task_id: int):
    """과제 삭제"""
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            del tasks_db[i]
            return {"message": "과제가 삭제되었습니다."}
    raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다.")

if __name__ == "__main__":
    uvicorn.run(
        "main_with_apis:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    ) 