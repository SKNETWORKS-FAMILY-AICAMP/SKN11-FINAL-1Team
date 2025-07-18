from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


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
