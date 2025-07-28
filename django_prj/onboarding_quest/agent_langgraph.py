import os
import psycopg2
import psycopg2.extras
import time
import asyncio
import threading
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from datetime import date, timedelta, datetime
from typing import TypedDict, List, Optional, Tuple, Dict
from dataclasses import dataclass
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

# ✅ 환경 설정
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=openai_api_key)

# PostgreSQL 연결 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'onboarding_quest_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# Agent 스케줄 설정
AGENT_CONFIG = {
    'cycle_interval': int(os.getenv('AGENT_CYCLE_INTERVAL', 30)),  # 기본 30초
    'hourly_check': int(os.getenv('AGENT_HOURLY_CHECK', 1)),     # 기본 1시간
    'daily_check_hour': int(os.getenv('AGENT_DAILY_CHECK_HOUR', 9)),  # 기본 오전 9시
    'enabled': os.getenv('AGENT_ENABLED', 'True').lower() == 'true'   # 기본 활성화
}

# ✅ 상태 정의
class GraphState(TypedDict, total=False):
    messages: List[BaseMessage]
    user_input: Optional[str]
    current_task: Optional[str]
    last_status_map: dict
    last_deadline_check: str
    last_onboarding_check: str
    task_id: Optional[int]
    feedback: Optional[str]
    deadline_due: Optional[bool]
    pending_review: Optional[bool]
    onboarding_due: Optional[bool]
    completed_onboarding_ids: Optional[List[int]]
    report_generated_ids: Optional[List[int]]
    user_id: Optional[int]
    reviewed_task_ids: Optional[List[int]]

@dataclass
class TaskInfo:
    task_id: int
    title: str
    guide: str
    date: str
    content: str
    mentor_name: str
    subtasks: List[Dict]
    task_memos: List[Dict]
    task_reviews: List[Dict]

@dataclass
class ComprehensiveReportData:
    user_name: str
    user_role: str
    all_tasks: List[TaskInfo]
    overall_stats: Dict

# ✅ 현재 상태 맵 로드
def load_current_status_map():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT task_assign_id, title, status FROM core_taskassign")
    rows = cur.fetchall()
    conn.close()
    return {row[0]: {"title": row[1], "status": row[2]} for row in rows}

# ✅ 라우터
def route_node(state: GraphState) -> GraphState:
    return state

# def routing_condition(state: GraphState) -> str:
#     if state.get("onboarding_due") and state.get("user_id"):
#         return "check_onboarding_complete"
#     if state.get("pending_review"):
#         return "detect_status_change"
#     if state.get("deadline_due"):
#         return "check_deadline_tasks"
#     return "check_deadline_tasks"


def routing_condition(state: GraphState) -> str:
    if state.get("pending_review") and state.get("task_id") not in state.get("reviewed_task_ids", []):
        return "review_node"
    if state.get("onboarding_due") and state.get("user_id"):
        return "check_onboarding_complete"
    return "check_deadline_tasks"



