import os
import json
import re
from dataclasses import dataclass
from typing import TypedDict
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, END

# 환경 변수 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
DB_PATH = "sample.db"

# 상태 스키마 정의
class TaskState(TypedDict):
    input_data: dict
    tasks: list

# 커리큘럼 입력 모델
@dataclass
class CurriculumInput:
    curriculum_title: str
    curriculum_description: str

# 프롬프트 생성 함수
def generate_prompt(data: CurriculumInput) -> str:
    return f"""
너는 온보딩 커리큘럼 기획 전문가야.
아래 정보를 바탕으로 커리큘럼 초안을 주차별로 요약해서 만들어줘.

- 커리큘럼 제목: {data.curriculum_title}
- {data.curriculum_description}

출력은 반드시 아래 형식처럼 반환해. 설명, 문장, 다른 텍스트를 포함하지 마.
1주차: ...
- ...
- ...
2주차: ...
- ...
- ...
...
"""

# 커리큘럼 초안 생성 함수
def generate_curriculum_draft(data: CurriculumInput) -> str:
    prompt = generate_prompt(data)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 커리큘럼 작성 전문가야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# 세부 Task 생성 함수
def generate_task_details(title: str, description: str, weekly_plan: str) -> list:
    prompt = f"""
너는 프로젝트 매니저야. 아래 커리큘럼을 참고하여 세부 Task들을 작성해.

커리큘럼 제목: {title}
커리큘럼 설명: {description}
초안:
{weekly_plan}

**출력은 반드시 아래 JSON 배열만 반환해. 설명, 문장, 다른 텍스트를 포함하지 마.**

JSON 형식:
[
  {{
    "title": "Task 이름",
    "guideline": "Task 가이드라인",
    "description": "Task에 대한 템플릿 구조 (멘티가 작성할 수 있는 항목 예: '1) 배운 점:\\n2) 개선할 점:')",
    "week": 몇 주차인지(정수 타입),
    "period": Task 수행 기간 (몇 일 걸리는 일인지) (정수 타입),
    "priority": "상/중/하 중 하나"
  }},
  ...
]
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 세부 Task를 설계하는 프로젝트 매니저야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    content = response.choices[0].message.content
    try:
        tasks = json.loads(content)
    except json.JSONDecodeError:
        content = content.strip("```json").strip("```").strip()
        tasks = json.loads(content)
    return tasks

# 전체 Task 생성 함수
def generate_all_tasks(data: CurriculumInput) -> list:
    draft = generate_curriculum_draft(data)
    print(draft)

    weekly_plans = re.findall(r"\d+주차:.*?(?=\n\d+주차:|\Z)", draft, re.S)
    all_tasks = []

    for week_index, weekly_plan in enumerate(weekly_plans, start=1):
        tasks = generate_task_details(
            title=data.curriculum_title,
            description=data.curriculum_description,
            # week_num=week_index,
            weekly_plan=weekly_plan
        )
        all_tasks.extend(tasks)
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
    return all_tasks

# LangGraph 노드 정의
def curriculum_node(state: TaskState):
    data_dict = state["input_data"]
    data = CurriculumInput(**data_dict)
    tasks = generate_all_tasks(data)
    return {"tasks": tasks}

# LangGraph 워크플로우 구성
def build_langgraph():
    graph = StateGraph(TaskState)
    graph.add_node("generate_tasks", curriculum_node)
    graph.set_entry_point("generate_tasks")
    graph.add_edge("generate_tasks", END)
    return graph



if __name__ == "__main__":
    input_data = CurriculumInput(
        curriculum_title="AI 엔지니어 온보딩",
        curriculum_description="신입 AI 엔지니어를 위한 6주 온보딩. 실습 중심이며, 프로젝트 기반으로 구성됨.",
        # job_role="AI 엔지니어",
        # weeks=6,
        # goal="신입사원의 기술 적응과 프로젝트 수행 역량 평가"
    )

    workflow = build_langgraph()
    app = workflow.compile()  # 실행 가능한 그래프로 컴파일
    result = app.invoke({"input_data": input_data.__dict__})
    all_tasks = result["tasks"]

    with open("tasks_6weeks.json", "w", encoding="utf-8") as f:
        json.dump(all_tasks, f, ensure_ascii=False, indent=2)
    print("\n✅ 전체 Task가 tasks_6weeks.json 파일로 저장되었습니다.")
