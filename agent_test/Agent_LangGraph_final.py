import os
import sqlite3
import time
import asyncio
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
DB_PATH = "sample.db"

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
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT task_assign_id, title, status FROM task_assign")
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
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.user_id, u.first_name, ta.task_assign_id, ta.title, ta.scheduled_end_date, ta.status
            FROM user u
            JOIN task_assign ta ON u.user_id = ta.user_id
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

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT task_assign_id, title, status, user_id FROM task_assign")
        rows = cur.fetchall()
        conn.close()

        current = {row[0]: {"title": row[1], "status": row[2], "user_id": row[3]} for row in rows}
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
                alarm_events.append({
                    "event_type": "task_review_requested",
                    "user_id": info["user_id"],
                    "message": message
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
                    "user_id": info["user_id"],
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
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.user_id, u.first_name, m.email, MAX(ta.scheduled_end_date)
            FROM user u
            JOIN task_assign ta ON u.user_id = ta.user_id
            JOIN mentorship ms ON ta.mentorship_id = ms.mentorship_id
            JOIN user m ON m.user_id = ms.mentor_id
            WHERE u.role = 'mentee'
            GROUP BY u.user_id
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

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # task 정보 확인
        cur.execute("SELECT user_id, mentorship_id, title FROM task_assign WHERE task_assign_id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            print("❌ [review] 해당 task_assign 없음")
            conn.close()
            return state

        mentee_id, mentorship_id, task_title = row
        print(f"🔍 [review] task_title: {task_title}, mentee_id: {mentee_id}, mentorship_id: {mentorship_id}")

        # 멘토 ID 조회
        cur.execute("SELECT mentor_id FROM mentorship WHERE mentorship_id = ?", (mentorship_id,))
        mentor_row = cur.fetchone()
        if not mentor_row:
            print("❌ [review] 멘토 ID 조회 실패")
            conn.close()
            return state

        mentor_id = mentor_row[0]
        print(f"✅ [review] mentor_id: {mentor_id}")

        # 하위 과제 가져오기
        cur.execute("SELECT subtask_title, content FROM subtask WHERE task_assign_id = ?", (task_id,))
        subtasks = cur.fetchall()
        conn.close()

        if not subtasks:
            print("⚠️ [review] 서브태스크 없음")

        subtask_text = "\n".join([f"- {title.strip()}: {content.strip() or '내용 없음'}" for title, content in subtasks])

        # GPT 프롬프트 작성 및 요청
        prompt = f"""너는 IT 멘토입니다. 상위 업무는 '{task_title}'이고, 하위 작업은 다음과 같습니다:\n{subtask_text}\n다음 형식으로 피드백 작성:\n- 👍 잘한 점:\n- 🔧 개선할 점:\n- 🧾 요약 피드백:\n---"""
        feedback = llm.invoke(prompt).content
        print("📝 [review] 피드백 생성 완료")

        # DB에 피드백 저장 -> memo 테이블에 저장
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        today_str = date.today().isoformat()
        cur.execute(
            "INSERT INTO memo (task_assign_id, content, create_date) VALUES (?, ?, ?)",
            (task_id, feedback, today_str)
        )
        conn.commit()
        conn.close()
        print(f"✅ [review] memo 저장 완료 (mentor_id={mentor_id}, task_id={task_id})")

        # ✅ 알람 이벤트 생성
        alarm_events = state.get("alarm_events", [])
        alarm_events.append({
            "event_type": "task_review_completed",
            "mentee_id": mentee_id,
            "message": f"{task_title} 태스크에 대한 멘토의 리뷰가 작성되었습니다. 확인해 주세요."
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
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.llm = llm

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_user_tasks(self, user_id: int) -> List[Tuple[int, str]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT t.task_id, t.title
                FROM task t
                JOIN task_assign ta ON t.task_id = ta.task_id
                WHERE ta.mentee_id = ? OR ta.mentor_id = ?
                ORDER BY t.task_id
            """, (user_id, user_id))
            return [(row['task_id'], row['title']) for row in cur.fetchall()]

    def fetch_single_task_data(self, task_id: int) -> Optional[TaskInfo]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT t.*, u_mentee.name as mentee_name, u_mentor.name as mentor_name
                FROM task t
                JOIN task_assign ta ON t.task_id = ta.task_id
                JOIN user u_mentee ON ta.mentee_id = u_mentee.user_id
                JOIN user u_mentor ON ta.mentor_id = u_mentor.user_id
                WHERE t.task_id = ?
            """, (task_id,))
            task_row = cur.fetchone()
            if not task_row:
                return None

            cur.execute("""
                SELECT s.*, 
                       GROUP_CONCAT(DISTINCT m.content) as memo_contents,
                       GROUP_CONCAT(DISTINCT r.content) as review_contents,
                       AVG(r.score) as avg_score
                FROM subtask s
                LEFT JOIN memo m ON s.subtask_id = m.subtask_id
                LEFT JOIN review r ON s.subtask_id = r.subtask_id
                WHERE s.task_id = ?
                GROUP BY s.subtask_id
                ORDER BY s.subtask_id
            """, (task_id,))

            subtasks = []
            for row in cur.fetchall():
                subtasks.append({
                    'subtask_id': row['subtask_id'],
                    'title': row['title'],
                    'guide': row['guide'],
                    'date': row['date'],
                    'content': row['content'],
                    'memos': row['memo_contents'].split(',') if row['memo_contents'] else [],
                    'reviews': row['review_contents'].split(',') if row['review_contents'] else [],
                    'score': row['avg_score'] if row['avg_score'] else 0
                })

            cur.execute("""
                SELECT content, create_date FROM memo
                WHERE task_id = ? AND subtask_id IS NULL
                ORDER BY create_date
            """, (task_id,))
            task_memos = [{'content': r['content'], 'date': r['create_date']} for r in cur.fetchall()]

            cur.execute("""
                SELECT content, score, summary, generated_by, create_date
                FROM review
                WHERE task_id = ? AND subtask_id IS NULL
                ORDER BY create_date
            """, (task_id,))
            task_reviews = [{'content': r['content'], 'score': r['score'], 'summary': r['summary'],
                             'generated_by': r['generated_by'], 'date': r['create_date']} for r in cur.fetchall()]

            return TaskInfo(
                task_id=task_row['task_id'],
                title=task_row['title'],
                guide=task_row['guide'],
                date=task_row['date'],
                content=task_row['content'],
                mentor_name=task_row['mentor_name'],
                subtasks=subtasks,
                task_memos=task_memos,
                task_reviews=task_reviews
            )

    def fetch_comprehensive_data(self, user_id: int) -> Optional[ComprehensiveReportData]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT first_name, last_name, role FROM user WHERE user_id = ?", (user_id,))
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
                    UPDATE mentorship SET report = ? WHERE mentee_id = ?
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
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def send_to_inbox(self, user_id: int, message: str):
        """📩 수신함 테이블에 알림 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO inbox (user_id, message, created_at, is_read)
                VALUES (?, ?, ?, 0)
            """, (user_id, message, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            print(f"📨 [수신함 저장 완료] → 사용자 {user_id}")
        except Exception as e:
            print(f"❌ [inbox 저장 실패]: {e}")

    def save_alarm_log(self, user_id: int, message: str, event_type: str):
        """📝 alarm 테이블에 알림 로그 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO alarm (user_id, message, event_type, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, message, event_type, datetime.now().isoformat()))
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

    def send_final_report_email(self, mentee_id: int):
        """📧 멘토에게 최종 보고서 이메일 전송"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # 멘토 ID, 이메일
            cur.execute("SELECT mentor_id FROM mentorship WHERE mentee_id = ?", (mentee_id,))
            mentor_row = cur.fetchone()
            if not mentor_row:
                print("❌ [멘토 ID 없음]")
                return
            mentor_id = mentor_row[0]

            cur.execute("SELECT email FROM user WHERE user_id = ?", (mentor_id,))
            email_row = cur.fetchone()
            if not email_row:
                print("❌ [멘토 이메일 없음]")
                return
            mentor_email = email_row[0]

            # 발신 계정 조회
            cur.execute("SELECT sender_email, sender_password FROM email_config ORDER BY created_at DESC LIMIT 1")
            sender_row = cur.fetchone()
            if not sender_row:
                print("❌ [발신 계정 없음]")
                return
            sender_email, sender_password = sender_row
            conn.close()

            report_url = f"https://sinip.company/report/{mentee_id}"  # 진슬이 실제 경로로 바꿔야 해
            asyncio.run(self.send_email(mentor_email, report_url, sender_email, sender_password))
            print(f"📧 [이메일 발송 완료] → {mentor_email}")

        except Exception as e:
            print(f"❌ [이메일 발송 실패]: {e}")

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
                self.send_final_report_email(user_id)
                self.send_to_inbox(user_id, message)
                self.save_alarm_log(user_id, message, event_type)

            elif event_type == "task_completed_by_mentor":
                user_id = event.get("mentee_id")
                self.send_to_inbox(user_id, message)
                self.save_alarm_log(user_id, message, event_type)

            elif event_type == "task_review_requested":
                user_id = event.get("mentor_id")
                self.send_to_inbox(user_id, message)
                self.save_alarm_log(user_id, message, event_type)

            elif event_type == "review_written":
                user_id = event.get("mentee_id")
                self.send_to_inbox(user_id, message)
                self.save_alarm_log(user_id, message, event_type)

            elif event_type == "deadline_reminder":
                user_id = event.get("user_id")
                self.send_to_inbox(user_id, message)
                self.save_alarm_log(user_id, message, event_type)
            
            elif event_type == "task_review_completed":
                user_id = event.get("mentee_id")
                self.send_to_inbox(user_id, message)
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
builder.add_node("send_email_final_report", AlarmAgent.send_final_report_email)  # 최종 보고서 이메일 발송

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


if __name__ == "__main__":
    state: GraphState = {
        "messages": [],
        "messages": [],
        "last_status_map": load_current_status_map(),
        "last_deadline_check": "",
        "last_onboarding_check": "",
        "completed_onboarding_ids": [],
        "report_generated_ids": [],
        "reviewed_task_ids": []
    }

    print(" LangGraph 통합 에이전트 상시 실행 시작...")
    while True:
        state = graph.invoke(state)
        if state.get("feedback"):
            print("📋 피드백:", state["feedback"])
        for m in state.get("messages", []):
            if isinstance(m, AIMessage):
                print("📢 응답 메시지:", m.content)
        time.sleep(5)
