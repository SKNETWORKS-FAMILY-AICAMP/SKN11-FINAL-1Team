import re
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import crud
import schemas
from database import get_db
import logging
import time
import sys
import os
import html  # 상단에 추가
from models import Docs  # 상단에 추가

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
#     handlers=[logging.StreamHandler()]
# )

# logger = logging.getLogger("chat_logger")

# chat.py 제일 상단에 (import 아래에 바로 삽입)

import logging

# 1. 기존 루트 로거 비활성화
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 2. 사용자 정의 로거만 활성화
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# 3. Chat 전용 로거 생성
logger = logging.getLogger("chat_logger")

# 4. SQLAlchemy의 엔진 로거 끄기
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)



# RAG 시스템 전역 변수
graph = None
client = None
COLLECTION_NAME = None
RAG_AVAILABLE = False

def initialize_rag_system():
    """RAG 시스템 초기화"""
    global graph, client, COLLECTION_NAME, RAG_AVAILABLE
    
    # 절대 경로로 Django 프로젝트 경로 찾기
    current_file = os.path.abspath(__file__)
    fast_api_dir = os.path.dirname(os.path.dirname(current_file))  # fast_api 디렉토리
    project_root = os.path.dirname(fast_api_dir)  # final_prj 디렉토리
    django_rag_path = os.path.join(project_root, "django_prj", "onboarding_quest")
    
    logging.info(f"RAG 시스템 초기화 시도 - 경로: {django_rag_path}")
    
    if django_rag_path not in sys.path:
        sys.path.insert(0, django_rag_path)
    
    try:
        # 동적 import
        rag_module = __import__('rag_agent_graph_db_v3_finaltemp_v2')
        graph = getattr(rag_module, 'graph')
        client = getattr(rag_module, 'client')
        COLLECTION_NAME = getattr(rag_module, 'COLLECTION_NAME')
        
        RAG_AVAILABLE = True
        logging.info("✅ RAG 시스템 초기화 성공")
        
    except Exception as e:
        logging.warning(f"⚠️ RAG 시스템 초기화 실패: {e}")
        RAG_AVAILABLE = False

# 초기화 시도
initialize_rag_system()

# # 로깅 설정
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# RAG 관련 Pydantic 모델
# class RagChatRequest(BaseModel):
#     question: str
#     session_id: Optional[int] = None
#     user_id: int
#     department_id: int

class RagChatRequest(BaseModel):
    question: str
    html_message: Optional[str] = None  # ✅ 추가
    session_id: Optional[int] = None
    user_id: int
    department_id: int
    doc_filter: Optional[List[str]] = []  # ✅ 추가됨



class RagChatResponse(BaseModel):
    answer: str
    session_id: int
    contexts: List[str] = []
    summary: Optional[str] = None
    used_rag: bool = False
    success: bool = True


