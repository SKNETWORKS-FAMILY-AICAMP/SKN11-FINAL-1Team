from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import sys
import os
import logging
import time
import uuid
from rag_agent_graph_db_v3_finaltemp_v2 import get_db_connection, client, COLLECTION_NAME


from fastapi.responses import JSONResponse
from embed_and_upsert import advanced_embed_and_upsert, get_existing_point_ids


from fastapi import UploadFile, File, Form, Query, HTTPException
from qdrant_client.models import Filter, FieldCondition, MatchValue

from fastapi.responses import FileResponse


from rag_agent_graph_db_v3_finaltemp_v2 import (
    create_chat_session,
    save_message,
    load_session_history,
    graph, AgentState
)


from fastapi.middleware.cors import CORSMiddleware



# 기존 RAG 시스템 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chatbot API", version="1.0.0")


# ✅ CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🚨 개발 중만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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
    used_rag: bool = False  # ✅ 추가
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
        start_time = time.time()

        logger.info(f"RAG 요청 수신: {request.question[:50]}...")
        
        # 세션 ID가 없으면 새로 생성
        if not request.session_id:
            session_id = create_chat_session(request.user_id)
            logger.info(f"새 세션 생성: {session_id}")
        else:
            session_id = request.session_id
        logger.warning(f"🔥 사용자 메시지 저장됨 - FastAPI: {request.question}")
        # 사용자 메시지 저장
        save_message(session_id, request.question, "user")
        
        # 사용자 히스토리 로드
        history = load_session_history(request.user_id, limit=5)
        
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

        used_rag = bool(result.get("contexts"))
        logger.info(f"[RAG 여부] {'🧾 사용함' if used_rag else '💬 사용 안 함'} - 질문: {request.question}")

        
        # 봇 응답 저장
        answer = result["answer"]
        save_message(session_id, answer, "bot")
        
        logger.info(f"RAG 응답 생성 완료: {answer[:50]}...")

        # ✅ 응답 시간 측정 및 출력
        elapsed = time.time() - start_time
        logger.info(f"⏱️ 응답 생성 시간: {elapsed:.2f}초 - 질문: {request.question}")
        
        return ChatResponse(
            answer=answer,
            session_id=session_id,
            contexts=result.get("contexts", []),
            summary=result.get("summary"),
            used_rag=bool(result.get("contexts")),  # ✅ 추가
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


# 문서 업로드 API

UPLOAD_BASE = "uploaded_docs"

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    department_id: int = Form(...),
    common_doc: bool = Form(False),
    original_file_name: str = Form("")
):
    try:
        # 저장 디렉토리 생성
        os.makedirs(UPLOAD_BASE, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        save_path = os.path.join(UPLOAD_BASE, unique_filename)

        with open(save_path, "wb") as f:
            f.write(await file.read())

        logger.info(f"📄 업로드 파일 저장 완료: {save_path}")

        # 기존 임베딩된 문서 목록 가져오기
        existing_ids = get_existing_point_ids()

        # 문서 임베딩 및 Qdrant 저장
        chunk_count = advanced_embed_and_upsert(
            save_path,
            existing_ids,
            department_id=department_id,
            common_doc=common_doc,
            original_file_name=original_file_name or file.filename
        )

        return JSONResponse({
            "success": True,
            "chunks_uploaded": chunk_count,
            "original_file": file.filename,
            "saved_path": save_path
        })
    except Exception as e:
        logger.error(f"📄 문서 업로드 처리 중 오류: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    


# 문서 삭제 API



@app.post("/delete")
async def delete_document(
    docs_id: int = Form(...),
    department_id: int = Form(...)
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM core_docs WHERE docs_id = ? AND department_id = ?", (docs_id, department_id))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
            file_path = row["file_path"]
            abs_path = os.path.abspath(file_path)

            # 실제 파일 삭제
            if os.path.exists(abs_path):
                os.remove(abs_path)

            # Qdrant에서 삭제
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            delete_filter = Filter(must=[
                FieldCondition(key="metadata.source", match=MatchValue(value=abs_path)),
                FieldCondition(key="metadata.department_id", match=MatchValue(value=department_id))
            ])
            client.delete(collection_name=COLLECTION_NAME, points_selector=delete_filter)

            # DB에서 삭제
            cursor.execute("DELETE FROM core_docs WHERE docs_id = ? AND department_id = ?", (docs_id, department_id))

        return {"success": True, "message": "문서 및 Qdrant 청크 삭제 완료"}
    except Exception as e:
        return {"success": False, "error": str(e)}



# 문서 수정 API

@app.post("/update")
async def update_document(
    docs_id: int = Form(...),
    department_id: int = Form(...),
    tags: str = Form(""),
    description: str = Form(""),
    common_doc: bool = Form(False)
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE core_docs
                SET tags = ?, description = ?, common_doc = ?
                WHERE docs_id = ? AND department_id = ?
            """, (tags, description, int(common_doc), docs_id, department_id))

        return {"success": True, "message": "문서 정보가 수정되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}



# 문서 목록 조회 API


@app.get("/list")
async def list_documents(department_id: int = Query(...)):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM core_docs
                WHERE department_id = ? OR common_doc = 1
            """, (department_id,))
            rows = cursor.fetchall()
            docs = [dict(row) for row in rows]

        return {"success": True, "docs": docs}
    except Exception as e:
        return {"success": False, "error": str(e)}




@app.get("/download/{docs_id}")
async def download_document(docs_id: int):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path, original_file_name FROM core_docs WHERE docs_id = ?", (docs_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

            file_path = os.path.abspath(row["file_path"])
            original_name = row["original_file_name"]

            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")

            return FileResponse(
                path=file_path,
                filename=original_name,
                media_type='application/octet-stream'
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/chat/session/create")
# async def create_chat_session(user_id: int = Form(...)):
#     try:
#         with get_db_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(
#                 "INSERT INTO core_chatsession (user_id, summary) VALUES (?, ?)",
#                 (user_id, "새 대화")
#             )
#             conn.commit()
#             session_id = cursor.lastrowid

#         return {"success": True, "session_id": session_id}
#     except Exception as e:
#         return {"success": False, "error": str(e)}



@app.post("/chat/session/create")
async def create_chat_session(user_id: int = Form(...)):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO core_chatsession (user_id, summary) VALUES (?, ?)",
                (user_id, "새 대화")
            )
            conn.commit()
            session_id = cursor.lastrowid

            # 🔥 바로 생성된 세션의 preview도 함께 응답
            return {
                "success": True,
                "session_id": session_id,
                "summary": "새 대화",
                "preview": ""
            }
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.post("/chat/session/delete")
async def delete_chat_session(session_id: int = Form(...), user_id: int = Form(...)):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 보안: 해당 유저가 소유한 세션인지 확인
            cursor.execute("SELECT * FROM core_chatsession WHERE session_id = ? AND user_id = ?", (session_id, user_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="권한이 없습니다.")

            cursor.execute("DELETE FROM core_chatsession WHERE session_id = ? AND user_id = ?", (session_id, user_id))
            conn.commit()

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}





@app.post("/chat/message/send")
async def send_chat_message(
    session_id: int = Form(...),
    user_id: int = Form(...),
    message_text: str = Form(...),
):
    try:
        # 1. 사용자 메시지 저장
        # save_message(session_id, "user", message_text)
        save_message(session_id, message_text, "user")

        # 2. 대화 이력 불러오기
        history = load_session_history(session_id)

        # 3. Agent 실행
        state: AgentState = {
            "question": message_text,
            "chat_history": history,
            "rewrite_count": 0,
            "session_id": session_id,
            "user_department_id": 0  # 기본값 (없으면 전체 context)
        }

        result = graph.invoke(state)
        answer = result.get("answer", "답변 생성 실패")
        
        
        # response = graph.invoke({
        #     "input": message_text,
        #     "chat_history": history,
        #     "state": state
        # })

        # answer = response.get("answer", "답변 생성 실패")

        # 4. 응답 메시지 저장
        # save_message(session_id, "bot", answer)
        save_message(session_id, answer, "bot")

        return {
            "success": True,
            "response": answer
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/chat/messages/{session_id}")
async def get_chat_messages(session_id: int):
    try:
        messages = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_type, message_text
                FROM core_chatmessage
                WHERE session_id = ?
                ORDER BY message_id
            """, (session_id,))
            rows = cursor.fetchall()
            for row in rows:
                messages.append({
                    "type": row["message_type"],
                    "text": row["message_text"]
                })

        return {"success": True, "messages": messages}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/chat/sessions/{user_id}")
async def get_user_sessions(user_id: int):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, summary FROM core_chatsession
                WHERE user_id = ?
                ORDER BY session_id DESC
            """, (user_id,))
            sessions = cursor.fetchall()

            # 각 세션의 첫 번째 user 메시지도 함께 가져옴
            result = []
            for row in sessions:
                session_id = row["session_id"]
                summary = row["summary"]
                cursor.execute("""
                    SELECT message_text
                    FROM core_chatmessage
                    WHERE session_id = ? AND message_type = 'user'
                    ORDER BY create_time ASC
                    LIMIT 1
                """, (session_id,))
                preview_row = cursor.fetchone()
                preview = preview_row["message_text"] if preview_row else ""
                result.append({
                    "session_id": session_id,
                    "summary": summary,
                    "preview": preview
                })

        return {"success": True, "sessions": result}
    except Exception as e:
        return {"success": False, "error": str(e)}




if __name__ == "__main__":
    import uvicorn
    logger.info("FastAPI RAG 서버 시작...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
