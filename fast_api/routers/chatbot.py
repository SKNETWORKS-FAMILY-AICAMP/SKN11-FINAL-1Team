from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

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
    
    # 챗봇 응답 저장
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