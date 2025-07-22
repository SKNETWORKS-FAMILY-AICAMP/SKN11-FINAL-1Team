from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import time
import logging
import sys
import os
from database import get_db
import crud
import schemas

# RAG 시스템 조건부 임포트
RAG_AVAILABLE = False
graph = None

def initialize_rag_for_chatbot():
    """챗봇용 RAG 시스템 초기화"""
    global RAG_AVAILABLE, graph
    
    # 절대 경로로 Django 프로젝트 경로 찾기
    current_file = os.path.abspath(__file__)
    fast_api_dir = os.path.dirname(os.path.dirname(current_file))  # fast_api 디렉토리
    project_root = os.path.dirname(fast_api_dir)  # final_prj 디렉토리
    django_rag_path = os.path.join(project_root, "django_prj", "onboarding_quest")
    
    logging.info(f"챗봇 RAG 시스템 초기화 시도 - 경로: {django_rag_path}")
    
    if django_rag_path not in sys.path:
        sys.path.insert(0, django_rag_path)
    
    try:
        # RAG 모듈 동적 import
        rag_module = __import__('rag_agent_graph_db_v3_finaltemp_v2')
        graph = getattr(rag_module, 'graph')
        
        RAG_AVAILABLE = True
        logging.info("✅ 챗봇용 RAG 시스템 초기화 성공")
        
    except Exception as e:
        logging.warning(f"⚠️ 챗봇용 RAG 시스템 초기화 실패: {e}")
        RAG_AVAILABLE = False

# 초기화 실행
initialize_rag_for_chatbot()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

# Pydantic 모델
class ChatMessage(BaseModel):
    message: str
    user_id: int

class ChatResponse(BaseModel):
    response: str
    user_id: int
    timestamp: Optional[str] = None

class ChatHistory(BaseModel):
    user_id: int
    messages: List[dict]

# 임시 챗봇 대화 이력 저장소
chat_history = {}

@router.post("/message", response_model=ChatResponse)
async def chatbot_message(chat_message: ChatMessage):
    """챗봇 메시지 처리"""
    # 간단한 챗봇 응답 로직
    message = chat_message.message.lower()
    
    # 사용자별 대화 이력 저장
    if chat_message.user_id not in chat_history:
        chat_history[chat_message.user_id] = []
    
    chat_history[chat_message.user_id].append({
        "type": "user",
        "message": chat_message.message
    })
    
    # 챗봇 응답 생성
    if "안녕" in message or "hello" in message:
        response = "안녕하세요! 온보딩 퀘스트 챗봇입니다. 무엇을 도와드릴까요?"
    elif "업무" in message or "task" in message:
        response = "업무 관련 도움을 드릴 수 있습니다. 다음과 같은 명령을 사용해보세요:\n- 업무 목록 확인\n- 새 업무 생성\n- 업무 상태 변경"
    elif "사용자" in message or "user" in message:
        response = "사용자 관리 기능을 도와드릴 수 있습니다. 멘토, 멘티, 관리자 정보를 확인하거나 관리할 수 있습니다."
    elif "도움말" in message or "help" in message:
        response = """
        📚 온보딩 퀘스트 챗봇 도움말 📚
        
        사용 가능한 명령:
        • 업무 관련: 업무 목록, 업무 생성, 업무 상태 변경
        • 사용자 관리: 멘토/멘티 정보 확인
        • 일반: 안녕하세요, 도움말
        
        더 자세한 정보가 필요하시면 언제든 말씀해주세요!
        """
    else:
        response = "죄송합니다. 아직 해당 질문에 대한 답변을 준비하지 못했습니다. '도움말'이라고 입력하시면 사용 가능한 명령을 확인하실 수 있습니다."
    
    # # 챗봇 응답 저장
    chat_history[chat_message.user_id].append({
        "type": "bot",
        "message": response
    })
    
    return ChatResponse(response=response, user_id=chat_message.user_id)

