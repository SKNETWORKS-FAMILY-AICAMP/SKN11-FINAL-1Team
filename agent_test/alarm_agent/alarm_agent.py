from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

# 슬랙 봇 설정 -> 슬랙 앱에서 봇 토큰을 발급받아야 함.
# 슬랙 please 봇 토큰
BOT_TOKEN = ""

# 비공개 채널이면 봇이 초대되어있어야함.
PRIVATE_CHANNEL_ID = ""  

# 이벤트 입력 모델
class EventInput(BaseModel):
    event: str

# 고정 메시지 맵핑
def get_test_message(event: str):
    messages = {
        "review_done": "📢 리뷰가 작성되었습니다. 확인해주세요!",
        "report_done": "📄 보고서가 제출되었습니다. 검토해주세요!",
        "finalized": "🧾 최종 평가 보고서가 완료되었습니다!"
    }
    return messages.get(event)

# 알림 전송 API -> alarm_agent가 post 요청을 보내면 이 함수가 실행됨.
@app.post("/event")
async def handle_event(payload: EventInput):
    message = get_test_message(payload.event)
    if not message:
        raise HTTPException(status_code=400, detail="지원되지 않는 이벤트입니다.")

    headers = { # 슬랙 api에 요청을 보낼 때 필요한 헤더
        "Authorization": f"Bearer {BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = { # 슬랙에 보낼 데이터
        "channel": PRIVATE_CHANNEL_ID,
        "text": message
    }

    # httpx.AsyncClient를 사용하여 slack api에 비동기 POST 요청을 보냄
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload
        )
        print("🔵 Slack 응답:", response.text)

        if response.status_code != 200 or not response.json().get("ok"):
            raise HTTPException(status_code=500, detail=f"Slack 전송 실패: {response.text}")

    return {"status": "sent", "message": message}
