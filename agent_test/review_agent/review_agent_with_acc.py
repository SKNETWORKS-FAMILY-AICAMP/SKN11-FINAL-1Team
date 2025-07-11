# 평가점수가 반영된 agent 코드
# 
# 
import sqlite3
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o",
    openai_api_key=openai_api_key
)

job = 'IT 개발자'

# 하위 subtasks 조회
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

# 상위 task 제목 조회
def fetch_task_title(task_id: int):
    conn = sqlite3.connect("my_database2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "알 수 없는 작업"

# 평가 지표별 프롬프트 정의
def get_score(prompt: str) -> float:
    response = llm.invoke(prompt)
    try:
        score = float(response.content.strip())
        return max(0.0, min(score, 1.0))  # Clamp between 0.0 and 1.0
    except ValueError:
        return -1.0  # Invalid score

# 평가 루틴
def evaluate_feedback(feedback: str, task_title: str, subtasks: list) -> dict:
    subtask_text = "\n".join([
        f"- {title.strip()}: {content.strip() if content else '내용 없음'}"
        for title, content in subtasks
    ]) or "관련 하위 작업 없음"

    prompts = {
        "answer_relevancy": f"""
        아래 피드백은 '{task_title}'라는 주제와 하위 작업들에 대해 잘 관련되어 있는가?
        주제 적합도(관련성)를 0.0에서 1.0 사이 점수로 평가해줘.

        [상위 제목]: {task_title}
        [하위 작업들]:
        {subtask_text}

        [피드백]:
        {feedback}

        점수만 숫자로 출력:
        """,

        "faithfulness": f"""
        아래 피드백은 상위 제목 및 하위 작업들에 기반하여 작성되었는가?
        없는 사실을 만들거나 조작한 표현 없이 충실하게 작성되었는지 0.0~1.0 점수로 평가해줘.

        [상위 제목]: {task_title}
        [하위 작업들]:
        {subtask_text}

        [피드백]:
        {feedback}

        점수만 숫자로 출력:
        """,

        "answer_correctness": f"""
        아래 피드백은 문법, 구성, 표현력 등 전반적으로 리뷰로서의 품질이 우수한가?
        작성 품질을 0.0~1.0 점수로 평가해줘.

        [피드백]:
        {feedback}

        점수만 숫자로 출력:
        """
    }

    return {
        metric: get_score(prompt)
        for metric, prompt in prompts.items()
    }

# 피드백 생성 + 평가
def get_feedback_on_task(task_id: int):
    subtasks = fetch_subtasks_for_task(task_id)
    task_title = fetch_task_title(task_id)

    if not task_title:
        return "❌ 상위 태스크가 존재하지 않습니다."

    if not subtasks:
        prompt = f"""
        너는 사내 온보딩 과제를 평가하는 멘토야. 판단할 업무 제목은 '{task_title}'야.
        제목을 기반으로 아래와 같은 형식으로 전체적인 피드백을 전문가처럼 작성해줘
                
        각 하위 작업을 참고해서 아래와 같은 형식으로 전체적인 피드백을 전문가처럼 작성해줘
        코드가 있을 시, 코드 리뷰도 포함해서 작성해줘 


        - 👍 잘된 점:
        - 🔧 개선할 점:
        - 🧾 요약 피드백: 
        """
    else:
        subtask_descriptions = "\n".join([
            f"- {title.strip()}: {content.strip() if content else '내용 없음'}"
            for title, content in subtasks
        ])

        prompt = f"""
        너는 사내 온보딩 과제를 평가하는 멘토야. 판단할 업무 제목은 '{task_title}'야.
        제목을 기반으로 아래와 같은 형식으로 전체적인 피드백을 전문가처럼 작성해줘
                
        각 하위 작업을 참고해서 아래와 같은 형식으로 전체적인 피드백을 전문가처럼 작성해줘
        코드가 있을 시, 코드 리뷰도 포함해서 작성해줘 


        - 👍 잘된 점:
        - 🔧 개선할 점:
        - 🧾 요약 피드백: 
        """

    feedback = llm.invoke(prompt).content
    scores = evaluate_feedback(feedback, task_title, subtasks)

    return feedback, scores


if __name__ == "__main__":
    task_id = 1
    feedback, scores = get_feedback_on_task(task_id)

    print("📋 피드백:\n")
    print(feedback)

    print("\n📊 자동 평가 점수:")
    for metric, score in scores.items():
        if score == -1.0:
            print(f"❌ {metric}: 평가 실패 (LLM 응답 오류)")
        else:
            print(f"{metric}: {score:.2f}")
