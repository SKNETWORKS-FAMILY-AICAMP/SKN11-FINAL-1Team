# 필수 라이브러리
import os
import uuid
import time
import sqlite3
import logging
import re
import numpy as np
from datetime import datetime
from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_core.messages import SystemMessage, HumanMessage
import threading
from contextlib import contextmanager
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 로딩
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 상단에 추가
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_multiformat")


# SQLite DB 연결
DATABASE_PATH = os.getenv("DATABASE_PATH", "db.sqlite3")

@contextmanager
def get_db_connection():
    """안전한 SQLite 연결 관리"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# LangChain 구성
client = QdrantClient(url=QDRANT_URL)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-4o-mini")

WINDOW_SIZE = 10

class AgentState(TypedDict, total=False):
    question: str
    contexts: List[str]
    answer: str
    reflection: str
    rewritten_question: str
    chat_history: List[str]
    rewrite_count: int
    session_id: str
    summary: str
    evaluation_score: int
    needs_rewrite: bool
    evaluation_details: str
    question_type: str
    user_department_id: int  # 부서 ID 추가

# 품질 평가 관리 클래스
class QualityMetrics:
    def __init__(self):
        self.evaluation_history = []
        self.success_threshold = 14  # 20점 만점 중 14점 기준
    
    def update_threshold(self, evaluation_score: int, user_satisfaction: bool):
        """사용자 만족도 기반 임계값 동적 조정"""
        self.evaluation_history.append({
            'score': evaluation_score,
            'satisfied': user_satisfaction,
            'timestamp': datetime.now()
        })
        
        # 최근 50개 평가 기준으로 임계값 조정
        recent_evaluations = self.evaluation_history[-50:]
        
        if len(recent_evaluations) >= 10:
            # 만족도가 높은 답변들의 평균 점수 계산
            satisfied_scores = [e['score'] for e in recent_evaluations if e['satisfied']]
            if satisfied_scores:
                self.success_threshold = max(12, min(18, int(np.mean(satisfied_scores)) - 1))
    
    def should_rewrite(self, evaluation_score: int) -> bool:
        return evaluation_score < self.success_threshold

# 전역 품질 메트릭 인스턴스
quality_metrics = QualityMetrics()

# 세션 및 메시지 DB 함수 (수정됨)
def create_chat_session(user_id: str) -> str:
    """Context Manager만 사용하는 세션 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # AutoField이므로 session_id 자동 생성
        cursor.execute(
            "INSERT INTO core_chatsession (user_id, summary) VALUES (?, ?)",
            (int(user_id), "새 채팅 세션")
        )
        
        # 생성된 session_id 조회
        cursor.execute("SELECT last_insert_rowid()")
        session_id = cursor.fetchone()[0]
        
    return str(session_id)

# def save_message(session_id: str, text: str, message_type: str):
#     """Context Manager만 사용하는 메시지 저장"""
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO core_chatmessage (session_id, create_time, message_text, message_type) VALUES (?, ?, ?, ?)",
#             (int(session_id), datetime.now().isoformat(), text, message_type)
#         )

def save_message(session_id: str, text: str, message_type: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO core_chatmessage (session_id, create_time, message_text, message_type, is_active) VALUES (?, ?, ?, ?, ?)",
            (int(session_id), datetime.now().isoformat(), text, message_type, 1)
        )


    # Context Manager가 자동으로 commit()과 close() 처리

