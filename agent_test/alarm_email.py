import sqlite3
import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# 내부 메일 전송 함수 (비동기)
async def send_email(to_email, report_url, from_email, from_password):
    conf = ConnectionConfig(
        MAIL_USERNAME=from_email,
        MAIL_PASSWORD=from_password,
        MAIL_FROM=from_email,
        MAIL_PORT=587,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True
    )

    message = MessageSchema(
        subject="신입사원 최종 평가 보고서 도착",
        recipients=[to_email],
        body=f"""
        <h3>최종 평가 보고서가 도착했습니다.</h3>
        <p>아래 링크를 통해 확인하세요:</p>
        <a href="{report_url}">{report_url}</a>
        """,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

# LangGraph 노드용 함수 (핵심 로직)
def alarm_agent_node(inputs: dict) -> dict:
    mentee_id = inputs["mentee_id"]
    report_url = inputs["report_url"]

    conn = sqlite3.connect("sample.db")  # 우리꺼 db로 수정해줘야함. 
    cursor = conn.cursor()

    # 멘토 ID 조회
    cursor.execute("SELECT mentor_id FROM mentorship WHERE mentee_id = ?", (mentee_id,))
    result = cursor.fetchone() # 멘토가 있는지 확인
    if not result:
        return {"status": "fail", "reason": "멘토 없음"}
    mentor_id = result[0]

    # 멘토 이메일 조회
    cursor.execute("SELECT personal_email FROM user WHERE user_id = ?", (mentor_id,))
    result = cursor.fetchone() # 멘토 이메일이 있는지 확인
    if not result:
        return {"status": "fail", "reason": "멘토 이메일 없음"}
    mentor_email = result[0]

    # 발신자 이메일 설정 조회
    cursor.execute("SELECT sender_email, sender_password FROM email_config ORDER BY created_at DESC LIMIT 1")
    result = cursor.fetchone() # 발신자 설정이 있는지 확인
    if not result:
        return {"status": "fail", "reason": "발신자 설정 없음"}
    sender_email, sender_password = result

    print(f"📤 LangGraph: {sender_email} → {mentor_email}")

    try:
        asyncio.run(send_email(mentor_email, report_url, sender_email, sender_password))
    except Exception as e:
        return {"status": "fail", "error": str(e)}

    conn.close()
    return {
        "status": "success",
        "sent_to": mentor_email
    }

# LangGraph에서 불러쓸 수 있도록 노드로 export
alarm_agent = alarm_agent_node



# 이건 그냥 테스트용
if __name__ == "__main__":
    result = alarm_agent_node({
        "mentee_id": 1002,
        "report_url": "https://sinip.company/report/1"
    })
    print(result)