class EventAgent:
    def run(self, state: dict) -> dict:
        print("EventAgent.run() 실행 시작")

    # ✅ 온보딩 상태 체크
        onboarding_state = self.check_completion(state)
        if onboarding_state.get("onboarding_due"):
            return onboarding_state

        # ✅ 중복 실행 방지 (오늘 이미 체크했다면 pass)
        today_str = date.today().isoformat()
        if state.get("last_deadline_check") == today_str:
            return state

        today = date.today()
        tomorrow = today + timedelta(days=1)

        # ✅ 멘티의 태스크 조회
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT u.user_id, u.first_name, ta.task_assign_id, ta.title, ta.scheduled_end_date, ta.status
            FROM core_taskassign ta
            JOIN core_mentorship ms ON ta.mentorship_id_id = ms.mentorship_id
            JOIN core_user u ON ms.mentee_id = u.user_id
            WHERE u.role = 'mentee'
        """)
        rows = cur.fetchall()
        conn.close()

        user_tasks = defaultdict(lambda: {"today": [], "tomorrow": [], "overdue": [], "name": ""})

        for uid, name, tid, title, end_date, status in rows:
            user_tasks[uid]["name"] = name
            if not end_date:
                continue
            try:
                d = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                continue

            if d == today:
                user_tasks[uid]["today"].append((tid, title))
            elif d == tomorrow:
                user_tasks[uid]["tomorrow"].append((tid, title))
            elif d < today and status != "완료":
                user_tasks[uid]["overdue"].append((tid, title))

        alarm_events = state.get("alarm_events", [])

        for uid, data in user_tasks.items():
            name = data["name"]
            today_tasks = data["today"]
            tomorrow_tasks = data["tomorrow"]
            overdue_tasks = data["overdue"]

            if not (today_tasks or tomorrow_tasks or overdue_tasks):
                continue

            lines = [
                f"안녕하세요, 멘티 {name}님.\n",
                f"\n오늘 날짜인 {today.isoformat()}을 기준으로, 처리해야 할 태스크와 관련하여 알림 드립니다.\n"
            ]

            if overdue_tasks:
                lines.append(f"🔴 마감일이 지난 태스크 {len(overdue_tasks)}건:\n")
                for tid, title in overdue_tasks:
                    lines.append(f" - {tid}번 태스크: **{title}**\n")

            if today_tasks:
                lines.append(f"🟡 오늘까지 처리해야 할 태스크 {len(today_tasks)}건:\n")
                for tid, title in today_tasks:
                    lines.append(f" - {tid}번 태스크: **{title}**\n")

            if tomorrow_tasks:
                lines.append(f"🟢 내일까지 처리해야 할 태스크 {len(tomorrow_tasks)}건:\n")
                for tid, title in tomorrow_tasks:
                    lines.append(f" - {tid}번 태스크: **{title}**\n")

            lines.append("\n각 태스크의 마감일을 놓치지 않도록 확인해 주세요. 필요한 경우 지원을 요청해 주세요. 감사합니다!")
            full_message = "\n".join(lines)

            # ✅ 알림 이벤트로 추가
            alarm_events.append({
                "event_type": "deadline_reminder",
                "user_id": uid,
                "message": full_message
            })

        # ✅ 상태에 저장
        state["alarm_events"] = alarm_events
        state["last_deadline_check"] = today_str
        return state

    


    def detect_status_change(self, state: dict) -> dict:
        print("detect_status_change() 실행 시작")

        last_status = state.get("last_status_map", {})
        reviewed_ids = set(state.get("reviewed_task_ids", []))

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT task_assign_id, title, status FROM core_taskassign")
        rows = cur.fetchall()
        conn.close()

        current = {row[0]: {"title": row[1], "status": row[2]} for row in rows}
        detected_task_id = None
        pending_review = False
        alarm_events = []

        for task_id, info in current.items():
            old = last_status.get(task_id)
            if not old:
                continue

            if (
                info["status"] == "검토 요청"
                and old["status"] in ["진행 전", "진행 중"]
                and task_id not in reviewed_ids
            ):
                prompt = f"{task_id}번 태스크 [{info['title']}]가 '검토 요청' 상태로 변경되었습니다. 멘토에게 보낼 메시지를 작성해주세요."
                alert = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                message = alert.choices[0].message.content.strip()
                
                # 멘토십 ID 조회를 위한 추가 쿼리
                conn_temp = psycopg2.connect(**DB_CONFIG)
                cur_temp = conn_temp.cursor()
                cur_temp.execute("SELECT mentorship_id_id FROM core_taskassign WHERE task_assign_id = %s", (task_id,))
                mentorship_row = cur_temp.fetchone()
                conn_temp.close()
                
                # 태스크로 이동할 수 있는 URL 생성 (mentorship_id 포함)
                if mentorship_row:
                    mentorship_id = mentorship_row[0]
                    task_url = f"/mentee/task_list/?mentorship_id={mentorship_id}&task_id={task_id}"
                else:
                    task_url = f"/mentee/task_list/?task_id={task_id}"  # fallback
                
                alarm_events.append({
                    "event_type": "task_review_requested",
                    # user_id가 필요하다면 별도 쿼리 필요
                    "message": message,
                    "task_id": task_id,
                    "url": task_url
                })
                detected_task_id = task_id
                pending_review = True

            elif (
                info["status"] == "완료"
                and old["status"] in ["진행 중", "검토 요청"]
            ):
                prompt = f"{task_id}번 태스크 [{info['title']}]가 멘토에 의해 '완료' 상태로 변경되었습니다. 멘티에게 보낼 메시지를 정중하게 작성해주세요."
                alert = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                message = alert.choices[0].message.content.strip()
                alarm_events.append({
                    "event_type": "task_completed_by_mentor",
                    # user_id가 필요하다면 별도 쿼리 필요
                    "message": message
                })

        state.update({
            "pending_review": pending_review,
            "task_id": detected_task_id,
            "last_status_map": current,
            "alarm_events": alarm_events
        })
        return state


    # 온보딩 완료 여부 확인하는 함수 -> 종료 시 멘토에게 알림 메시지 생성
    # 온보딩 종료 시점 자동 감지 -> 보고서 생성을 트리거 
    def check_completion(self, state: GraphState) -> GraphState:
        if state.get("onboarding_due") and state.get("user_id"):
            print("⏩ 이미 감지된 온보딩 상태, 중복 실행 방지")
            return state

        # 멘티별로 가장 늦은 태스크 마감일(MAX) 조회
        today_str = date.today().isoformat()
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT u.user_id, u.first_name, m.email, MAX(ta.scheduled_end_date)
            FROM core_taskassign ta
            JOIN core_mentorship ms ON ta.mentorship_id_id = ms.mentorship_id
            JOIN core_user u ON ms.mentee_id = u.user_id
            JOIN core_user m ON m.user_id = ms.mentor_id
            WHERE u.role = 'mentee'
            GROUP BY u.user_id, u.first_name, m.email
        """)
        rows = cur.fetchall()
        conn.close()

        # 이미 온보딩 완료된 멘티 ID 목록
        completed = state.get("completed_onboarding_ids", [])
        generated = state.get("report_generated_ids", [])

        # 이미 처리된 경우는 건너뛰고, 아직 종료 되지 않은 멘티만 검사
        for mentee_id, mentee_name, mentor_email, end_date_str in rows:
            if mentee_id in completed or mentee_id in generated:
                continue
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except:
                continue
            if end_date <= date.today():
                prompt = f"{mentee_name} 멘티의 온보딩 기간이 오늘로 종료되었습니다. 멘토({mentor_email})에게 보낼 메시지를 정중하게 작성해주세요."
                alert = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                print("🎓 온보딩 종료 알림:", alert.choices[0].message.content.strip())

                # 멘토에게 보고서 요청할 수 있도록 메시지 추가(HumanMessage는 LangGraph의 chat_history 용도임.)
                return {
                    **state,
                    "messages": [HumanMessage(content=f"{mentee_id}번 멘티의 보고서를 작성해줘")],
                    "user_id": mentee_id,
                    "onboarding_due": True, 
                    "last_onboarding_check": today_str,
                    "completed_onboarding_ids": completed + [mentee_id] # 완료된 멘티 추가해서 다음에 중복 트리거 방지함.
                }

        state["onboarding_due"] = False
        state["last_onboarding_check"] = today_str
        return state