def load_session_history(session_id: str, limit: int = 10) -> List[str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_text, message_type
            FROM core_chatmessage
            WHERE session_id = ?
            ORDER BY create_time ASC
        """, (int(session_id),))
        
        messages = cursor.fetchall()

    history = []
    buffer = {}
    for row in messages:
        text, mtype = row[0], row[1]
        if mtype == "user":
            buffer["user"] = text
        elif mtype in ["bot", "chatbot"]:
            buffer["bot"] = text
        if "user" in buffer and "bot" in buffer:
            history.append(f"Q: {buffer['user']}\nA: {buffer['bot']}")
            buffer = {}

    return history[-limit:]


# 질문 유형 분류 함수
def classify_question_type(question: str) -> str:
    """질문 유형을 분류하여 맞춤형 평가 기준 적용"""
    question_lower = question.lower()
    
    if any(keyword in question_lower for keyword in ['조항', '규정', '조례', '법률', '제', '조']):
        return "regulation"
    elif any(keyword in question_lower for keyword in ['절차', '방법', '어떻게', '신청', '처리']):
        return "procedure"
    elif any(keyword in question_lower for keyword in ['일정', '기간', '언제', '시간']):
        return "schedule"
    elif any(keyword in question_lower for keyword in ['담당자', '연락처', '부서', '누구']):
        return "contact"
    else:
        return "general"

# 개선된 답변 품질 평가 함수
def judge_answer_improved(state: AgentState) -> AgentState:
    """구체적인 평가 기준으로 답변 품질을 평가"""
    context = "\n---\n".join(state.get("contexts", []))
    question = state['question']
    answer = state['answer']
    question_type = classify_question_type(question)
    
    # 질문 유형별 맞춤 평가 기준
    if question_type == "regulation":
        evaluation_criteria = """
        1. 완전성: 해당 조항 번호와 제목이 명시되었는가? (1-5점)
        2. 정확성: 조항의 구체적 내용이 정확히 인용되었는가? (1-5점)
        3. 구체성: 적용 범위나 예외사항이 설명되었는가? (1-5점)
        4. 관련성: 질문과 직접적으로 관련된 조항을 제시했는가? (1-5점)
        """
    elif question_type == "procedure":
        evaluation_criteria = """
        1. 완전성: 절차의 모든 단계가 순서대로 설명되었는가? (1-5점)
        2. 정확성: 필요한 서류나 조건이 구체적으로 명시되었는가? (1-5점)
        3. 구체성: 담당 부서나 연락처 정보가 포함되었는가? (1-5점)
        4. 관련성: 질문자의 상황에 맞는 절차를 제시했는가? (1-5점)
        """
    elif question_type == "schedule":
        evaluation_criteria = """
        1. 완전성: 정확한 일정이나 기간이 제시되었는가? (1-5점)
        2. 정확성: 제시된 일정이 현재 규정과 일치하는가? (1-5점)
        3. 구체성: 구체적인 날짜나 기간이 명시되었는가? (1-5점)
        4. 관련성: 질문과 관련된 일정 정보를 제공했는가? (1-5점)
        """
    else:
        evaluation_criteria = """
        1. 완전성: 질문의 모든 부분에 답변했는가? (1-5점)
        2. 정확성: 제공된 Context에 기반하여 정확한 답변인가? (1-5점)
        3. 구체성: 구체적인 정보와 예시가 포함되었는가? (1-5점)
        4. 관련성: 질문과 직접적으로 관련된 내용인가? (1-5점)
        """
    
    # 구체적인 평가 프롬프트
    evaluation_prompt = f"""
    다음 기준에 따라 답변의 품질을 평가하세요:
    
    **평가 기준 ({question_type} 유형):**
    {evaluation_criteria}
    
    **질문:** {question}
    
    **Context:** {context}
    
    **답변:** {answer}
    
    **평가 결과를 다음 형식으로 제출하세요:**
    완전성: X점 (이유: ...)
    정확성: X점 (이유: ...)
    구체성: X점 (이유: ...)
    관련성: X점 (이유: ...)
    총점: X점 (20점 만점)
    최종판단: [충분|부족]
    개선방향: (부족한 경우만) ...
    """
    
    reflection = llm.invoke(evaluation_prompt)
    
    # 점수 추출
    score_match = re.search(r'총점:\s*(\d+)', reflection.content)
    evaluation_score = int(score_match.group(1)) if score_match else 10
    
    # 개선 방향 추출
    improvement_match = re.search(r'개선방향:\s*(.+)', reflection.content)
    improvement_direction = improvement_match.group(1) if improvement_match else "더 구체적인 정보가 필요합니다."
    
    # 재작성 필요 여부 판단
    needs_rewrite = quality_metrics.should_rewrite(evaluation_score)
    
    return {
        **state, 
        "reflection": reflection.content,
        "evaluation_score": evaluation_score,
        "needs_rewrite": needs_rewrite,
        "evaluation_details": improvement_direction,
        "question_type": question_type
    }

# 개선된 질문 재작성 함수
def reformulate_question_improved(state: AgentState) -> AgentState:
    """평가 결과를 바탕으로 질문을 개선하여 재작성"""
    question = state.get('question')
    contexts = state.get('contexts', [])
    improvement_direction = state.get('evaluation_details', '더 구체적인 정보가 필요합니다.')
    question_type = state.get('question_type', 'general')
    
    # 사용 가능한 Context 키워드 추출
    context_keywords = []
    for context in contexts:
        if '[' in context and ']' in context:
            keyword = context.split('[')[1].split(']')[0]
            context_keywords.append(keyword)
    
    # 질문 유형별 재작성 가이드
    if question_type == "regulation":
        rewrite_guide = """
        1. 구체적인 조항 번호나 제목 언급
        2. 해당 규정의 적용 범위 확인 요청
        3. 예외사항이나 특수 조건 포함
        4. 관련 하위 조항이나 시행령 확인
        """
    elif question_type == "procedure":
        rewrite_guide = """
        1. 단계별 절차의 구체적 순서 요청
        2. 필요한 서류나 준비물 명시 요구
        3. 담당 부서나 연락처 정보 포함
        4. 처리 기간이나 소요 시간 확인
        """
    else:
        rewrite_guide = """
        1. 더 구체적인 세부사항 요청
        2. 실무적 적용 방법 포함
        3. 예외 상황이나 추가 고려사항 확인
        4. 관련 문서나 참고 자료 요청
        """
    
    reformulate_prompt = f"""
    기존 질문을 다음 개선 방향에 따라 재작성하세요:
    
    **기존 질문:** {question}
    
    **개선 방향:** {improvement_direction}
    
    **질문 유형:** {question_type}
    
    **재작성 가이드:**
    {rewrite_guide}
    
    **사용 가능한 Context 키워드:**
    {', '.join(context_keywords)}
    
    **재작성 원칙:**
    - 기존 질문의 핵심 의도는 유지하면서 더 구체적으로 작성
    - 평가에서 부족했던 부분을 보완할 수 있는 방향으로 재작성
    - 사용 가능한 Context의 키워드를 활용하여 정확한 답변을 유도
    
    **재작성된 질문:**
    """
    
    new_question = llm.invoke(reformulate_prompt).content.strip()
    
    return {
        **state, 
        "rewritten_question": new_question, 
        "rewrite_count": state.get("rewrite_count", 0) + 1
    }

# 개선된 판단 함수
def decide_to_reflect_improved(state: AgentState) -> str:
    """점수 기반으로 재작성 여부 결정"""
    if state.get("rewrite_count", 0) >= 2:
        return "summarize"
    
    # 평가 점수 기반 판단
    if state.get("needs_rewrite", False):
        return "rewrite"
    else:
        return "summarize"

# 사용자별 필터링 검색 함수
def search_documents_filtered(state: AgentState) -> AgentState:
    """사용자 부서별 문서 필터링 + 유사도 기반 필터링 적용"""
    query = state.get("rewritten_question") or state["question"]
    user_department_id = state.get("user_department_id")

    query_vec = embeddings.embed_query(query)

    # 🔍 부서 필터 정의
    if user_department_id:
        search_filter = Filter(
            should=[
                FieldCondition(
                    key="metadata.department_id",
                    match=MatchValue(value=user_department_id)
                ),
                FieldCondition(
                    key="metadata.common_doc",
                    match=MatchValue(value=True)
                )
            ]
        )
    else:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.common_doc",
                    match=MatchValue(value=True)
                )
            ]
        )

    # 🔍 Qdrant에서 유사도 검색
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vec,
        query_filter=search_filter,
        limit=10,
        with_payload=True
    )

    logger.info(f"[🔍 Qdrant 검색 결과 수] {len(results)}")

    # ✅ 유사도 임계값 필터링
    threshold = 0.75
    filtered = [r for r in results if r.score >= threshold][:3]

    # fallback: 유사한 청크가 없을 경우 가장 상위 하나만 사용
    if not filtered:
        logger.warning("⚠️ 유사한 문서가 없습니다. 가장 유사한 1개 청크만 사용합니다.")
        filtered = results[:1]

    contexts = []
    for r in filtered:
        title = r.payload.get("metadata", {}).get("title", "무제")
        text = r.payload.get("text", "")
        file_name = (
            r.payload.get("metadata", {}).get("original_file_name") or
            r.payload.get("metadata", {}).get("file_name", "알 수 없음")
        )
        logger.info(f"✅ 포함된 context: {title} (score: {r.score:.4f})")
        contexts.append(f"[{title}] (출처: {file_name})\n{text}")

    return {**state, "contexts": contexts}


# 세션 요약 함수 (수정됨)
def summarize_session(state: AgentState) -> AgentState:
    """단일 연결에서 모든 작업 처리"""
    session_id = state.get("session_id")
    if not session_id:
        return state
    
    # 하나의 연결에서 모든 작업 처리
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 메시지 조회
        cursor.execute("""
            SELECT message_text, message_type
            FROM core_chatmessage
            WHERE session_id = ?
            ORDER BY create_time ASC
        """, (session_id,))
        
        messages = cursor.fetchall()
        
        # 히스토리 처리
        history = []
        buffer = {}
        for row in messages:
            text, mtype = row[0], row[1]
            if mtype == "user":
                buffer["user"] = text
            elif mtype == "bot":
                buffer["bot"] = text
            if "user" in buffer and "bot" in buffer:
                history.append(f"Q: {buffer['user']}\nA: {buffer['bot']}")
                buffer = {}
        
        combined = "\n".join(history[-10:])
        
        # LLM으로 요약 생성
        messages_for_llm = [
            SystemMessage(content="당신은 기업 내부 상담용 챗봇입니다. 다음 대화 내용은 한 사용자의 상담 기록입니다. 핵심 질문과 답변이 무엇이었는지 중심으로 20글자 내로 요약해 주세요."),
            HumanMessage(content=f"대화 내용:\n{combined}\n\n요약:")
        ]
        
        summary = llm.invoke(messages_for_llm).content.strip()
        
        # 같은 연결에서 요약 업데이트
        cursor.execute(
            "UPDATE core_chatsession SET summary = ? WHERE session_id = ?",
            (summary, session_id)
        )
    
    return {**state, "summary": summary}

# 기존 함수들 (필터링으로 변경)
def decide_use_rag(state: AgentState) -> AgentState:
    return state

# def get_use_rag_condition(state: AgentState) -> str:
#     question = state["question"]
#     prompt = f"""다음 질문을 읽고, 사내 문서나 규정과 같은 참고 문서가 필요한 질문인지 판단하세요.

# 질문: "{question}"

# 문서가 필요하면 "use_rag", 아니면 "skip_rag"만 출력하세요."""
    
#     result = llm.invoke(prompt).content.strip().lower()
#     return "use_rag" if "use" in result else "skip_rag"

def get_use_rag_condition(state: AgentState) -> str:
    question = state["question"]

    logger.info("🔥 get_use_rag_condition() 함수 호출됨!")

    prompt = f"""
너는 사용자의 질문이 '회사 내부 문서 검색이 필요한 질문'인지 판단하는 심사관이야.

다음의 기준에 따라 판단해:
- 회사 정책, 규정, 메뉴얼, 제출 기한, 휴가 제도, 신청 절차, 업무 처리 방식 등과 관련된 질문이면 "use_rag"
- 일반적인 잡담, 일상 대화, 개인적인 감정 또는 널리 알려진 상식 기반 질문이면 "skip_rag"

질문: "{question}"

반드시 딱 하나의 단어만 출력해: "use_rag" 또는 "skip_rag".
다른 말은 절대 하지 마.
"""

    result = llm.invoke(prompt).content.strip().lower()
    # ✅ 로그 찍기
    logger.info(f"[RAG 판단] 질문: {question}")
    logger.info(f"[RAG 판단] LLM 응답: {result}")
    logger.info(f"[RAG 판단] 결과: {'✅ use_rag' if 'use_rag' in result else '❌ skip_rag'}")
    return "use_rag" if "use_rag" in result else "skip_rag"



def generate_answer(state: AgentState) -> AgentState:
    context = "\n---\n".join(state.get("contexts", []))
    question = state.get("rewritten_question") or state["question"]
    full_history = state.get("chat_history", [])
    recent_history = full_history[-WINDOW_SIZE:]
    history_text = "\n".join(recent_history)
    
    titles = []
    ref_files = set()

    for c in state.get("contexts", []):
        if c.startswith("["):
            lines = c.split("\n")
            if lines:
                titles.append(lines[0].strip("[]"))
            if "(출처: " in c:
                file_name = c.split("(출처: ")[1].split(")")[0].strip()
                ref_files.add(file_name)

    ref_titles = ", ".join(titles)
    ref_file_list = ", ".join(sorted(ref_files))  # 중복 제거된 파일명들
    
    prompt = f"""
지금까지의 대화 기록:
{history_text}

아래 질문에 대해 context에 충실하게 자세히 답변하세요.
→ 반드시 형식: "제X조 조항명 에 따르면 ..."

참고 조항: {ref_titles}

Context:
{context}

Question: {question}

Answer:"""
    
    response = llm.invoke(prompt)
    answer_text = response.content.strip()

    # 참고 문서 표시 추가
    if ref_file_list:
        answer_text += f"\n\n📄 참고 문서: {ref_file_list}"

    updated_history = full_history + [f"Q: {question}\nA: {answer_text}"]

    return {**state, "answer": answer_text, "chat_history": updated_history}




def direct_answer(state: AgentState) -> AgentState:
    question = state["question"]
    history_text = "\n".join(state.get("chat_history", [])[-WINDOW_SIZE:])
    
    prompt = f"""
지금까지의 대화 내용:
{history_text}

Question: {question}

Answer:"""
    
    response = llm.invoke(prompt)
    updated_history = state.get("chat_history", []) + [f"Q: {question}\nA: {response.content}"]
    
    return {**state, "answer": response.content, "chat_history": updated_history}

# LangGraph 정의 (개선된 노드 사용)
builder = StateGraph(AgentState)
builder.add_node("decide", decide_use_rag)
builder.add_node("judge_rag", get_use_rag_condition)
builder.add_node("search", search_documents_filtered)  # 필터링 검색으로 변경
builder.add_node("answer", generate_answer)
builder.add_node("judge", judge_answer_improved)  # 개선된 함수 사용
builder.add_node("rewrite", reformulate_question_improved)  # 개선된 함수 사용
builder.add_node("direct_answer", direct_answer)
builder.add_node("summarize", summarize_session)

builder.set_entry_point("decide")

builder.add_conditional_edges("decide", get_use_rag_condition, {
    "use_rag": "search", "skip_rag": "direct_answer"
})

builder.add_edge("search", "answer")
builder.add_edge("answer", "judge")

builder.add_conditional_edges("judge", decide_to_reflect_improved, {  # 개선된 함수 사용
    "summarize": "summarize", "rewrite": "rewrite"
})

builder.add_edge("rewrite", "search")
builder.add_edge("direct_answer", "summarize")
builder.add_edge("summarize", END)

graph = builder.compile()

# 실행 진입점
def run_agent(user_id: str):
    session_id = create_chat_session(user_id)
    history = load_session_history(session_id=session_id, limit=10)

    state: AgentState = {
        "chat_history": history,
        "rewrite_count": 0,
        "session_id": session_id
    }

    while True:
        question = input("\n질문을 입력하세요: ")
        if question.lower() == "exit":
            print("\n✅ 세션 종료")
            break

        save_message(session_id, question, "user")

        state["question"] = question
        state["rewrite_count"] = 0
        state.pop("rewritten_question", None)

        final = graph.invoke(state)

        answer = final["answer"]
        evaluation_score = final.get("evaluation_score", 0)

        # ✅ RAG 사용 여부 판단
        used_rag = bool(final.get("contexts"))  # context가 비어있지 않으면 RAG 사용
        rag_tag = "🧾 [RAG 사용]" if used_rag else "💬 [RAG 미사용]"

        # ✅ 사용자에게 출력
        print(f"\n{rag_tag}")
        print(f"\n🧠 답변:\n{answer}")
        print(f"\n📊 평가 점수: {evaluation_score}/20")

        # ✅ 로그에도 저장
        save_message(session_id, f"{rag_tag}\n\n{answer}", "bot")

        # 상태 업데이트
        state["chat_history"] = final.get("chat_history", [])


# 테스트용
if __name__ == "__main__":
    run_agent(user_id="로그인된-유저-id")
