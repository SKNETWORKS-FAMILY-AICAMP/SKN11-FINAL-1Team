from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
import models 
from database import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# 태스크 관리 (Template의 태스크들)
@router.post("/manage/", response_model=schemas.TaskManage)
async def create_task_manage(task: schemas.TaskManageCreate, db: Session = Depends(get_db)):
    """새 태스크 관리 생성"""
    return crud.create_task_manage(db=db, task=task)


@router.get("/manage/", response_model=List[schemas.TaskManage])
async def get_task_manages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """태스크 관리 목록 조회"""
    tasks = crud.get_task_manages(db, skip=skip, limit=limit)
    return tasks


@router.get("/manage/{task_id}", response_model=schemas.TaskManage)
async def get_task_manage(task_id: int, db: Session = Depends(get_db)):
    """특정 태스크 관리 조회"""
    db_task = crud.get_task_manage(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    return db_task


@router.put("/manage/{task_id}", response_model=schemas.TaskManage)
async def update_task_manage(task_id: int, task: schemas.TaskManageCreate, db: Session = Depends(get_db)):
    """태스크 관리 수정"""
    db_task = crud.get_task_manage(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    return crud.update_task_manage(db=db, task_id=task_id, task_update=task)


@router.delete("/manage/{task_id}")
async def delete_task_manage(task_id: int, db: Session = Depends(get_db)):
    """태스크 관리 삭제"""
    db_task = crud.get_task_manage(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    
    crud.delete_task_manage(db, task_id=task_id)
    return {"message": "태스크가 성공적으로 삭제되었습니다"}


# 태스크 할당 (사용자에게 할당된 태스크들)
@router.post("/assign/", response_model=schemas.TaskAssignResponse)
async def create_task_assign(task: schemas.TaskAssignCreate, db: Session = Depends(get_db)):
    """새 태스크 할당 생성"""
    # 사용자 존재 확인
    db_user = crud.get_user(db, user_id=task.user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 태스크 관리 존재 확인
    db_task_manage = crud.get_task_manage(db, task_id=task.task_manage_id)
    if db_task_manage is None:
        raise HTTPException(status_code=404, detail="관리 태스크를 찾을 수 없습니다")
    
    return crud.create_task_assign(db=db, task=task)


@router.get("/assign/", response_model=List[schemas.TaskAssign])
async def get_task_assigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """태스크 할당 목록 조회"""
    tasks = crud.get_task_assigns(db, skip=skip, limit=limit)
    return tasks

@router.get("/assigns", response_model=List[schemas.TaskAssignResponse])
async def get_task_assigns_plural(
    skip: int = 0,
    limit: int = 100,
    mentorship_id: int = None,
    status: str = None,
    priority: str = None,
    sort: str = "week",
    db: Session = Depends(get_db)
):
    """태스크 할당 목록 조회 (필터 및 정렬 지원)"""
    
    # 'all' 값은 필터링에서 제외
    if status == "all":
        status = None
    if priority == "all":
        priority = None

    tasks = crud.get_task_assigns_filtered(
        db,
        mentorship_id=mentorship_id,
        status=status,
        priority=priority,
        skip=skip,
        limit=limit
    )

    # 정렬
    if sort == "deadline":
        tasks.sort(key=lambda t: t.scheduled_end_date or "9999-12-31")
    else:
        tasks.sort(key=lambda t: t.week or 0)

    return tasks



@router.get("/assign/{task_id}", response_model=schemas.TaskAssignResponse)
async def get_task_assign(task_id: int, db: Session = Depends(get_db)):
    """특정 태스크 할당 조회"""
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    return db_task


@router.put("/assign/{task_id}", response_model=schemas.TaskAssignResponse)
async def update_task_assign(task_id: int, task: schemas.TaskAssignCreate, db: Session = Depends(get_db)):
    """태스크 할당 수정"""
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    return crud.update_task_assign(db=db, task_id=task_id, task_update=task)


@router.delete("/assign/{task_id}")
async def delete_task_assign(task_id: int, db: Session = Depends(get_db)):
    """태스크 할당 삭제"""
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    
    crud.delete_task_assign(db, task_id=task_id)
    return {"message": "할당된 태스크가 성공적으로 삭제되었습니다"}

# Task 상세 조회
@router.get("/assign/detail/{task_id}")
async def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    """특정 할당된 태스크의 상세정보와 메모를 반환"""
    task = crud.get_task_assign(db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다.")
    
    # 댓글(메모)도 가져오기
    memos = crud.get_task_memos(db, task_id=task_id) if hasattr(crud, "get_task_memos") else []

    return {
        "success": True,
        "task": {
            "task_assign_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "guideline": getattr(task, "guideline", ""),
            "status": task.status,
            "priority": task.priority,
            "scheduled_end_date": task.scheduled_end_date,
            "week": task.week,
            "order": task.order,
            "memos": [
                {
                    "user": memo.user_name if hasattr(memo, "user_name") else "🤖 리뷰 에이전트",
                    "comment": memo.comment,
                    "create_date": memo.create_date
                } for memo in memos
            ]
        }
    }


# Task 상태 업데이트
@router.post("/assign/update_status/{task_id}")
async def update_task_status_api(task_id: int, payload: dict = Body(...), db: Session = Depends(get_db)):
    print(f"DEBUG [update_task_status_api] task_id={task_id}, payload={payload}")
    """태스크 상태와 주요 필드를 업데이트"""
    status = payload.get("status")
    description = payload.get("description")
    guideline = payload.get("guideline")
    priority = payload.get("priority")
    scheduled_start_date = payload.get("scheduled_start_date")
    scheduled_end_date = payload.get("scheduled_end_date")

    # 태스크 조회
    task = crud.get_task_assign(db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다.")

    # CRUD 호출
    updated_task = crud.update_task_status(
        db,
        task_id=task_id,
        status=status,
        description=description,
        guideline=guideline,
        priority=priority,
        scheduled_start_date=scheduled_start_date,
        scheduled_end_date=scheduled_end_date
    )

    return {"success": True, "task_id": task_id, "updated_priority": updated_task.priority}




# Task 댓글 추가
@router.post("/assign/comment/{task_id}")
async def add_task_comment(task_id: int, payload: dict = Body(...), db: Session = Depends(get_db)):
    """태스크에 댓글(메모) 추가"""
    comment = payload.get("comment")
    if not comment:
        raise HTTPException(status_code=400, detail="댓글 내용이 없습니다.")
    
    crud.add_task_memo(db, task_id=task_id, comment=comment)  # crud 함수 필요
    return {"success": True}


@router.get("/assign/user/{user_id}", response_model=List[schemas.TaskAssignResponse])
async def get_user_tasks(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """특정 사용자의 할당된 태스크 목록 조회"""
    # 사용자 존재 확인
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    tasks = crud.get_task_assigns_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return tasks


@router.patch("/assign/{task_id}/status")
async def update_task_status(task_id: int, status: int, db: Session = Depends(get_db)):
    """태스크 할당 상태 업데이트"""
    valid_statuses = [0, 1, 2, 3]  # 예: 0=미시작, 1=진행중, 2=완료, 3=보류
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 상태입니다. 가능한 상태: {valid_statuses}")
    
    db_task = crud.get_task_assign(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="할당된 태스크를 찾을 수 없습니다")
    
    # 상태만 업데이트
    db_task.status = status
    db.commit()
    db.refresh(db_task)
    
    status_names = {0: "미시작", 1: "진행중", 2: "완료", 3: "보류"}
    return {"message": f"태스크 상태가 '{status_names.get(status, status)}'로 업데이트되었습니다"}


# 하위 태스크 (TaskAssign의 서브태스크)
@router.post("/subtask/", response_model=schemas.TaskAssignResponse)
async def create_subtask(subtask: schemas.TaskAssignCreate, db: Session = Depends(get_db)):
    """새 하위 태스크 생성 (TaskAssign의 서브태스크)"""
    # 부모 태스크 할당 존재 확인
    if subtask.parent_id:
        db_parent_task = crud.get_task_assign(db, task_id=subtask.parent_id)
        if db_parent_task is None:
            raise HTTPException(status_code=404, detail="부모 태스크를 찾을 수 없습니다")
    
    # 멘토십 존재 확인
    db_mentorship = crud.get_mentorship(db, mentorship_id=subtask.mentorship_id)
    if db_mentorship is None:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    
    return crud.create_task_assign(db=db, task=subtask)


# 멘토링과 관련된 태스크 기능
@router.post("/mentorship/", response_model=schemas.Mentorship)
async def create_mentorship(mentorship: schemas.MentorshipCreate, db: Session = Depends(get_db)):
    """새 멘토링 관계 생성"""
    # 멘토와 멘티 존재 확인
    mentor = crud.get_user(db, user_id=mentorship.mentor_id)
    mentee = crud.get_user(db, user_id=mentorship.mentee_id)
    
    if mentor is None or mentor.role != "mentor":
        raise HTTPException(status_code=404, detail="멘토를 찾을 수 없습니다")
    
    if mentee is None or mentee.role != "mentee":
        raise HTTPException(status_code=404, detail="멘티를 찾을 수 없습니다")
    
    return crud.create_mentorship(db=db, mentorship=mentorship)


@router.get("/mentorship/", response_model=List[schemas.MentorshipResponse])
async def get_mentorships(mentor_id: int = None, mentee_id: int = None, search: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """멘토링 관계 목록 조회 with task counts"""
    print(f"[DEBUG] get_mentorships called with mentor_id={mentor_id}, mentee_id={mentee_id}, search={search}, skip={skip}, limit={limit}")
    
    # 필터링된 멘토십 조회
    if mentor_id or mentee_id or search:
        mentorships = crud.get_mentorships_with_filters(db, mentor_id=mentor_id, mentee_id=mentee_id, search=search, skip=skip, limit=limit)
    else:
        mentorships = crud.get_mentorships(db, skip=skip, limit=limit)
    
    print(f"[DEBUG] Found {len(mentorships)} mentorships")
    
    response_list = []
    for i, m in enumerate(mentorships):
        print(f"[DEBUG] Processing mentorship {i+1}/{len(mentorships)}: ID={m.mentorship_id}")
        
        counts = crud.get_task_counts_by_mentorship(db, m.mentorship_id)
        print(f"[DEBUG] Counts for mentorship {m.mentorship_id}: {counts}")
        
        mentee_name = f"{m.mentee.first_name} {m.mentee.last_name}" if m.mentee else ""
        mentor_name = f"{m.mentor.first_name} {m.mentor.last_name}" if m.mentor else ""
        
        total_tasks = counts.get("total_tasks", 0)
        completed_tasks = counts.get("completed_tasks", 0)
        
        print(f"[DEBUG] Final values - total_tasks: {total_tasks}, completed_tasks: {completed_tasks}")
        
        mentorship_response = schemas.MentorshipResponse(
            id=m.mentorship_id,
            mentor_id=m.mentor_id,
            mentee_id=m.mentee_id,
            curriculum_id=None,
            start_date=m.start_date,
            end_date=m.end_date,
            is_active=m.is_active,
            status="active" if m.is_active else "inactive",
            created_at=None,
            updated_at=None,
            mentee_name=mentee_name,
            mentor_name=mentor_name,
            curriculum_title=m.curriculum_title or "",
            total_weeks=m.total_weeks or 0,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            tags=[]
        )
        
        print(f"[DEBUG] Created response object - total_tasks: {mentorship_response.total_tasks}, completed_tasks: {mentorship_response.completed_tasks}")
        response_list.append(mentorship_response)
    
    print(f"[DEBUG] Returning {len(response_list)} mentorship responses")
    return response_list


@router.get("/mentorship/{mentorship_id}/task_counts", response_model=dict)
async def get_task_counts(mentorship_id: int, db: Session = Depends(get_db)):
    """특정 멘토십의 태스크 카운트 조회"""
    print(f"[DEBUG] get_task_counts called for mentorship_id: {mentorship_id}")
    
    # 멘토십 존재 확인
    mentorship = crud.get_mentorship(db, mentorship_id)
    if not mentorship:
        raise HTTPException(status_code=404, detail="멘토십을 찾을 수 없습니다")
    
    counts = crud.get_task_counts_by_mentorship(db, mentorship_id)
    print(f"[DEBUG] Task counts result: {counts}")
    
    return counts


@router.get("/test/mentorship/{mentor_id}")
async def test_mentorship_response(mentor_id: int, db: Session = Depends(get_db)):
    """테스트용: 멘토십 응답 데이터 확인"""
    print(f"[TEST] Testing mentorship response for mentor_id: {mentor_id}")
    
    # 직접 mentorships_with_filters 호출
    mentorships = crud.get_mentorships_with_filters(db, mentor_id=mentor_id)
    print(f"[TEST] Found {len(mentorships)} mentorships from crud.get_mentorships_with_filters")
    
    if not mentorships:
        return {"message": "No mentorships found", "mentorships": []}
    
    test_results = []
    for m in mentorships:
        print(f"[TEST] Processing mentorship {m.mentorship_id}")
        print(f"[TEST] Mentorship data: mentor_id={m.mentor_id}, mentee_id={m.mentee_id}, is_active={m.is_active}")
        
        # 태스크 카운트 확인
        counts = crud.get_task_counts_by_mentorship(db, m.mentorship_id)
        print(f"[TEST] Task counts: {counts}")
        
        # 사용자 정보 확인
        mentee = crud.get_user(db, m.mentee_id) if m.mentee_id else None
        mentor = crud.get_user(db, m.mentor_id) if m.mentor_id else None
        
        mentee_name = f"{mentee.first_name} {mentee.last_name}" if mentee else "Unknown"
        mentor_name = f"{mentor.first_name} {mentor.last_name}" if mentor else "Unknown"
        
        print(f"[TEST] Names - mentee: {mentee_name}, mentor: {mentor_name}")
        
        test_result = {
            "mentorship_id": m.mentorship_id,
            "mentor_id": m.mentor_id,
            "mentee_id": m.mentee_id,
            "mentee_name": mentee_name,
            "mentor_name": mentor_name,
            "curriculum_title": m.curriculum_title,
            "total_weeks": m.total_weeks,
            "is_active": m.is_active,
            "start_date": str(m.start_date) if m.start_date else None,
            "end_date": str(m.end_date) if m.end_date else None,
            "total_tasks": counts.get("total_tasks", 0),
            "completed_tasks": counts.get("completed_tasks", 0),
            "raw_counts": counts
        }
        
        print(f"[TEST] Final test result: {test_result}")
        test_results.append(test_result)
    
    return {"mentorships": test_results}


@router.get("/debug/task_statuses")
async def debug_task_statuses_endpoint(mentorship_id: int = None, db: Session = Depends(get_db)):
    """디버깅용: 실제 DB의 태스크 상태값들을 확인"""
    print(f"[DEBUG] debug_task_statuses_endpoint called with mentorship_id: {mentorship_id}")
    
    status_counts = crud.debug_task_statuses(db, mentorship_id)
    
    return {
        "message": "Check server console for detailed status information",
        "status_counts": [
            {
                "mentorship_id": m_id,
                "status": status,
                "count": count
            }
            for status, m_id, count in status_counts
        ]
    }


@router.post("/generate_draft/", response_class=PlainTextResponse)
async def generate_draft(input_data: dict):
    """
    Generate curriculum draft based on input data.
    """
    try:
        import sys
        import os
        
        # 프로젝트 루트를 Python 경로에 추가
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        print(f"[DEBUG] Python path: {sys.path[:3]}")
        print(f"[DEBUG] Project root: {project_root}")
        print(f"[DEBUG] Input data: {input_data}")
        
        from agent_test.task_agent import generate_curriculum_draft, CurriculumInput

        # 기본값 설정
        curriculum_input = CurriculumInput(
            curriculum_title=input_data.get('title', ''),
            curriculum_description=input_data.get('description', ''),
        )
        
        print(f"[DEBUG] Curriculum input: {curriculum_input}")
        
        # OpenAI API 키 확인
        import os
        from dotenv import load_dotenv
        load_dotenv()
        openai_key = os.getenv("OPENAI_API_KEY")
        print(f"[DEBUG] OpenAI API key exists: {bool(openai_key)}")
        
        draft = generate_curriculum_draft(curriculum_input)
        print(f"[DEBUG] Generated draft: {draft[:100]}...")
        return draft
        
    except ImportError as e:
        error_msg = f"Import error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"오류: {error_msg}"
    except Exception as e:
        import traceback
        error_msg = f"Error generating draft: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Traceback: {traceback_str}")
        return f"오류: {error_msg}\n상세: {traceback_str}"


@router.post("/generate_tasks_from_draft/")
async def generate_tasks_from_draft(input_data: dict):
    """
    Generate tasks based on the provided draft using LangGraph workflow.
    """
    try:
        import sys
        import os
        
        # 프로젝트 루트를 Python 경로에 추가
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        print(f"[DEBUG] Generating tasks with LangGraph - Input data: {input_data}")
        
        from agent_test.task_agent import build_langgraph, CurriculumInput

        # 기본값 설정
        curriculum_input = CurriculumInput(
            curriculum_title=input_data.get('title', ''),
            curriculum_description=input_data.get('description', ''),
        )
        
        print(f"[DEBUG] Generating tasks for: {curriculum_input.curriculum_title}")
        
        # LangGraph 워크플로우 빌드 및 실행
        try:
            workflow = build_langgraph()
            app = workflow.compile()
            
            print(f"[DEBUG] Starting LangGraph workflow execution...")
            result = app.invoke({"input_data": curriculum_input.__dict__})
            
            if not result or "tasks" not in result:
                raise ValueError("LangGraph workflow did not return expected task structure")
            
            all_tasks = result["tasks"]
            
            if not isinstance(all_tasks, list):
                raise ValueError("Tasks should be a list")
            
            print(f"[DEBUG] Generated {len(all_tasks)} tasks using LangGraph")
            return {"tasks": all_tasks, "success": True}
            
        except Exception as workflow_error:
            print(f"[ERROR] LangGraph workflow error: {str(workflow_error)}")
            raise workflow_error
        
    except ImportError as e:
        error_msg = f"필요한 모듈을 가져올 수 없습니다: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg, "type": "import_error", "success": False}
    except FileNotFoundError as e:
        error_msg = f"필요한 파일을 찾을 수 없습니다: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg, "type": "file_error", "success": False}
    except ValueError as e:
        error_msg = f"입력 데이터 또는 처리 과정에서 오류가 발생했습니다: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg, "type": "value_error", "success": False}
    except Exception as e:
        import traceback
        error_msg = f"Task 생성 중 예상치 못한 오류가 발생했습니다: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Traceback: {traceback_str}")
        return {"error": error_msg, "traceback": traceback_str, "type": "general_error", "success": False}