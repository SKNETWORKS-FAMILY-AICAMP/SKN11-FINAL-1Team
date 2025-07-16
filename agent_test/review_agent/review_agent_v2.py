# get_hierarchical_feedback_on_task 방식
# 
import sqlite3
import os
import time
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

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

# ✅ 하위 태스크별 개별 리뷰 생성
def get_individual_subtask_review(task_title: str, subtask_title: str, subtask_content: str):
    prompt = f"""
    너는 {job}의 전문가이면서 사내 온보딩 과제를 평가하는 멘토야.

    상위 업무: '{task_title}'
    하위 작업: '{subtask_title}'
    작업 내용: {subtask_content if subtask_content else '내용 없음'}

    이 하위 작업에 대해 간단한 개별 평가를 해줘:
    - 👍 잘된 점 (1-2줄)
    - 🔧 개선할 점 (1-2줄)
    """
    return llm.invoke(prompt).content

# ✅ 전체 종합 리뷰 생성
def get_comprehensive_review(task_title: str, task_guide: str, task_content: str, subtask_reviews: list):
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
    return llm.invoke(prompt).content

# ✅ 메인 피드백 생성 함수 (계층적 방식)
def get_hierarchical_feedback_on_task(task_id: int):
    task_title, task_guide, task_content = fetch_task_details(task_id)
    if not task_title:
        return "❌ 상위 태스크가 존재하지 않습니다.", 0.0

    subtasks = fetch_subtasks_for_task(task_id)

    start = time.time()

    if not subtasks:
        # 하위 작업이 없을 경우 상위 업무만 리뷰
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
    else:
        # 하위 작업이 있을 경우: 각각 리뷰 후 종합
        subtask_reviews = []
        for subtask_title, subtask_content in subtasks:
            review = get_individual_subtask_review(task_title, subtask_title, subtask_content)
            subtask_reviews.append(review)

        feedback = get_comprehensive_review(task_title, task_guide, task_content, subtask_reviews)

    elapsed = time.time() - start
    return feedback, elapsed


# ✅ 실행 예시
if __name__ == "__main__":
    task_id = 1
    feedback, elapsed_time = get_hierarchical_feedback_on_task(task_id)

    print("📋 피드백:\n")
    print(feedback)
    print(f"\n⏱️ 응답 시간: {elapsed_time:.2f}초")