class ReviewAgent:
    def review(self, state: GraphState) -> GraphState:
        task_id = state.get("task_id")
        print(f"🟡 [review] 시작 - task_id: {task_id}")

        if not task_id:
            print("⚠️ [review] task_id 없음. 종료")
            return state

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # task 정보 확인
        cur.execute("SELECT mentorship_id_id, title FROM core_taskassign WHERE task_assign_id = %s", (task_id,))
        row = cur.fetchone()
        if not row:
            print("❌ [review] 해당 task_assign 없음")
            conn.close()
            return state

        mentorship_id, task_title = row[0], row[1]
        print(f"🔍 [review] task_title: {task_title}, mentorship_id: {mentorship_id}")

        # 멘토 ID와 멘티 ID 조회
        cur.execute("SELECT mentor_id, mentee_id FROM core_mentorship WHERE mentorship_id = %s", (mentorship_id,))
        mentor_row = cur.fetchone()
        if not mentor_row:
            print("❌ [review] 멘토 ID 조회 실패")
            conn.close()
            return state

        mentor_id, mentee_id = mentor_row[0], mentor_row[1]
        print(f"✅ [review] mentor_id: {mentor_id}, mentee_id: {mentee_id}")

        # 하위 과제 가져오기 (parent 필드로 조회)
        cur.execute("SELECT title, description FROM core_taskassign WHERE parent_id = %s", (task_id,))
        subtasks = cur.fetchall()
        conn.close()

        if not subtasks:
            print("⚠️ [review] 서브태스크 없음")

        subtask_text = "\n".join([f"- {title.strip()}: {description.strip() or '내용 없음'}" for title, description in subtasks])

        # GPT 프롬프트 작성 및 요청
        prompt = f"""너는 IT 멘토입니다. 상위 업무는 '{task_title}'이고, 하위 작업은 다음과 같습니다:\n{subtask_text}\n다음 형식으로 피드백 작성:\n- 👍 잘한 점:\n- 🔧 개선할 점:\n- 🧾 요약 피드백:\n---"""
        feedback = llm.invoke(prompt).content
        print("📝 [review] 피드백 생성 완료")

        # DB에 피드백 저장 -> memo 테이블에 저장 (mentor_id를 null로 설정)
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "INSERT INTO core_memo (task_assign_id, comment, user_id) VALUES (%s, %s, %s)",
            (task_id, feedback, None)  # mentor_id 대신 None(null) 사용
        )
        conn.commit()
        conn.close()
        print(f"✅ [review] memo 저장 완료 (user_id=null, task_id={task_id})")

        # ✅ 알람 이벤트 생성 (mentorship_id 포함 URL)
        task_url = f"/mentee/task_list/?mentorship_id={mentorship_id}&task_id={task_id}"
        alarm_events = state.get("alarm_events", [])
        alarm_events.append({
            "event_type": "task_review_completed",
            "mentee_id": mentee_id,
            "message": f"{task_title} 태스크에 대한 멘토의 리뷰가 작성되었습니다. 확인해 주세요.",
            "url": task_url
        })

        return {
            **state,
            "feedback": feedback,
            "current_task": "reviewed",
            "pending_review": False,
            "task_id": None,
            "last_status_map": load_current_status_map(),
            "messages": [m for m in state.get("messages", []) if not isinstance(m, AIMessage)],
            "reviewed_task_ids": state.get("reviewed_task_ids", []) + [task_id],
            "alarm_events": alarm_events
        }



