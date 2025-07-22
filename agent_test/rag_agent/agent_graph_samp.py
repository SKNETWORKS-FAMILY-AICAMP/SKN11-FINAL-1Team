import os
import logging
import time
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rag_graph_v2.log", mode="a", encoding="utf-8")
    ]
)

# 환경 변수 로딩
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = "rag_multiformat"

# 클라이언트 및 모델
client = QdrantClient(url=QDRANT_URL, check_compatibility=False)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small")
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-4o-mini")

WINDOW_SIZE = 3

# State 정의
class AgentState(TypedDict, total=False):
    question: str
    contexts: List[str]
    answer: str
    reflection: str
    rewritten_question: str
    chat_history: List[str]
    rewrite_count: int

# RAG 여부 판단
def decide_use_rag(state: AgentState) -> AgentState:
    return state

def get_use_rag_condition(state: AgentState) -> str:
    question = state["question"]
    prompt = f"""다음 질문을 읽고, 사내 문서나 규정과 같은 참고 문서가 필요한 질문인지 판단하세요.

질문: \"{question}\"

문서가 필요하면 "use_rag", 아니면 "skip_rag"만 출력하세요."""
    result = llm.invoke(prompt).content.strip().lower()
    return "use_rag" if "use" in result else "skip_rag"

# 문서 검색
def search_documents(state: AgentState) -> AgentState:
    query = state.get("rewritten_question") or state["question"]
    query_vec = embeddings.embed_query(query)
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vec,
        limit=3,
        with_payload=True
    )
    contexts = []
    for r in results:
        title = r.payload.get("metadata", {}).get("title", "무제")
        text = r.payload.get("text", "")
        contexts.append(f"[{title}]\n{text}")
    return {**state, "contexts": contexts}

# 답변 생성
def generate_answer(state: AgentState) -> AgentState:
    context = "\n---\n".join(state.get("contexts", []))
    question = state.get("rewritten_question") or state["question"]
    full_history = state.get("chat_history", [])
    recent_history = full_history[-WINDOW_SIZE:]
    history_text = "\n".join(recent_history)
    titles = [c.split('\n')[0].strip("[]") for c in state["contexts"] if c.startswith("[")]
    ref_titles = ", ".join(titles)
    fewshot = """예시 :
Q: 지각이 3회 누적되면 어떻게 되나요?
A: [제12조 근태관리 규정]에 따르면 지각 3회는 결근 1회로 간주됩니다.

"""
    prompt = f"""{fewshot}
지금까지의 대화 기록:
{history_text}

아래 질문에 대해 context에 충실하게 자세히 답변하세요.

**반드시 다음 형식을 따르세요**  
→ "제X조 조항명 에 따르면 ..."  

참고 조항: {ref_titles}

Context:
{context}
Question: {question}
Answer:"""
    response = llm.invoke(prompt)
    updated_history = full_history + [f"Q: {question}\nA: {response.content}"]
    return {**state, "answer": response.content, "chat_history": updated_history}

# RAG 없이 직접 답변
def direct_answer(state: AgentState) -> AgentState:
    question = state["question"]
    full_history = state.get("chat_history", [])
    recent_history = full_history[-WINDOW_SIZE:]
    history_text = "\n".join(recent_history)
    fewshot = """예시 :
Q: 연차 신청은 언제까지 해야 하나요?
A: [근태규정]에 따르면 연차는 최소 3일 전까지 신청해야 합니다.

"""
    prompt = f"""{fewshot}
지금까지의 대화 내용:
{history_text}

Question: {question}
Answer:"""
    response = llm.invoke(prompt)
    updated_history = full_history + [f"Q: {question}\nA: {response.content}"]
    return {**state, "answer": response.content, "chat_history": updated_history}

# 답변 평가
def judge_answer(state: AgentState) -> AgentState:
    context = "\n---\n".join(state.get("contexts", []))
    question = state.get("rewritten_question") or state["question"]
    answer = state["answer"]
    prompt = f"""다음은 질문과 답변, 그리고 참고 context입니다.

Question: {question}
Context: {context}
Answer: {answer}

답변이 충분한가요? 다음 형식으로 평가하세요:

- 평가: [충분|부족]
- 이유: ..."""
    reflection = llm.invoke(prompt)
    return {**state, "reflection": reflection.content}

# 리플렉션 결과 판단 + 최대 재작성 제한
def decide_to_reflect(state: AgentState) -> str:
    if state.get("rewrite_count", 0) >= 2:
        return "end"
    reflection = state.get("reflection", "")
    return "end" if any(kw in reflection for kw in ["충분", "문제없음", "적절"]) else "rewrite"

# 질문 재작성
def reformulate_question(state: AgentState) -> AgentState:
    question = state.get("rewritten_question") or state["question"]
    answer = state["answer"]
    context = "\n---\n".join(state.get("contexts", []))
    prompt = f"""답변이 부족하다면, 질문을 좀 더 명확하고 구체적으로 바꿔 주세요.

기존 질문: {question}
답변: {answer}
Context: {context}

보강 질문:"""
    new_q = llm.invoke(prompt).content.strip()
    count = state.get("rewrite_count", 0) + 1
    return {**state, "rewritten_question": new_q, "rewrite_count": count}

# LangGraph 구성
builder = StateGraph(AgentState)
builder.add_node("decide", decide_use_rag)
builder.add_node("search", search_documents)
builder.add_node("answer", generate_answer)
builder.add_node("judge", judge_answer)
builder.add_node("rewrite", reformulate_question)
builder.add_node("direct_answer", direct_answer)

builder.set_entry_point("decide")

builder.add_conditional_edges("decide", get_use_rag_condition, {
    "use_rag": "search",
    "skip_rag": "direct_answer"
})
builder.add_edge("search", "answer")
builder.add_edge("answer", "judge")
builder.add_conditional_edges("judge", decide_to_reflect, {
    "end": END,
    "rewrite": "search"
})
builder.add_edge("rewrite", "search")
builder.add_edge("direct_answer", END)

graph = builder.compile()

# 실행 루프
def run_agent():
    print("LangGraph 기반 Agentic RAG 시작 (종료: exit)")
    state: AgentState = {"chat_history": [], "rewrite_count": 0}

    while True:
        question = input("\n질문을 입력하세요: ")
        if question.strip().lower() == "exit":
            print("종료합니다.")
            break

        state["question"] = question
        state.pop("rewritten_question", None)
        state["rewrite_count"] = 0  # 질문마다 카운터 초기화

        start = time.time()
        final_state = graph.invoke(state)
        duration = time.time() - start
        logging.info(f"[run_agent] 처리 완료 (소요 시간: {duration:.2f}초)")

        print(f"\n🧠 최종 답변:\n{final_state.get('answer', '[응답 없음]')}")
        state["chat_history"] = final_state.get("chat_history", [])

if __name__ == "__main__":
    run_agent()