@router.get("/history/{user_id}", response_model=ChatHistory)
async def get_chat_history(user_id: int):
    """사용자의 채팅 이력 조회"""
    if user_id not in chat_history:
        chat_history[user_id] = []
    
    return ChatHistory(user_id=user_id, messages=chat_history[user_id])

@router.delete("/history/{user_id}")
async def clear_chat_history(user_id: int):
    """사용자의 채팅 이력 삭제"""
    if user_id in chat_history:
        del chat_history[user_id]
    return {"message": "채팅 이력이 성공적으로 삭제되었습니다"}

@router.get("/stats")
async def get_chatbot_stats():
    """챗봇 통계 조회"""
    total_users = len(chat_history)
    total_messages = sum(len(messages) for messages in chat_history.values())
    
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "active_conversations": len([uid for uid, messages in chat_history.items() if len(messages) > 0])
    }


# RAG 기반 챗봇 인터랙션 엔드포인트
@router.post("/rag/interact")
async def chatbot_rag_interact(
    question: str = Form(...),
    user_id: int = Form(...),
    department_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """RAG 기반 챗봇과의 상호작용"""
    if not RAG_AVAILABLE:
        # RAG 시스템이 없으면 기본 챗봇 응답
        return await chatbot_basic_response(question, user_id)
    
    try:
        # 사용자 검증
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 간단한 질문-답변 상호작용 (세션 미생성)
        state = {
            "question": question,
            "chat_history": [],
            "rewrite_count": 0,
            "user_department_id": department_id
        }
        
        # LangGraph 실행
        result = graph.invoke(state)
        
        # 간단한 응답 반환
        return {
            "success": True,
            "answer": result["answer"],
            "used_rag": bool(result.get("contexts")),
            "contexts": result.get("contexts", [])[:3],  # 최대 3개만
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"RAG 챗봇 처리 중 오류: {str(e)}")
        # 오류 시 기본 챗봇으로 폴백
        return await chatbot_basic_response(question, user_id)

async def chatbot_basic_response(question: str, user_id: int):
    """기본 챗봇 응답 (RAG 미사용)"""
    message = question.lower()
    
    if "안녕" in message or "hello" in message:
        response = "안녕하세요! 온보딩 퀘스트 챗봇입니다. 무엇을 도와드릴까요?"
    elif "업무" in message or "task" in message:
        response = "업무 관련 도움을 드릴 수 있습니다. 다음과 같은 명령을 사용해보세요:\n- 업무 목록 확인\n- 새 업무 생성\n- 업무 상태 변경"
    elif "사용자" in message or "user" in message:
        response = "사용자 관리 기능을 도와드릴 수 있습니다. 멘토, 멘티, 관리자 정보를 확인하거나 관리할 수 있습니다."
    elif "도움말" in message or "help" in message:
        response = """
        📚 온보딩 퀘스트 챗봇 도움말 📚
        
        사용 가능한 명령:
        • 업무 관련: 업무 목록, 업무 생성, 업무 상태 변경
        • 사용자 관리: 멘토/멘티 정보 확인
        • 일반: 안녕하세요, 도움말
        
        더 자세한 정보가 필요하시면 언제든 말씀해주세요!
        """
    else:
        response = "죄송합니다. 아직 해당 질문에 대한 답변을 준비하지 못했습니다. '도움말'이라고 입력하시면 사용 가능한 명령을 확인하실 수 있습니다."
    
    return {
        "success": True,
        "answer": response,
        "used_rag": False,
        "contexts": [],
        "timestamp": time.time()
    }

@router.get("/rag/health")
async def rag_health_check():
    """RAG 시스템 상태 확인"""
    return {
        "rag_available": RAG_AVAILABLE,
        "status": "healthy" if RAG_AVAILABLE else "fallback_mode",
        "message": "RAG 시스템이 활성화되었습니다." if RAG_AVAILABLE else "기본 챗봇 모드로 동작합니다."
    } 