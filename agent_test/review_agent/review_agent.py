import sqlite3
import os
import time
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

# 피드백 생성 + 응답시간 측정
def get_feedback_on_task(task_id: int):
    subtasks = fetch_subtasks_for_task(task_id)
    task_title = fetch_task_title(task_id)

    if not task_title:
        return "❌ 상위 태스크가 존재하지 않습니다.", 0.0

    if not subtasks:
        prompt = f"""
        너는 {job} 의 전문가이면서 사내 온보딩 과제를 평가하는 멘토야.
        상위 업무 제목은 '{task_title}'야.
                
        제목을 기반으로 아래와 같은 형식으로 전체적인 피드백을 전문가처럼 작성해줘
        코드가 있을 시, 코드 리뷰도 포함해서 작성해줘 

        {subtask_descriptions}
            
        각 하위 작업을 참고해서 아래와 같은 형식으로 전체적인 피드백을 전문가처럼 작성해줘
        코드가 있을 시, 코드 리뷰도 포함해서 작성해줘 

        아래는 예시야.
        ---

        예시 피드백:
        - 👍 잘된 점: 로그인 UI가 직관적이며 컴포넌트 분리가 잘 되어 있어 유지보수에 유리합니다. API 호출 시 비동기 처리를 적절히 사용한 점도 좋았습니다.
        - 🔧 개선할 점: 로그인 실패 시 에러 메시지가 콘솔에만 출력되고 사용자에게 전달되지 않는 문제가 있습니다. UX 개선이 필요합니다.
        - 🧾 요약 피드백: 전반적으로 구조적이고 깔끔하게 구성되어 있으나, 사용자 피드백 처리 측면에서 개선 여지가 있습니다.

        ---

        응답 시작:
        """
    else:
        subtask_descriptions = "\n".join([
            f"- {title.strip()}: {content.strip() if content else '내용 없음'}"
            for title, content in subtasks
        ])

        prompt = f"""
        너는 {job} 분야의 전문가이자, 사내 온보딩 과제를 평가하는 멘토이자 HR 담당자야.
        상위 업무 제목은 '{task_title}'야.

        너의 피드백은 **정확하고 냉철하며 직설적**이어야 해.  
        - 잘된 부분은 간결하고 구체적하되,  
        - 부족하거나 기준 미달인 부분은 돌려 말하지 말고 명확하게 지적하고 개선 방향을 제시해.  
        - 특히 완성도가 낮거나 기본적인 요구사항조차 충족하지 못했다면 단호하게 비판하고, 평가 기준에 미달했다고 알려줘.  

        하위 작업 목록:
        {subtask_descriptions}

        아래 형식으로 전체 피드백을 작성해. 코드가 있을 경우 코드 리뷰도 반드시 포함해.

        <structure>

        - 👍 잘된 점: 구체적으로 작성. 단순 칭찬보다는 어떤 점이 왜 좋은지 전문가 관점에서 설명.
        - 🔧 개선할 점: 부족하거나 미흡한 부분을 냉철하게 지적. 필요하다면 "이 상태로는 실무 적용 불가"와 같이 단호한 어조 사용.
        - 🧾 피드백: 전반적인 완성도에 대한 총평. 필요하다면 가혹한 평가도 허용. (예: “기본 요구사항조차 충족하지 못해 재작업이 필요합니다.”)

        </structure>

        평가는 HR 담당자가 실제로 온보딩 과제를 평가하듯, **사실에 기반하여 냉정하고 객관적으로** 진행해. 잘된 점은 조금만 말하고, 부족한 점을 명확히 지적하는 데 집중해.
        """


    start = time.time()
    feedback = llm.invoke(prompt).content
    elapsed = time.time() - start

    return feedback, elapsed


if __name__ == "__main__":
    task_id = 1
    feedback, elapsed_time = get_feedback_on_task(task_id)

    print("📋 피드백:\n")
    print(feedback)

    print(f"\n⏱️ 응답 시간: {elapsed_time:.2f}초")