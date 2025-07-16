import sqlite3
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing import TypedDict, List, Tuple, Optional
from langgraph.graph import StateGraph, END

# 환경 변수 로드 및 LLM 초기화
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o",
    openai_api_key=openai_api_key
)

job = 'IT 개발자'

# ✅ 하위 subtasks 조회
def fetch_subtasks_for_task(task_id: int):
    conn = sqlite3.connect("my_database2.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, content
        FROM subtasks
        WHERE task_id = ?
    """, (task_id,))
    results = cursor.fetchall()
    conn.close()
    return results

# ✅ 상위 task 정보 조회 (title, guide, content)
def fetch_task_details(task_id: int):
    conn = sqlite3.connect("my_database2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, guide, content FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None, None)

# ✅ LangGraph 상태 정의
class HierarchicalState(TypedDict):
    task_id: int
    task_title: Optional[str]
    task_guide: Optional[str]
    task_content: Optional[str]
    subtasks: List[Tuple[str, str]]
    subtask_reviews: List[str]
    feedback: str
    error: Optional[str]

# ✅ 노드 1: 데이터 조회
def fetch_data_node(state: HierarchicalState) -> HierarchicalState:
    task_id = state["task_id"]
    
    # 상위 task 정보 조회
    task_title, task_guide, task_content = fetch_task_details(task_id)
    if not task_title:
        return {
            **state,
            "error": "❌ 상위 태스크가 존재하지 않습니다.",
            "feedback": "❌ 상위 태스크가 존재하지 않습니다."
        }
    
    # 하위 subtasks 조회
    subtasks = fetch_subtasks_for_task(task_id)
    
    return {
        **state,
        "task_title": task_title,
        "task_guide": task_guide,
        "task_content": task_content,
        "subtasks": subtasks,
        "subtask_reviews": [],
        "error": None
    }

# ✅ 노드 2: 개별 subtask 리뷰 생성
def individual_reviews_node(state: HierarchicalState) -> HierarchicalState:
    if state.get("error"):
        return state
    
    task_title = state["task_title"]
    subtasks = state["subtasks"]
    subtask_reviews = []
    
    for subtask_title, subtask_content in subtasks:
        prompt = f"""
        너는 {job}의 전문가이면서 사내 온보딩 과제를 평가하는 멘토야.

        상위 업무: '{task_title}'
        하위 작업: '{subtask_title}'
        작업 내용: {subtask_content if subtask_content else '내용 없음'}

        이 하위 작업에 대해 간단한 개별 평가를 해줘:
        - 👍 잘된 점 (1-2줄)
        - 🔧 개선할 점 (1-2줄)
        """
        review = llm.invoke(prompt).content
        subtask_reviews.append(review)
    
    return {
        **state,
        "subtask_reviews": subtask_reviews
    }

# ✅ 노드 3: 종합 리뷰 생성
def comprehensive_review_node(state: HierarchicalState) -> HierarchicalState:
    if state.get("error"):
        return state
    
    task_title = state["task_title"]
    task_guide = state["task_guide"]
    task_content = state["task_content"]
    subtask_reviews = state["subtask_reviews"]
    
    reviews_text = "\n".join([
        f"하위 작업 {i+1}: {review}" for i, review in enumerate(subtask_reviews)
    ])
    
    prompt = f"""
    너는 {job}의 전문가이면서 사내 온보딩 과제를 평가하는 멘토야.

    🔹 상위 업무: {task_title}
    🔹 업무 가이드: {task_guide if task_guide else '없음'}
    🔹 업무 내용: {task_content if task_content else '없음'}

    🔸 각 하위 작업별 개별 리뷰:
    {reviews_text}

    위의 개별 리뷰들을 종합하여 상위 업무 기준으로 전체 피드백을 작성해줘:

    - 👍 전체적으로 잘된 점: (업무 목표 달성, 일관성, 완성도 등)
    - 🔧 전체적으로 개선할 점: (구조적 문제, 누락된 부분 등)
    - 🧾 종합 피드백: (멘토로서 조언, 다음 단계 제안 등)

    응답 시작:
    """
    feedback = llm.invoke(prompt).content
    
    return {
        **state,
        "feedback": feedback
    }

# ✅ 노드 4: 상위 업무만 리뷰 (하위 작업이 없는 경우)
def task_only_review_node(state: HierarchicalState) -> HierarchicalState:
    if state.get("error"):
        return state
    
    task_title = state["task_title"]
    task_guide = state["task_guide"]
    task_content = state["task_content"]
    
    prompt = f"""
    너는 {job}의 전문가이면서 사내 온보딩 과제를 평가하는 멘토야.

    🔹 업무 제목: {task_title}
    🔹 업무 가이드: {task_guide if task_guide else '없음'}
    🔹 업무 내용: {task_content if task_content else '없음'}

    하위 작업이 없는 상태에서 상위 업무만을 기반으로 피드백을 작성해줘:

    - 👍 잘된 점
    - 🔧 개선할 점
    - 🧾 종합 피드백

    응답 시작:
    """
    feedback = llm.invoke(prompt).content
    
    return {
        **state,
        "feedback": feedback
    }

# ✅ 조건부 라우팅 함수
def route_after_data_fetch(state: HierarchicalState) -> str:
    if state.get("error"):
        return END
    
    if state["subtasks"]:
        return "individual_reviews"
    else:
        return "task_only_review"

# ✅ LangGraph 워크플로우 구성
def create_hierarchical_feedback_graph():
    graph = StateGraph(HierarchicalState)
    
    # 노드 추가
    graph.add_node("fetch_data", fetch_data_node)
    graph.add_node("individual_reviews", individual_reviews_node)
    graph.add_node("comprehensive_review", comprehensive_review_node)
    graph.add_node("task_only_review", task_only_review_node)
    
    # 엣지 설정
    graph.set_entry_point("fetch_data")
    
    # 조건부 라우팅
    graph.add_conditional_edges(
        "fetch_data",
        route_after_data_fetch,
        {
            "individual_reviews": "individual_reviews",
            "task_only_review": "task_only_review"
        }
    )
    
    graph.add_edge("individual_reviews", "comprehensive_review")
    graph.add_edge("comprehensive_review", END)
    graph.add_edge("task_only_review", END)
    
    return graph.compile()

# ✅ 메인 피드백 생성 함수
def get_hierarchical_feedback_on_task(task_id: int):
    start = time.time()
    
    # 그래프 생성
    app = create_hierarchical_feedback_graph()
    
    # 초기 상태
    initial_state = HierarchicalState(
        task_id=task_id,
        task_title=None,
        task_guide=None,
        task_content=None,
        subtasks=[],
        subtask_reviews=[],
        feedback="",
        error=None
    )
    
    # 실행
    result = app.invoke(initial_state)
    
    elapsed = time.time() - start
    return result["feedback"], elapsed

# ✅ 실행 예시
if __name__ == "__main__":
    task_id = 1
    feedback, elapsed_time = get_hierarchical_feedback_on_task(task_id)

    print("📋 피드백:\n")
    print(feedback)
    print(f"\n⏱️ 응답 시간: {elapsed_time:.2f}초")