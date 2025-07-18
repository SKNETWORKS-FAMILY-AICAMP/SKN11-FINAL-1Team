from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import sys
import os
import logging

# 기존 RAG 시스템 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag_agent_graph_db_v3_finaltemp_v2 import graph, AgentState, load_user_history, save_message, create_chat_session

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    user_id: str
    department_id: int  # 부서 ID 추가

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    contexts: List[str] = []
    summary: Optional[str] = None
    success: bool = True

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """API 상태 확인"""
    return HealthResponse(
        status="healthy",
        message="RAG 시스템이 정상 작동 중입니다."
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest):
    """RAG 기반 챗봇 응답 생성"""
    try:
        logger.info(f"RAG 요청 수신: {request.question[:50]}...")
        
        # 세션 ID가 없으면 새로 생성
        if not request.session_id:
            session_id = create_chat_session(request.user_id)
            logger.info(f"새 세션 생성: {session_id}")
        else:
            session_id = request.session_id
        logger.warning(f"🔥 사용자 메시지 저장됨 - FastAPI: {request.question}")
        # 사용자 메시지 저장
        # save_message(session_id, request.question, "user")
        
        # 사용자 히스토리 로드
        history = load_user_history(request.user_id, limit=5)
        
        # 초기 상태 설정 (부서 ID 추가)
        state: AgentState = {
            "question": request.question,
            "chat_history": history,
            "rewrite_count": 0,
            "session_id": session_id,
            "user_department_id": request.department_id  # 부서 ID 전달
        }
        
        # LangGraph 실행
        logger.info("LangGraph 실행 시작...")
        result = graph.invoke(state)
        
        # 봇 응답 저장
        answer = result["answer"]
        save_message(session_id, answer, "bot")
        
        logger.info(f"RAG 응답 생성 완료: {answer[:50]}...")
        
        return ChatResponse(
            answer=answer,
            session_id=session_id,
            contexts=result.get("contexts", []),
            summary=result.get("summary"),
            success=True
        )
        
    except Exception as e:
        logger.error(f"RAG 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG 처리 중 오류 발생: {str(e)}")

@app.post("/create_session")
async def create_new_session(user_id: str):
    """새 채팅 세션 생성"""
    try:
        session_id = create_chat_session(user_id)
        logger.info(f"새 세션 생성: {session_id}")
        return {"session_id": session_id, "success": True}
    except Exception as e:
        logger.error(f"세션 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("FastAPI RAG 서버 시작...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
