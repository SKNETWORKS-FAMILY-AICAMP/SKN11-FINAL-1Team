from openai import OpenAI
import os

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def review_alert_message(task_id, title):
    prompt = f"""
태스크 번호 {task_id}, 제목: "{title}"가 검토 요청 상태로 변경되었습니다.
멘토에게 전달할 메시지를 공손하게 작성해 주세요.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
