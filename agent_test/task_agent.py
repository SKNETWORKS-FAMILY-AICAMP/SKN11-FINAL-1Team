import os
import json
import re
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=openai_api_key)
DB_PATH = "sample.db"

# 커리큘럼 입력 모델
@dataclass
class CurriculumInput:
    curriculum_title: str
    curriculum_description: str
    job_role: str
    weeks: int
    goal: str

# 프롬프트 생성 함수
def generate_prompt(data: CurriculumInput) -> str:
    return f"""
너는 신입사원 온보딩 커리큘럼 기획 전문가야.
아래 정보를 바탕으로 총 {data.weeks}주차 일정으로 구성된 커리큘럼 초안을 주차별로 요약해서 만들어줘.

- 커리큘럼 제목: {data.curriculum_title}
- 설명: {data.curriculum_description}
- 직무: {data.job_role}
- 온보딩 목적: {data.goal}
- 기간: {data.weeks}주

형식은 다음과 같아:
1주차: ...
2주차: ...
...
"""

#  커리큘럼 초안 생성 함수 (신버전 OpenAI SDK 방식?)
def generate_curriculum_draft(data: CurriculumInput) -> str:
    prompt = generate_prompt(data)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 커리큘럼 작성 전문가야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_task_details(title: str, description: str, week_num: int, weekly_plan: str) -> list:
    prompt = f"""
너는 프로젝트 매니저야. 아래 커리큘럼을 참고하여 {week_num}주차의 세부 Task들을 작성해.

커리큘럼 제목: {title}
커리큘럼 설명: {description}
{week_num}주차 초안:
{weekly_plan}

**출력은 반드시 아래 JSON 배열만 반환해. 설명, 문장, 다른 텍스트를 포함하지 마.**

JSON 형식:
[
  {{
    "title": "Task 이름",
    "guide": "Task 가이드라인",
    "description": "Task에 대한 템플릿 구조 (멘티가 작성할 수 있는 항목 예: '1) 배운 점:\\n2) 개선할 점:')",
    "week": {week_num},
    "period": 1,
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
        temperature=0.7
    )
    content = response.choices[0].message.content

    try:
        tasks = json.loads(content)
    except json.JSONDecodeError:
        content = content.strip("```json").strip("```").strip()
        tasks = json.loads(content)
    return tasks


def generate_all_tasks(data: CurriculumInput) -> list:
    # 1. 커리큘럼 초안 생성
    draft = generate_curriculum_draft(data)
    print("\n📘 생성된 커리큘럼 초안:")
    print(draft)

    # 2. 주차별 초안 분리 (정규식으로 각 주차 내용 나누기)
    weekly_plans = re.findall(r"\d+주차:.*?(?=\n\d+주차:|\Z)", draft, re.S)

    all_tasks = []
    # 3. 각 주차별 세부 Task 생성
    for week_index, weekly_plan in enumerate(weekly_plans, start=1):
        tasks = generate_task_details(
            title=data.curriculum_title,
            description=data.curriculum_description,
            week_num=week_index,
            weekly_plan=weekly_plan
        )
        all_tasks.extend(tasks)
        # JSON 리스트만 출력
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
    return all_tasks

if __name__ == "__main__":
    input_data = CurriculumInput(
        curriculum_title="AI 엔지니어 온보딩",
        curriculum_description="신입 AI 엔지니어를 위한 12주 온보딩. 실습 중심이며, 프로젝트 기반으로 구성됨.",
        job_role="AI 엔지니어",
        weeks=12,
        goal="신입사원의 기술 적응과 프로젝트 수행 역량 평가"
    )

    all_tasks = generate_all_tasks(input_data)

    # 4. 전체 Task JSON 파일로 저장
    with open("tasks_12weeks.json", "w", encoding="utf-8") as f:
        json.dump(all_tasks, f, ensure_ascii=False, indent=2)
    print("\n✅ 전체 Task가 tasks_12weeks.json 파일로 저장되었습니다.")
