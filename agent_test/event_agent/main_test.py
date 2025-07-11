import sqlite3
import time
from datetime import date, timedelta, datetime
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# ✅ 환경변수 로딩
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

DB_PATH = "sample.db"

class AgentState(TypedDict, total=False):
    last_status_map: dict
    alerts: List[str]
    last_deadline_check: str  # 날짜 형식 문자열 (예: '2025-07-10')
# 태스크 번호 {task_id}, 제목: \"{title}\"가 검토 요청 상태로 변경되었습니다.
# 
# ✅ 알림 메시지 생성 함수
def review_alert_message(task_id, title):
    prompt = f"""
{task_id}번 태스크 [{title}]가 검토 요청 상태로 변경되었습니다.
멘토에게 검토를 요청하는 메시지를 짧고 간결하게 작성해 주세요.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def deadline_alert_message(message_block):
    prompt = f"""
"안녕하세요, 담당자님. 오늘의 날짜는 2025-07-11 입니다."처럼 오늘의 날짜를 맨 앞에 명시해주고 내용을 작성해주세요.
다음은 마감 일정에 따른 태스크 목록입니다. 담당자에게 전달할 알림 메시지를 짧고 간결하게 작성해 주세요.
메세지에는 일정에 대한 내용만 포함시켜주세요.


{message_block}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# ✅ 현재 상태 로드
def load_current_status():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT task_assign_id, title, status FROM task_assignment")
    rows = cur.fetchall()
    conn.close()
    return {row[0]: {"title": row[1], "status": row[2]} for row in rows}

# ✅ 상태 변경 감지 노드
def detect_status_change(state: AgentState) -> AgentState:
    last_status = state.get("last_status_map", {})
    current = load_current_status()
    alerts = []

    for task_id, info in current.items():
        old = last_status.get(task_id)
        if old:
            if info["status"] == "검토 요청" and old["status"] in ["진행 전", "진행 중"]:
                print(f"📡 감지: {task_id}번 태스크 [{info['title']}] → '검토 요청'")
                msg = review_alert_message(task_id, info['title'])
                alerts.append(msg)
                print("🤖 상태 변경 감지 응답:")
                print(msg)
                print()

    return {
        "last_status_map": current,
        "alerts": alerts,
        "last_deadline_check": state.get("last_deadline_check")  # 그대로 유지
    }

# ✅ 마감 일정 감지 노드 (하루 한 번만 실행)
def check_deadline_tasks(state: AgentState) -> AgentState:
    today_str = date.today().isoformat()
    if state.get("last_deadline_check") == today_str:
        return state  # 오늘 이미 실행함

    today = date.today()
    tomorrow = today + timedelta(days=1)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    def fetch(query, param):
        cur.execute(query, param)
        return cur.fetchall()

    due_today = fetch("SELECT task_assign_id, title FROM task_assignment WHERE DATE(scheduled_end_date) = ?", (today,))
    overdue = fetch("SELECT task_assign_id, title FROM task_assignment WHERE DATE(scheduled_end_date) < ? AND status != '완료'", (today,))
    due_tomorrow = fetch("SELECT task_assign_id, title FROM task_assignment WHERE DATE(scheduled_end_date) = ?", (tomorrow,))

    def format(tasks, headline):
        if not tasks:
            return ""
        lines = [f"{tid}번 태스크 [{title}]" for tid, title in tasks]
        return f"{headline} {len(tasks)}건 있습니다.\n" + "\n".join(lines)

    message_block = "\n\n".join(filter(None, [
        format(due_today, "오늘까지 처리해야 할 태스크가"),
        format(due_tomorrow, "내일까지 처리해야 할 태스크가"),
        format(overdue, "마감기한이 지난 태스크가")
    ]))

    if message_block:
        response = deadline_alert_message(message_block)
        print("🗓️ 마감 일정 감지 응답:")
        print(response)
        print()

    conn.close()
    state["last_deadline_check"] = today_str
    return state

# ✅ LangGraph 구성
builder = StateGraph(AgentState)
builder.add_node("detect_status_change", detect_status_change)
builder.add_node("check_deadline_tasks", check_deadline_tasks)
builder.set_entry_point("detect_status_change")
builder.add_edge("detect_status_change", "check_deadline_tasks")
builder.add_edge("check_deadline_tasks", END)
graph = builder.compile()

# ✅ 실행 루프
if __name__ == "__main__":
    print("🤖 LangGraph 기반 태스크 모니터링 실행 중...")
    state: AgentState = {"last_status_map": {}, "last_deadline_check": ""}
    while True:
        state = graph.invoke(state)
        time.sleep(5)