# ChatSession 관리
@router.post("/session/", response_model=schemas.ChatSession)
async def create_chat_session(session: schemas.ChatSessionCreate, db: Session = Depends(get_db)):
    """새 채팅 세션 생성"""
    # 사용자 존재 확인
    db_user = crud.get_user(db, user_id=session.user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return crud.create_chat_session(db=db, chat_session=session)


@router.get("/session/{session_id}", response_model=schemas.ChatSession)
async def get_chat_session(session_id: int, db: Session = Depends(get_db)):
    """특정 채팅 세션 조회"""
    db_session = crud.get_chat_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
    return db_session


@router.get("/session/user/{user_id}", response_model=List[schemas.ChatSession])
async def get_chat_sessions_by_user(user_id: int, db: Session = Depends(get_db)):
    """사용자별 채팅 세션 조회"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return crud.get_chat_sessions_by_user(db, user_id=user_id)


@router.put("/session/{session_id}", response_model=schemas.ChatSession)
async def update_chat_session(session_id: int, session: schemas.ChatSessionCreate, db: Session = Depends(get_db)):
    """채팅 세션 정보 수정"""
    db_session = crud.get_chat_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
    return crud.update_chat_session(db=db, session_id=session_id, session_update=session)


@router.delete("/session/{session_id}")
async def delete_chat_session(session_id: int, db: Session = Depends(get_db)):
    """채팅 세션 삭제"""
    db_session = crud.get_chat_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
    
    crud.delete_chat_session(db, session_id=session_id)
    return {"message": "채팅 세션이 성공적으로 삭제되었습니다"}


# ChatMessage 관리
@router.post("/message/", response_model=schemas.ChatMessage)
async def create_chat_message(message: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
    """새 채팅 메시지 생성"""
    # 채팅 세션 존재 확인
    db_session = crud.get_chat_session(db, session_id=message.session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
    
    return crud.create_chat_message(db=db, chat_message=message)


@router.get("/message/{message_id}", response_model=schemas.ChatMessage)
async def get_chat_message(message_id: int, db: Session = Depends(get_db)):
    """특정 채팅 메시지 조회"""
    db_message = crud.get_chat_message(db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="채팅 메시지를 찾을 수 없습니다")
    return db_message


@router.get("/message/session/{session_id}", response_model=List[schemas.ChatMessage])
async def get_chat_messages_by_session(session_id: int, db: Session = Depends(get_db)):
    """세션별 채팅 메시지 조회"""
    db_session = crud.get_chat_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
    
    return crud.get_chat_messages_by_session(db, session_id=session_id)


@router.delete("/message/{message_id}")
async def delete_chat_message(message_id: int, db: Session = Depends(get_db)):
    """채팅 메시지 삭제"""
    db_message = crud.get_chat_message(db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="채팅 메시지를 찾을 수 없습니다")
    
    crud.delete_chat_message(db, message_id=message_id)
    return {"message": "채팅 메시지가 성공적으로 삭제되었습니다"}


# RAG 기반 채팅 엔드포인트
@router.post("/rag", response_model=RagChatResponse)
async def chat_with_rag(request: RagChatRequest, db: Session = Depends(get_db)):
    """RAG 기반 챗봇 응답 생성"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=500, detail="RAG 시스템이 로드되지 않았습니다.")
    
    try:
        logger.info(f"🚨 프론트에서 받은 doc_filter: {request.doc_filter}")

        start_time = time.time()
        logger.info(f"RAG 요청 수신: {request.question[:50]}...")
        
        # 사용자 검증
        user = crud.get_user_by_id(db, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 세션 ID가 없으면 새로 생성
        if not request.session_id:
            session = crud.create_chat_session(db, schemas.ChatSessionCreate(
                user_id=request.user_id,
                summary="새 대화"
            ))
            session_id = session.session_id
            logger.info(f"새 세션 생성: {session_id}")
        else:
            session_id = request.session_id
            # 세션 존재 여부 확인
            session = crud.get_chat_session(db, session_id)
            if not session or session.user_id != request.user_id:
                raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 사용자 메시지 저장
        crud.create_chat_message(db, schemas.ChatMessageCreate(
            session_id=session_id,
            # message_text=request.question
            message_text=request.html_message or request.question,
            message_type="user"
        ))
        
        # 사용자 히스토리 로드 (최근 10개)
        messages = crud.get_chat_messages(db, session_id, limit=10)
        
        history = []
        buffer = {}
        for msg in messages:
            if msg.message_type == "user":
                buffer["user"] = msg.message_text
            elif msg.message_type == "bot":
                buffer["bot"] = msg.message_text
            if "user" in buffer and "bot" in buffer:
                history.append(f"Q: {buffer['user']}\nA: {buffer['bot']}")
                buffer = {}
        
        # 초기 상태 설정
        # state = {
        #     "question": request.question,
        #     "chat_history": history,
        #     "rewrite_count": 0,
        #     "session_id": str(session_id),
        #     "user_department_id": request.department_id
        # }
        state = {
    "question": request.question,
    "chat_history": history,
    "rewrite_count": 0,
    "session_id": str(session_id),
    "user_department_id": request.department_id,
    "doc_filter": request.doc_filter  # ✅ 추가됨
}
        
        # LangGraph 실행
        logger.info("LangGraph 실행 시작...")
        result = graph.invoke(state)
        
        used_rag = bool(result.get("contexts"))
        logger.info(f"[RAG 여부] {'🧾 사용함' if used_rag else '💬 사용 안 함'} - 질문: {request.question}")
        
        # 봇 응답 저장
        answer = result["answer"]
        crud.create_chat_message(db, schemas.ChatMessageCreate(
            session_id=session_id,
            message_text=answer,
            message_type="bot"
        ))
        
        logger.info(f"RAG 응답 생성 완료: {answer[:50]}...")
        
        # 응답 시간 측정
        elapsed = time.time() - start_time
        logger.info(f"⏱️ 응답 생성 시간: {elapsed:.2f}초 - 질문: {request.question}")
        
        return RagChatResponse(
            answer=answer,
            session_id=session_id,
            contexts=result.get("contexts", []),
            summary=result.get("summary"),
            used_rag=used_rag,
            success=True
        )
        
    except Exception as e:
        logger.error(f"RAG 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG 처리 중 오류 발생: {str(e)}")

@router.post("/session/create")
async def create_new_session(user_id: int = Form(...), db: Session = Depends(get_db)):
    """새 채팅 세션 생성"""
    try:
        # 사용자 검증
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 새 세션 생성
        session = crud.create_chat_session(db, schemas.ChatSessionCreate(
            user_id=user_id,
            summary="새 대화"
        ))
        
        # 환영 메시지 자동 저장
        crud.create_chat_message(db, schemas.ChatMessageCreate(
            session_id=session.session_id,
            message_text="어서오세요. 무엇을 도와드릴까요?",
            message_type="bot"
        ))
        
        logger.info(f"새 세션 생성: {session.session_id}")
        return {
            "success": True,
            "session_id": session.session_id,
            "summary": "새 대화",
            "preview": ""
        }
    except Exception as e:
        logger.error(f"세션 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/delete")
async def delete_chat_session_rag(
    session_id: int = Form(...), 
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """채팅 세션 삭제 (비활성화)"""
    try:
        # 세션 소유권 확인
        session = crud.get_chat_session(db, session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        # 세션 및 메시지 비활성화
        crud.update_chat_session(db, session_id, schemas.ChatSessionCreate(
            user_id=user_id,
            summary=session.summary,
            is_active=False
        ))
        
        # 메시지들 비활성화 (직접 쿼리 사용)
        from models import ChatMessage
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).update({"is_active": False})
        db.commit()
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{user_id}")
async def get_user_sessions_rag(user_id: int, db: Session = Depends(get_db)):
    """사용자의 채팅 세션 목록 조회"""
    try:
        # 사용자 검증
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 활성 세션 조회
        sessions = crud.get_user_chat_sessions(db, user_id)
        
        result = []
        for session in sessions:
            # 첫 번째 사용자 메시지 조회
            messages = crud.get_chat_messages(db, session.session_id, limit=2)
            first_user_message = None
            for msg in messages:
                if msg.message_type == "user":
                    first_user_message = msg
                    break
            
            # preview = first_user_message.message_text if first_user_message else ""
            # preview = ""
            # if first_user_message:
            #     raw = first_user_message.message_text
            #     preview = re.sub(r"<span.*?>.*?</span>", "", raw, flags=re.DOTALL).strip()
            preview = ""
            if first_user_message:
                from bs4 import BeautifulSoup
                raw = first_user_message.message_text
                # soup = BeautifulSoup(raw, "html.parser")
                unescaped = html.unescape(raw)  # ← 이 줄 추가
                soup = BeautifulSoup(unescaped, "html.parser")
                for span in soup.select("span.token"):
                    span.decompose()
                preview = soup.get_text(strip=True)



            result.append({
                "session_id": session.session_id,
                "summary": session.summary,
                "preview": preview
            })
        
        return {"success": True, "sessions": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/messages/{session_id}")
async def get_chat_messages_rag(session_id: int, db: Session = Depends(get_db)):
    """채팅 세션의 메시지 목록 조회"""
    try:
        messages = crud.get_chat_messages(db, session_id)
        
        result = []
        for msg in messages:
            result.append({
                "message_id": msg.message_id,  # 추가
                "type": msg.message_type,
                "text": msg.message_text
            })
        
        return {"success": True, "messages": result}
    except Exception as e:
        return {"success": False, "error": str(e)}




# @router.get("/autocomplete", tags=["chat"])
# async def autocomplete_docs(query: str = "", db: Session = Depends(get_db)):
#     """문서 이름 자동완성 (original_file_name 기준 검색)"""
#     docs = (
#         db.query(Docs)
#         .filter(Docs.original_file_name.ilike(f"%{query}%"))
#         .limit(10)
#         .all()
#     )

#     print("[📄 DB 검색 결과]", [doc.original_file_name for doc in docs])
#     return [
#     {"id": doc.docs_id, "name": doc.original_file_name}
#     for doc in docs
# ]
from sqlalchemy import or_

@router.get("/autocomplete", tags=["chat"])
async def autocomplete_docs(query: str = "", user_id: int = None, db: Session = Depends(get_db)):
    """문서 자동완성 (자기 부서 + 공통문서만 검색)"""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id가 필요합니다")

    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    user_dept_id = int(user.department_id or 0)

    docs = (
        db.query(Docs)
        .filter(
            Docs.original_file_name.ilike(f"%{query}%"),
            or_(
                Docs.common_doc.is_(True),
                Docs.department_id == user_dept_id
            )
        )
        .order_by(Docs.create_time.desc())
        .limit(10)
        .all()
    )

    return [{"id": doc.docs_id, "name": doc.original_file_name} for doc in docs]