# ✅ ReportAgent 정의
class ReportAgent:
    def __init__(self, db_config: dict = None):
        self.db_config = db_config or DB_CONFIG
        self.llm = llm

    def get_connection(self) -> psycopg2.extensions.connection:
        conn = psycopg2.connect(**self.db_config)
        return conn

    def get_user_tasks(self, user_id: int) -> List[Tuple[int, str]]:
        with self.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT DISTINCT ta.task_assign_id, ta.title
                FROM core_taskassign ta
                JOIN core_mentorship m ON ta.mentorship_id_id = m.mentorship_id
                WHERE m.mentee_id = %s OR m.mentor_id = %s
                ORDER BY ta.task_assign_id
            """, (user_id, user_id))
            return [(row['task_assign_id'], row['title']) for row in cur.fetchall()]

    def fetch_single_task_data(self, task_id: int) -> Optional[TaskInfo]:
        with self.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT ta.*, 
                       CONCAT(u_mentee.last_name, u_mentee.first_name) as mentee_name, 
                       CONCAT(u_mentor.last_name, u_mentor.first_name) as mentor_name
                FROM core_taskassign ta
                JOIN core_mentorship m ON ta.mentorship_id_id = m.mentorship_id
                JOIN core_user u_mentee ON m.mentee_id = u_mentee.user_id
                JOIN core_user u_mentor ON m.mentor_id = u_mentor.user_id
                WHERE ta.task_assign_id = %s
            """, (task_id,))
            task_row = cur.fetchone()
            if not task_row:
                return None

            # 하위 태스크들과 메모, 리뷰 조회
            cur.execute("""
                SELECT s.task_assign_id, s.title, s.description, s.guideline,
                       s.scheduled_start_date, s.status
                FROM core_taskassign s
                WHERE s.parent_id = %s
                ORDER BY s.task_assign_id
            """, (task_id,))

            subtasks = []
            for row in cur.fetchall():
                # 각 서브태스크의 메모 조회
                cur.execute("""
                    SELECT comment FROM core_memo
                    WHERE task_assign_id = %s
                    ORDER BY create_date
                """, (row['task_assign_id'],))
                memos = [memo['comment'] for memo in cur.fetchall()]

                subtasks.append({
                    'subtask_id': row['task_assign_id'],
                    'title': row['title'],
                    'guide': row['guideline'],
                    'date': str(row['scheduled_start_date']) if row['scheduled_start_date'] else '',
                    'content': row['description'] or '',
                    'status': row['status'],
                    'memos': memos,
                    'reviews': [],  # 리뷰 시스템이 없으므로 빈 배열
                    'score': 0
                })

            # 태스크 레벨 메모 조회
            cur.execute("""
                SELECT comment, create_date FROM core_memo
                WHERE task_assign_id = %s
                ORDER BY create_date
            """, (task_id,))
            task_memos = [{'content': r['comment'], 'date': str(r['create_date'])} for r in cur.fetchall()]

            # 태스크 레벨 리뷰는 별도 테이블이 없으므로 빈 배열
            task_reviews = []

            return TaskInfo(
                task_id=task_row['task_assign_id'],
                title=task_row['title'],
                guide=task_row['guideline'] or '',
                date=str(task_row['scheduled_start_date']) if task_row['scheduled_start_date'] else '',
                content=task_row['description'] or '',
                mentor_name=task_row['mentor_name'],
                subtasks=subtasks,
                task_memos=task_memos,
                task_reviews=task_reviews
            )

    def fetch_comprehensive_data(self, user_id: int) -> Optional[ComprehensiveReportData]:
        with self.get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT first_name, last_name, role FROM core_user WHERE user_id = %s", (user_id,))
            user_row = cur.fetchone()

            if not user_row:
                return None

            full_name = f"{user_row['last_name']}{user_row['first_name']}"
            task_list = self.get_user_tasks(user_id)
            all_tasks = []
            total_tasks, total_subtasks, completed_subtasks = len(task_list), 0, 0
            total_scores, subtask_scores = [], []

            for task_id, _ in task_list:
                task_info = self.fetch_single_task_data(task_id)
                if task_info:
                    all_tasks.append(task_info)
                    total_subtasks += len(task_info.subtasks)
                    completed_subtasks += len([s for s in task_info.subtasks if s['content']])
                    for review in task_info.task_reviews:
                        if review['score']:
                            total_scores.append(review['score'])
                    for subtask in task_info.subtasks:
                        if subtask['score'] > 0:
                            subtask_scores.append(subtask['score'])

            all_scores = total_scores + subtask_scores
            overall_stats = {
                'total_tasks': total_tasks,
                'total_subtasks': total_subtasks,
                'completed_subtasks': completed_subtasks,
                'completion_rate': (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0,
                'average_score': sum(all_scores) / len(all_scores) if all_scores else 0,
                'task_scores': total_scores,
                'subtask_scores': subtask_scores,
                'total_evaluations': len(all_scores)
            }

            return ComprehensiveReportData(
                user_name=full_name,
                user_role=user_row['role'],
                all_tasks=all_tasks,
                overall_stats=overall_stats
            )
        def generate_comprehensive_report_prompt(self, report_data: ComprehensiveReportData) -> str:
            """전체 종합 리포트 생성을 위한 프롬프트 생성"""
        prompt = f"""
            다음 정보를 바탕으로 "{report_data.user_name}" 사용자의 전체 학습 과정에 대한 종합 리포트를 생성해주세요.

            === 학습자 기본 정보 ===
            - 학습자: {report_data.user_name} ({report_data.user_role})
            - 총 과제 수: {report_data.overall_stats['total_tasks']}개
            - 총 하위 과제 수: {report_data.overall_stats['total_subtasks']}개
            - 완료된 하위 과제: {report_data.overall_stats['completed_subtasks']}개
            - 완료율: {report_data.overall_stats['completion_rate']:.1f}%
            - 전체 평균 점수: {report_data.overall_stats['average_score']:.1f}점 (총 {report_data.overall_stats['total_evaluations']}개 평가)

            === 상위 과제별 상세 정보 ===
            """
        
        for i, task in enumerate(report_data.all_tasks, 1):
            # 해당 과제의 점수 추출
            task_score = 0
            for review in task.task_reviews:
                if review['score']:
                    task_score = review['score']
                    break
            
            prompt += f"""
            [상위 과제 {i}] {task.title}
            - 과제 날짜: {task.date}
            - 담당 멘토: {task.mentor_name}
            - 과제 점수: {task_score}점
            - 과제 가이드: {task.guide}
            - 과제 상세 내용: {task.content}

            하위 과제 상세 정보:
            """
            
            for j, subtask in enumerate(task.subtasks, 1):
                status = "완료" if subtask['content'] else "미완료"
                prompt += f"""  [{j}] {subtask['title']} ({status})
     - 가이드: {subtask['guide']}
     - 제출일: {subtask['date']}
     - 점수: {subtask['score']:.1f}점
     - 제출 내용: {subtask['content'][:200]}{'...' if len(subtask['content']) > 200 else ''}
"""
                
                # 하위 과제별 피드백 정보
                if subtask['memos']:
                    prompt += f"     - 메모: {'; '.join(subtask['memos'])}\n"
                if subtask['reviews']:
                    prompt += f"     - 리뷰: {'; '.join(subtask['reviews'])}\n"
            
            # 상위 과제 전체 피드백
            if task.task_memos:
                prompt += f"\n상위 과제 멘토 피드백:\n"
                for memo in task.task_memos:
                    prompt += f"- {memo['content']} ({memo['date']})\n"
            
            if task.task_reviews:
                prompt += f"\n상위 과제 리뷰봇 평가:\n"
                for review in task.task_reviews:
                    prompt += f"- {review['content']} (점수: {review['score']}, {review['date']})\n"
            
            prompt += "\n" + "="*50 + "\n"
        
        prompt += f"""
        === 점수 분석 ===
        - 상위 과제 점수: {report_data.overall_stats['task_scores']}
        - 하위 과제 점수: {report_data.overall_stats['subtask_scores']}
        - 전체 평균: {report_data.overall_stats['average_score']:.1f}점

        === 종합 요청사항 ===
        위의 모든 상위 과제와 하위 과제 정보를 바탕으로 다음 구조의 종합 리포트를 작성해주세요:

        1. **전체 학습 여정 종합 분석**
        - 모든 과제를 통해 학습한 핵심 기술과 개념
        - 과제 간 연계성과 점진적 발전 과정
        - 학습 목표 달성도 평가

        2. **핵심 성취 및 우수 성과**
        - 각 상위/하위 과제에서 보여준 뛰어난 성과
        - 지속적으로 나타나는 강점과 역량
        - 특별히 성장이 뚜렷한 영역

        3. **개선 필요 영역 및 보완점**
        - 여러 과제에서 반복적으로 나타나는 어려움
        - 기술적/학습적 보완이 필요한 부분
        - 학습 방법론상의 개선 방향

        4. **과제별 핵심 학습 성과 요약**
        - 각 상위 과제의 주요 학습 성과
        - 하위 과제를 통한 세부 역량 발전
        - 과제 수행 과정에서의 성장 포인트

        5. **종합 평가 및 미래 학습 로드맵**
        - 전체 학습 과정에 대한 종합 평가
        - 현재 수준에서의 강점과 약점 분석
        - 다음 단계 학습 방향 제시
        - 장기적 커리어 발전을 위한 추천 사항

        리포트는 학습자의 노력을 인정하고 격려하는 톤으로, 구체적인 근거와 함께 건설적인 피드백을 제공해주세요.
        모든 상위 과제와 하위 과제의 내용을 균형 있게 반영하여 종합적인 분석을 진행해주세요.
        """
        return prompt
    
    def generate_comprehensive_report(self, user_id: int) -> Optional[str]:
        """전체 종합 리포트 생성 메인 함수"""
        print(f"사용자 {user_id}의 전체 학습 데이터 조회 중...")
        
        # 전체 데이터 조회
        report_data = self.fetch_comprehensive_data(user_id)
        if not report_data:
            print("사용자 데이터를 찾을 수 없습니다.")
            return None
        
        print(f"총 {len(report_data.all_tasks)}개 과제 데이터 로드 완료")
        print(f"전체 완료율: {report_data.overall_stats['completion_rate']:.1f}%")
        print(f"평균 점수: {report_data.overall_stats['average_score']:.1f}점")
        
        # 프롬프트 생성
        prompt = self.generate_comprehensive_report_prompt(report_data)
        
        print("AI 종합 리포트 생성 중...")
        
        # LLM을 통한 종합 리포트 생성
        messages = [
            SystemMessage(content="""당신은 학습자의 전체 학습 과정을 분석하고 종합적인 피드백을 제공하는 교육 전문가입니다. 
            모든 상위 과제와 하위 과제의 내용을 면밀히 분석하여 학습자의 성장 과정을 정확히 파악하고, 
            구체적이고 실용적인 피드백을 제공해주세요."""),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"리포트 생성 중 오류 발생: {e}")
            return None
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        report_data = self.fetch_comprehensive_data(user_id)
        if not report_data:
            return None
        return {
            'user_name': report_data.user_name,
            'user_role': report_data.user_role,
            'stats': report_data.overall_stats,
            'task_count': len(report_data.all_tasks)
        }    

    def generate_comprehensive_report_node(self, state: dict) -> dict:
        user_id = state.get("user_id")
        if not user_id:
            return state

        report = self.generate_comprehensive_report(user_id)
        if not report:
            return state

        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE core_mentorship SET report = %s WHERE mentee_id = %s
                """, (report, user_id))
                conn.commit()
            print("✅ 리포트 DB 저장 완료")
        except Exception as e:
            print(f"❌ 리포트 저장 실패: {e}")

        alarm_events = state.get("alarm_events", [])
        alarm_events.append({
            "event_type": "final_report_ready",
            "user_id": user_id,
            "message": f"{user_id}번 멘티의 최종 평가 보고서가 생성되었습니다. 확인해 주세요."
        })

        return {
            **state,
            "report_generated_ids": state.get("report_generated_ids", []) + [user_id],
            "alarm_events": alarm_events
        }

    

# alarm_agent
class AlarmAgent:
    def __init__(self, db_config: dict = None):
        self.db_config = db_config or DB_CONFIG


    def send_to_alarm(self, user_id: int, message: str, url_link: str = None):
        """📩 알림 테이블에 알림 저장 (core_alarm 사용)"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()  # DictCursor 제거: 튜플로 받음
            # datetime을 문자열로 명시적 변환
            created_at = str(datetime.now().isoformat())
            cur.execute("""
                INSERT INTO core_alarm (user_id, message, created_at, is_active, url_link)
                VALUES (%s, %s, %s, true, %s)
            """, (int(user_id), str(message), created_at, url_link))
            conn.commit()
            conn.close()
            print(f"📨 [알림 저장 완료] → 사용자 {user_id}, URL: {url_link or 'None'}")
        except Exception as e:
            print(f"❌ [알림 저장 실패]: {e}")

    def save_alarm_log(self, user_id: int, message: str, event_type: str):
        """📝 alarm 테이블에 알림 로그 저장 (event_type은 메시지에 포함)"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()  # DictCursor 제거: 튜플로 받음
            # event_type을 메시지에 포함하여 저장
            full_message = f"[{event_type}] {message}"
            # datetime을 문자열로 명시적 변환
            created_at = str(datetime.now().isoformat())
            cur.execute("""
                INSERT INTO core_alarm (user_id, message, created_at, is_active)
                VALUES (%s, %s, %s, true)
            """, (int(user_id), str(full_message), created_at))
            conn.commit()
            conn.close()
            print(f"🔔 [alarm 로그 저장 완료] → {event_type} for user {user_id}")
        except Exception as e:
            print(f"❌ [alarm 로그 저장 실패]: {e}")

    async def send_email(self, to_email, report_url, from_email, from_password):
        """📧 최종 평가 보고서 이메일 전송"""
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

        # recipients는 반드시 문자열 리스트여야 함
        recipient_email = str(to_email) if not isinstance(to_email, dict) else to_email.get('email', '')
        message = MessageSchema(
            subject="신입사원 최종 평가 보고서 도착",
            recipients=[recipient_email],
            body=f"""
            <h3>최종 평가 보고서가 도착했습니다.</h3>
            <p>아래 링크를 통해 확인하세요:</p>
            <a href="{report_url}">{report_url}</a>
            """,
            subtype="html"
        )

        fm = FastMail(conf)
        await fm.send_message(message)

    def send_final_report_email(self, mentee_id: int):
        """📧 멘토에게 최종 보고서 이메일 전송"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()  # DictCursor 제거: 튜플로 받음

            # 멘토 ID, 이메일
            cur.execute("SELECT mentor_id FROM core_mentorship WHERE mentee_id = %s", (int(mentee_id),))
            mentor_row = cur.fetchone()
            if not mentor_row:
                print("❌ [멘토 ID 없음]")
                conn.close()
                return
            mentor_id = int(mentor_row[0])

            cur.execute("SELECT email FROM core_user WHERE user_id = %s", (mentor_id,))
            email_row = cur.fetchone()
            if not email_row:
                print("❌ [멘토 이메일 없음]")
                conn.close()
                return
            mentor_email = email_row[0]
            # 혹시라도 dict 타입이 들어올 경우 방지
            if isinstance(mentor_email, dict):
                mentor_email = mentor_email.get('email', '')
            else:
                mentor_email = str(mentor_email)

            # 발신 계정 조회
            cur.execute("SELECT email, password FROM core_emailconfig ORDER BY id DESC LIMIT 1")
            sender_row = cur.fetchone()
            if not sender_row:
                print("❌ [발신 계정 없음]")
                conn.close()
                return
            sender_email = str(sender_row[0])
            sender_password = str(sender_row[1])
            conn.close()

            report_url = f"https://sinip.company/report/{mentee_id}"  # 실제 경로로 바꿔야 함
            # recipients에 dict가 들어가지 않도록 보장
            asyncio.run(self.send_email(mentor_email, report_url, sender_email, sender_password))
            print(f"📧 [이메일 발송 완료] → {mentor_email}")

        except Exception as e:
            print(f"❌ [이메일 발송 실패]: {e}")

    def send_final_report_email_node(self, state: dict) -> dict:
        """📧 LangGraph용 최종 보고서 이메일 발송 노드"""
        user_id = state.get("user_id")
        if user_id:
            self.send_final_report_email(user_id)
        return state

    def run(self, state: dict) -> dict:
        """🔔 LangGraph용 실행 메서드"""
        print("🔔 alarm_agent_node 실행 시작")

        alarm_events = state.get("alarm_events", [])
        for event in alarm_events:
            event_type = event.get("event_type")
            message = event.get("message")

            # 알림 대상 결정
            if event_type == "final_report_ready":
                user_id = event.get("user_id")
                url = event.get("url")
                self.send_final_report_email(user_id)
                self.send_to_alarm(user_id, message, url)
                self.save_alarm_log(user_id, message, event_type)

            elif event_type == "task_completed_by_mentor":
                user_id = event.get("mentee_id")
                url = event.get("url")
                self.send_to_alarm(user_id, message, url)
                self.save_alarm_log(user_id, message, event_type)

            elif event_type == "task_review_requested":
                # 멘토 ID를 task_id로부터 조회
                task_id = event.get("task_id")
                url = event.get("url")
                if task_id:
                    try:
                        conn = psycopg2.connect(**self.db_config)
                        cur = conn.cursor()
                        # task_assign -> mentorship -> mentor_id 조회
                        cur.execute("""
                            SELECT m.mentor_id 
                            FROM core_taskassign ta 
                            JOIN core_mentorship m ON ta.mentorship_id_id = m.mentorship_id 
                            WHERE ta.task_assign_id = %s
                        """, (task_id,))
                        mentor_row = cur.fetchone()
                        conn.close()
                        
                        if mentor_row:
                            mentor_id = mentor_row[0]
                            self.send_to_alarm(mentor_id, message, url)
                            self.save_alarm_log(mentor_id, message, event_type)
                        else:
                            print(f"❌ [멘토 ID 조회 실패] task_id: {task_id}")
                    except Exception as e:
                        print(f"❌ [멘토 ID 조회 오류]: {e}")
                else:
                    print("❌ [task_id 없음] task_review_requested 이벤트")

            elif event_type == "review_written":
                user_id = event.get("mentee_id")
                url = event.get("url")
                self.send_to_alarm(user_id, message, url)
                self.save_alarm_log(user_id, message, event_type)

            elif event_type == "deadline_reminder":
                user_id = event.get("user_id")
                url = event.get("url")
                self.send_to_alarm(user_id, message, url)
                self.save_alarm_log(user_id, message, event_type)
            
            elif event_type == "task_review_completed":
                user_id = event.get("mentee_id")
                url = event.get("url")
                self.send_to_alarm(user_id, message, url)
                self.save_alarm_log(user_id, message, event_type)

            else:
                print(f"⚠️ 알 수 없는 이벤트 타입: {event_type}")
                continue

        state["alarm_events"] = []
        return state



# ✅ LangGraph 구성 및 실행
EventAgent = EventAgent()
ReviewAgent = ReviewAgent()
ReportAgent = ReportAgent()
AlarmAgent = AlarmAgent()

# ✅ 그래프 빌더 초기화
builder = StateGraph(GraphState)

# ✅ 노드 정의
builder.add_node("check_state", EventAgent.run)
builder.add_node("route", route_node)
builder.add_node("check_deadline_tasks", EventAgent.run)
builder.add_node("detect_status_change", EventAgent.detect_status_change)
builder.add_node("check_onboarding_complete", EventAgent.check_completion)
builder.add_node("review_node", ReviewAgent.review)
builder.add_node("report_generator", ReportAgent.generate_comprehensive_report_node)
builder.add_node("send_alarm_email", AlarmAgent.run)  # 수신함 알람
builder.add_node("send_email_final_report", AlarmAgent.send_final_report_email_node)  # 최종 보고서 이메일 발송

# ✅ 진입점 설정
builder.set_entry_point("check_state")

# ✅ 주요 흐름 연결
builder.add_edge("check_state", "detect_status_change")
builder.add_edge("detect_status_change", "route")

# ✅ 조건 분기 정의
builder.add_conditional_edges("route", routing_condition, {
    "review_node": "review_node",
    "check_onboarding_complete": "check_onboarding_complete",
    "check_deadline_tasks": "check_deadline_tasks"
})

# ✅ 온보딩 완료 → 보고서 생성 → 수신함 알림 → 이메일 발송 → 종료
builder.add_edge("check_onboarding_complete", "report_generator")
builder.add_edge("report_generator", "send_alarm_email")
builder.add_edge("send_alarm_email", "send_email_final_report")
builder.add_edge("send_email_final_report", END)

# ✅ 기타 분기 종료
builder.add_edge("review_node", END)
builder.add_edge("check_deadline_tasks", "send_alarm_email")
builder.add_edge("send_alarm_email", END)


# 그래프 컴파일
graph = builder.compile()


import threading
import os
import asyncio

# 전역 상태 관리
global_state: GraphState = {
    "messages": [],
    "last_status_map": {},
    "last_deadline_check": "",
    "last_onboarding_check": "",
    "completed_onboarding_ids": [],
    "report_generated_ids": [],
    "reviewed_task_ids": []
}

class AgentScheduler:
    """Agent 스케줄러 클래스"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        
    def initialize_state(self):
        """상태 초기화"""
        global global_state
        try:
            global_state["last_status_map"] = load_current_status_map()
            print("✅ 초기 상태 로드 완료")
        except Exception as e:
            print(f"❌ 상태 초기화 실패: {e}")
            global_state["last_status_map"] = {}

    def run_agent_cycle(self):
        """Agent 사이클 실행"""
        global global_state
        try:
            print(f"🤖 Agent 사이클 실행 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # LangGraph 실행
            result_state = graph.invoke(global_state)
            
            # 상태 업데이트
            global_state.update(result_state)
            
            # 결과 출력
            if result_state.get("feedback"):
                print("📋 피드백:", result_state["feedback"])
            
            for m in result_state.get("messages", []):
                if isinstance(m, AIMessage):
                    print("📢 응답 메시지:", m.content)
            
            print("✅ Agent 사이클 완료")
            
        except Exception as e:
            print(f"❌ Agent 사이클 실행 실패: {e}")

    def scheduler_loop(self):
        """스케줄러 메인 루프 (환경변수 기반 설정)"""
        if not AGENT_CONFIG['enabled']:
            print("⚠️ Agent가 비활성화되어 있습니다. (.env AGENT_ENABLED=False)")
            return
            
        print(f"🕐 백그라운드 스케줄러 시작... (주기: {AGENT_CONFIG['cycle_interval']}초)")
        
        last_cycle_time = time.time()
        last_hourly_check = datetime.now().hour
        last_daily_check = datetime.now().date()
        
        while self.is_running:
            try:
                current_time = time.time()
                current_hour = datetime.now().hour
                current_date = datetime.now().date()
                
                # 설정된 주기마다 실행
                if current_time - last_cycle_time >= AGENT_CONFIG['cycle_interval']:
                    self.run_agent_cycle()
                    last_cycle_time = current_time
                
                # 매시 정각에 실행 (hourly_check 간격으로)
                elif current_hour != last_hourly_check and current_hour % AGENT_CONFIG['hourly_check'] == 0:
                    print(f"⏰ 정시 체크 실행 (매 {AGENT_CONFIG['hourly_check']}시간)")
                    self.run_agent_cycle()
                    last_hourly_check = current_hour
                
                # 매일 설정된 시간에 실행
                elif current_date != last_daily_check and current_hour == AGENT_CONFIG['daily_check_hour']:
                    print(f"🌅 일일 체크 실행 ({AGENT_CONFIG['daily_check_hour']}시)")
                    self.run_agent_cycle()
                    last_daily_check = current_date
                
                time.sleep(1)  # 1초마다 체크
                
            except KeyboardInterrupt:
                print("🛑 스케줄러 중지됨")
                break
            except Exception as e:
                print(f"❌ 스케줄러 오류: {e}")
                time.sleep(30)  # 오류 시 30초 대기

    def start(self):
        """백그라운드에서 Agent 시스템 시작"""
        if self.is_running:
            print("⚠️ Agent 시스템이 이미 실행 중입니다.")
            return
        
        if not AGENT_CONFIG['enabled']:
            print("⚠️ Agent가 비활성화되어 있습니다. (.env AGENT_ENABLED=False)")
            return
            
        print("🚀 LangGraph 통합 에이전트 백그라운드 실행 시작...")
        print(f"📋 Agent 설정:")
        print(f"   - 실행 주기: {AGENT_CONFIG['cycle_interval']}초")
        print(f"   - 정시 체크: 매 {AGENT_CONFIG['hourly_check']}시간")
        print(f"   - 일일 체크: 매일 {AGENT_CONFIG['daily_check_hour']}시")
        print(f"   - PostgreSQL DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        
        # 상태 초기화
        self.initialize_state()
        
        # 첫 실행
        self.run_agent_cycle()
        
        # 백그라운드 스레드로 스케줄러 실행
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        return self.scheduler_thread

    def stop(self):
        """백그라운드 Agent 시스템 중지"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("🛑 LangGraph 통합 에이전트 중지됨")

    def trigger_immediate_check(self):
        """즉시 Agent 체크 실행 (외부 트리거용)"""
        print("⚡ 즉시 Agent 체크 트리거됨")
        self.run_agent_cycle()

    def get_status(self):
        """현재 Agent 상태 반환 (설정 정보 포함)"""
        return {
            "is_running": self.is_running,
            "enabled": AGENT_CONFIG['enabled'],
            "config": {
                "cycle_interval": AGENT_CONFIG['cycle_interval'],
                "hourly_check": AGENT_CONFIG['hourly_check'],
                "daily_check_hour": AGENT_CONFIG['daily_check_hour']
            },
            "database": {
                "host": DB_CONFIG['host'],
                "port": DB_CONFIG['port'],
                "database": DB_CONFIG['database']
            },
            "stats": {
                "last_check": global_state.get("last_deadline_check"),
                "reviewed_tasks": len(global_state.get("reviewed_task_ids", [])),
                "completed_onboarding": len(global_state.get("completed_onboarding_ids", [])),
                "generated_reports": len(global_state.get("report_generated_ids", []))
            }
        }



# 전역 스케줄러 인스턴스
agent_scheduler = AgentScheduler()

# 외부에서 사용할 수 있는 함수들
def start_background_agent():
    """백그라운드 Agent 시작"""
    if not AGENT_CONFIG['enabled']:
        print("⚠️ Agent가 비활성화되어 있습니다. (.env AGENT_ENABLED=True로 설정하세요)")
        return None
    return agent_scheduler.start()

def stop_background_agent():
    """백그라운드 Agent 중지"""
    agent_scheduler.stop()

def trigger_immediate_check():
    """즉시 체크 트리거"""
    if not AGENT_CONFIG['enabled']:
        print("⚠️ Agent가 비활성화되어 있습니다.")
        return
    agent_scheduler.trigger_immediate_check()

def get_agent_status():
    """Agent 상태 조회"""
    return agent_scheduler.get_status()
