# 필수 라이브러리
import os
import uuid
import time
import psycopg2
import logging
from datetime import datetime
from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient
from langchain_core.messages import SystemMessage, HumanMessage

# 로딩
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = "rag_multiformat"

# DB 연결
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# LangChain 구성
client = QdrantClient(url=QDRANT_URL, check_compatibility=False)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-4o-mini")

WINDOW_SIZE = 3

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

# 세션 및 메시지 DB 함수
def create_chat_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO core_chatsession (session_id, user_id, created_at) VALUES (%s, %s, %s)",
        (session_id, user_id, datetime.now())
    )
    conn.commit()
    return session_id

def save_message(session_id: str, text: str, message_type: str):
    cursor.execute(
        "INSERT INTO core_chatmessage (message_id, session_id, create_time, message_text, message_type) VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), session_id, datetime.now(), text, message_type)
    )
    conn.commit()

def load_user_history(user_id: str, limit: int = 10) -> List[str]:
    cursor.execute("""
        SELECT message_text, message_type
        FROM core_chatmessage
        WHERE session_id IN (
            SELECT session_id FROM core_chatsession WHERE user_id = %s
        )
        ORDER BY create_time DESC
        LIMIT %s
    """, (user_id, limit * 2))
    messages = cursor.fetchall()[::-1]

    history = []
    buffer = {}
    for text, mtype in messages:
        if mtype == "user":
            buffer["user"] = text
        elif mtype == "bot":
            buffer["bot"] = text
        if "user" in buffer and "bot" in buffer:
            history.append(f"Q: {buffer['user']}\nA: {buffer['bot']}")
            buffer = {}
    return history[-limit:]

# 세션 요약 LangGraph 노드
def summarize_session(state: AgentState) -> AgentState:
    session_id = state.get("session_id")
    if not session_id:
        return state

    cursor.execute("""
        SELECT message_text, message_type
        FROM core_chatmessage
        WHERE session_id = %s
        ORDER BY create_time ASC
    """, (session_id,))
    messages = cursor.fetchall()

    history = []
    buffer = {}
    for text, mtype in messages:
        if mtype == "user":
            buffer["user"] = text
        elif mtype == "bot":
            buffer["bot"] = text
        if "user" in buffer and "bot" in buffer:
            history.append(f"Q: {buffer['user']}\nA: {buffer['bot']}")
            buffer = {}

    combined = "\n".join(history[-10:])

    messages = [
        SystemMessage(content="당신은 기업 내부 상담용 챗봇입니다. 다음 대화 내용은 한 사용자의 상담 기록입니다. 핵심 질문과 답변이 무엇이었는지 중심으로 요약해 주세요."),
        HumanMessage(content=f"대화 내용:\n{combined}\n\n요약:")
    ]
    summary = llm.invoke(messages).content.strip()

    cursor.execute(
        "UPDATE core_chatsession SET summary = %s WHERE session_id = %s",
        (summary, session_id)
    )
    conn.commit()

    return {**state, "summary": summary}

# LangGraph 노드 함수
def decide_use_rag(state: AgentState) -> AgentState:
    return state

def get_use_rag_condition(state: AgentState) -> str:
    question = state["question"]
    prompt = f"""다음 질문을 읽고, 사내 문서나 규정과 같은 참고 문서가 필요한 질문인지 판단하세요.

질문: \"{question}\"

문서가 필요하면 \"use_rag\", 아니면 \"skip_rag\"만 출력하세요."""
    result = llm.invoke(prompt).content.strip().lower()
    return "use_rag" if "use" in result else "skip_rag"

def search_documents(state: AgentState) -> AgentState:
    query = state.get("rewritten_question") or state["question"]
    query_vec = embeddings.embed_query(query)
    results = client.search(collection_name=COLLECTION_NAME, query_vector=query_vec, limit=3, with_payload=True)
    contexts = []
    for r in results:
        title = r.payload.get("metadata", {}).get("title", "무제")
        text = r.payload.get("text", "")
        contexts.append(f"[{title}]\n{text}")
    return {**state, "contexts": contexts}

def generate_answer(state: AgentState) -> AgentState:
    context = "\n---\n".join(state.get("contexts", []))
    question = state.get("rewritten_question") or state["question"]
    full_history = state.get("chat_history", [])
    recent_history = full_history[-WINDOW_SIZE:]
    history_text = "\n".join(recent_history)
    titles = [c.split('\n')[0].strip("[]") for c in state.get("contexts", []) if c.startswith("[")]
    ref_titles = ", ".join(titles)
    prompt = f"""
지금까지의 대화 기록:
{history_text}

아래 질문에 대해 context에 충실하게 자세히 답변하세요.
→ 반드시 형식: \"제X조 조항명 에 따르면 ...\"

참고 조항: {ref_titles}

Context:
{context}
Question: {question}
Answer:"""
    response = llm.invoke(prompt)
    updated_history = full_history + [f"Q: {question}\nA: {response.content}"]
    return {**state, "answer": response.content, "chat_history": updated_history}

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

def judge_answer(state: AgentState) -> AgentState:
    context = "\n---\n".join(state.get("contexts", []))
    prompt = f"""질문: {state['question']}
Context: {context}
Answer: {state['answer']}
답변이 충분한가요? 
- 평가: [충분|부족]
- 이유: ..."""
    reflection = llm.invoke(prompt)
    return {**state, "reflection": reflection.content}

def decide_to_reflect(state: AgentState) -> str:
    if state.get("rewrite_count", 0) >= 2:
        return "summarize"
    return "summarize" if "충분" in state.get("reflection", "") else "rewrite"

def reformulate_question(state: AgentState) -> AgentState:
    prompt = f"""답변이 부족하다면, 질문을 좀 더 명확하게 다시 작성해주세요.
기존 질문: {state.get('question')}
답변: {state['answer']}
Context: {'---'.join(state.get('contexts', []))}

새 질문:"""
    new_q = llm.invoke(prompt).content.strip()
    return {**state, "rewritten_question": new_q, "rewrite_count": state.get("rewrite_count", 0) + 1}

# LangGraph 정의
builder = StateGraph(AgentState)
builder.add_node("decide", decide_use_rag)
builder.add_node("search", search_documents)
builder.add_node("answer", generate_answer)
builder.add_node("judge", judge_answer)
builder.add_node("rewrite", reformulate_question)
builder.add_node("direct_answer", direct_answer)
builder.add_node("summarize", summarize_session)

builder.set_entry_point("decide")
builder.add_conditional_edges("decide", get_use_rag_condition, {
    "use_rag": "search", "skip_rag": "direct_answer"
})
builder.add_edge("search", "answer")
builder.add_edge("answer", "judge")
builder.add_conditional_edges("judge", decide_to_reflect, {
    "summarize": "summarize", "rewrite": "search"
})
builder.add_edge("rewrite", "search")
builder.add_edge("direct_answer", "summarize")
builder.add_edge("summarize", END)

graph = builder.compile()

# 실행 진입점
def run_agent(user_id: str):
    session_id = create_chat_session(user_id)
    history = load_user_history(user_id, limit=5)
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
        print(f"\n🧠 답변:\n{answer}")
        save_message(session_id, answer, "bot")
        state["chat_history"] = final.get("chat_history", [])

# 테스트용
if __name__ == "__main__":
    run_agent(user_id="로그인된-유저-id")
