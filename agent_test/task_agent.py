import os
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


# 프론트에서 집어넣을 descriptiion 예시!!!!!!
# AI 엔지니어 신입을 위한 커리큘럼입니다. 전체 기간은 12주이고, 목적은 실무 투입 전 프로젝트 역량과 팀 협업 능력을 평가하기 위함입니다.

# 테스트 실행 (예시 입력)
if __name__ == "__main__":
    input_data = CurriculumInput(
        curriculum_title="AI 엔지니어 온보딩",
        curriculum_description="신입 AI 엔지니어를 위한 12주 온보딩. 실습 중심이며, 프로젝트 기반으로 구성됨.",
        job_role="AI 엔지니어",
        weeks=12,
        goal="신입사원의 기술 적응과 프로젝트 수행 역량 평가"
    )

    draft = generate_curriculum_draft(input_data)
    print("\n📘 생성된 커리큘럼 초안:")
    print(draft)
