import os
from typing import TypedDict, List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, date
from dotenv import load_dotenv
from openai import OpenAI
from typing import Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
import psycopg2
import psycopg2.extras
import asyncio
import re
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from core.models import Mentorship



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

# ✅ 상태 정의
class GraphState(TypedDict, total=False):
    messages: List[BaseMessage]
    user_id: Optional[int]
    onboarding_due: Optional[bool]
    completed_onboarding_ids: Optional[List[int]]
    report_generated_ids: Optional[List[int]]
    alarm_events: Optional[List[Dict]]

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


# ✅ 노드 정의
class ReportAgent:
    def check_completion(self, state: GraphState) -> GraphState:
        """온보딩 완료 여부 확인하는 노드"""
        print(f"check_completion() 실행 시작 : user_id={state.get('user_id')}")
        
        # 이미 처리된 경우는 건너뛰기
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

                return {
                    **state,
                    "messages": [HumanMessage(content=f"{mentee_id}번 멘티의 보고서를 작성해줘")],
                    "user_id": mentee_id,
                    "onboarding_due": True, 
                    "last_onboarding_check": today_str,
                    "completed_onboarding_ids": completed + [mentee_id]
                }

        state["onboarding_due"] = False
        state["last_onboarding_check"] = today_str
        return state
    
    
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


            for task_id, _ in task_list:
                task_info = self.fetch_single_task_data(task_id)
                if task_info:
                    all_tasks.append(task_info)
                    total_subtasks += len(task_info.subtasks)
                    completed_subtasks += len([s for s in task_info.subtasks if s['status'] == '완료'])


            overall_stats = {
                'total_tasks': total_tasks,
                'total_subtasks': total_subtasks,
                'completed_subtasks': completed_subtasks,
                'completion_rate': (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0,
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
                - 멘티: {report_data.user_name} ({report_data.user_role})
                - 총 과제 수: {report_data.overall_stats['total_tasks']}개
                - 총 하위 과제 수: {report_data.overall_stats['total_subtasks']}개
                - 완료된 하위 과제: {report_data.overall_stats['completed_subtasks']}개

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
                - 과제 가이드: {task.guide}
                - 과제 상세 내용: {task.content}

                하위 과제 상세 정보:
                """
                
                for j, subtask in enumerate(task.subtasks, 1):
                    status = "완료" if subtask['content'] else "미완료"
                    prompt += f"""  [{j}] {subtask['title']} ({status})
        - 가이드: {subtask['guide']}
        - 제출일: {subtask['date']}
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

        # 프롬프트 생성
        prompt = self.generate_comprehensive_report_prompt(report_data)
        
        print("AI 종합 리포트 생성 중...")
        
        # LLM을 통한 종합 리포트 생성
        messages = [
            SystemMessage(content="""당신은 멘티의 전체 학습 과정을 분석하고 종합적인 피드백을 제공하는 교육 전문가입니다. 
            모든 상위 과제와 하위 과제의 내용을 면밀히 분석하여 학습자의 성장 과정을 정확히 파악하고, 
            구체적이고 실용적인 피드백을 제공해주세요. 그리고 태스크 수행 내용이 부족하거나 미흡한 부분은 객관적으로 지적하고, 개선 방향을 구체적으로 제시해주세요. 
            **각 항목(1~4번)은 최소 400자 이상 작성하여, 전체 글자 수가 2000자 이상이 되도록 해주세요.** """),
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
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

                # 멘티 이름 조회
                cur.execute("""
                    SELECT first_name, last_name 
                    FROM core_user 
                    WHERE user_id = %s
                """, (user_id,))
                user_row = cur.fetchone()
                mentee_name = f"{user_row['last_name']}{user_row['first_name']}" if user_row else f"사용자 {user_id}"

                # 멘토 정보 조회
                cur.execute("""
                    SELECT m.mentor_id, u.email
                    FROM core_mentorship m
                    JOIN core_user u ON m.mentor_id = u.user_id
                    WHERE m.mentee_id = %s
                    ORDER BY m.is_active DESC
                    LIMIT 1
                """, (user_id,))
                mentor_info = cur.fetchone()

                mentor_id = mentor_info['mentor_id'] if mentor_info else None
                mentor_email = mentor_info['email'] if mentor_info else None

                cur.execute("""
                    UPDATE core_mentorship SET report = %s WHERE mentee_id = %s
                """, (report, user_id))
                conn.commit()
            print("✅ 리포트 DB 저장 완료")
        except Exception as e:
            print(f"❌ 리포트 저장 실패: {e}")
            mentor_id, mentor_email, mentee_name = None, None, f"사용자 {user_id}"

        alarm_events = state.get("alarm_events", [])
        alarm_events.append({
            "event_type": "final_report_ready",
            "user_id": user_id,
            "mentor_id": mentor_id,
            "mentor_email": mentor_email,
            "message": f"{mentee_name} 멘티의 최종 평가 보고서가 생성되었습니다. 확인해 주세요."
        })

        return {
            **state,
            "report_generated_ids": state.get("report_generated_ids", []) + [user_id],
            "alarm_events": alarm_events
        }


    def send_alarm(self, state: GraphState) -> GraphState:
        """알림 발송 노드"""
        print("send_alarm() 실행 시작")
        
        alarm_events = state.get("alarm_events", [])
        if not alarm_events:
            print("⚠️ 알림 이벤트가 없습니다.")
            return state
            
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            for event in alarm_events:
                # URL 생성 (최종 보고서용)
                url_link = None
                if event.get("event_type") == "final_report_ready" and event.get("mentorship_id"):
                    url_link = f"/mentee/task_list/?mentorship_id={event['mentorship_id']}&open=final_report"
                
                # 멘티에게 알림 저장
                # cur.execute("""
                #     INSERT INTO core_alarm (user_id, message, created_at, is_active, url_link)
                #     VALUES (%s, %s, CURRENT_TIMESTAMP, true, %s)
                # """, (event["user_id"], event["message"], url_link))
                
                if event.get("mentor_id"):
                    # 멘토에게도 알림 (같은 URL 사용)
                    cur.execute("""
                        INSERT INTO core_alarm (user_id, message, created_at, is_active, url_link)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, true, %s)
                    """, (event["mentor_id"], event["message"], url_link))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 알림 저장 완료 - {len(alarm_events)}개의 알림")
            
            # 중요: alarm_events를 유지한 채로 상태 반환
            return state
            
        except Exception as e:
            print(f"❌ 알림 발송 실패: {e}")
            return state

    async def send_email_async(self, to_email: str, report_url: str, from_email: str, from_password: str, report_content: str, mentee_name: str):
        """📧 최종 평가 보고서 이메일 전송"""
        try:
            print(f"📧 이메일 발송 시도 - FROM: {from_email}, TO: {to_email}")
            
            conf = ConnectionConfig(
                MAIL_USERNAME=from_email,
                MAIL_PASSWORD=from_password,
                MAIL_FROM=from_email,
                MAIL_PORT=587,
                MAIL_SERVER="smtp.gmail.com",
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
                MAIL_FROM_NAME="EZ:FLOW",
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True
            )

            # recipients는 반드시 문자열 리스트여야 함
            recipient_email = str(to_email) if not isinstance(to_email, dict) else to_email.get('email', '')
            
            # HTML 형식의 이메일 본문 생성
            def markdown_to_html(text: str) -> str:
                text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # **bold**
                text = text.replace('\n', '<br>')  # 줄바꿈 처리
                return text

            report_html = markdown_to_html(report_content)

            email_body = f"""
                <h2>{mentee_name} 멘티 온보딩 최종 평가 보고서</h2>
                
                <div style="margin: 20px 0; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                    <h3>보고서 내용</h3>
                    <div style="font-family: Arial, sans-serif;">
                        {report_html}
                    </div>
                </div>
                
                <p>자세한 내용은 아래 링크에서 확인하실 수 있습니다:</p>
                <a href="{report_url}" style="display: inline-block; margin: 20px 0; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
                    보고서 상세 보기
                </a>
                
                <p style="color: #6c757d; font-size: 0.9em; margin-top: 30px;">
                    본 이메일은 자동으로 발송되었습니다.<br>
                    문의사항이 있으시면 관리자에게 연락해 주세요.
                </p>
            """
            
            message = MessageSchema(
                subject=f"{mentee_name} 멘티 온보딩 최종 평가 보고서",
                recipients=[recipient_email],
                body=email_body,
                subtype="html"
            )

            print("📧 FastMail 설정 완료, 메시지 전송 시도...")
            fm = FastMail(conf)
            await fm.send_message(message)
            print("📧 이메일 전송 성공!")
            
        except Exception as e:
            print(f"❌ 이메일 발송 중 오류 발생:")
            print(f"  - 오류 유형: {type(e).__name__}")
            print(f"  - 오류 내용: {str(e)}")
            print(f"  - FROM: {from_email}")
            print(f"  - TO: {recipient_email}")
            raise

    def send_email(self, state: GraphState) -> GraphState:
        """이메일 발송 노드"""
        print("send_email() 실행 시작")
        
        alarm_events = state.get("alarm_events", [])
        if not alarm_events:
            print("⚠️ 알림 이벤트가 없습니다.")
            return state
            
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # 이메일 발송 설정 조회
            cur.execute("SELECT email, password FROM core_emailconfig ORDER BY id DESC LIMIT 1")
            email_config = cur.fetchone()
            
            if not email_config:
                print("⚠️ 이메일 설정을 찾을 수 없습니다.")
                return state
            
            for event in alarm_events:
                if event.get("event_type") == "final_report_ready" and event.get("mentor_email"):
                    mentor_email = event.get("mentor_email")
                    
                    # 멘토십 정보 조회하여 보고서 URL 생성
                    cur.execute("""
                        SELECT m.mentorship_id, m.report
                        FROM core_mentorship m
                        WHERE m.mentor_id = %s AND m.mentee_id = %s
                        ORDER BY m.is_active DESC
                        LIMIT 1
                    """, (event.get("mentor_id"), event.get("user_id")))
                    mentorship_row = cur.fetchone()
                    
                    if mentorship_row and mentorship_row['report']:
                        report_url = f"http://127.0.0.1:8000/mentee/task_list/?mentorship_id={mentorship_row['mentorship_id']}&open=final_report"

                        # DB에 url_link 저장
                        # Django ORM을 사용하여 url_link 업데이트
                        try:
                            mentorship_obj = Mentorship.objects.get(mentorship_id=mentorship_row['mentorship_id'])
                            mentorship_obj.url_link = report_url
                            mentorship_obj.save(update_fields=['url_link'])
                            print(f"✅ DB에 report_url 저장 완료: {report_url}")
                        except Mentorship.DoesNotExist:
                            print(f"❌ Mentorship ID={mentorship_row['mentorship_id']}를 찾을 수 없습니다.")
                        except Exception as db_error:
                            import traceback
                            print(f"❌ DB url_link 저장 실패: {db_error}")
                            traceback.print_exc()
                             

                        try:
                            asyncio.run(self.send_email_async(
                                to_email=mentor_email,
                                report_url=report_url,
                                from_email=email_config['email'],
                                from_password=email_config['password'],
                                report_content=mentorship_row['report'],
                                mentee_name=event.get("message").split(" 멘티")[0]
                            ))
                            print(f"📧 이메일 발송 완료 (TO: {mentor_email})")
                        except Exception as email_error:
                            print(f"❌ 이메일 발송 실패: {email_error}")
                    else:
                        print("⚠️ 보고서 내용을 찾을 수 없습니다.")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 이메일 발송 실패: {e}")
        
        return state

# ✅ 그래프 구성
def create_report_graph():
    nodes = ReportAgent()
    builder = StateGraph(GraphState)
    
    # 노드 추가
    builder.add_node("check_completion", nodes.check_completion)
    builder.add_node("generate_report", nodes.generate_comprehensive_report_node)
    builder.add_node("send_alarm", nodes.send_alarm)
    builder.add_node("send_email", nodes.send_email)
    
    # 진입점 설정
    builder.set_entry_point("check_completion")
    
    # 순차적 엣지 연결
    builder.add_edge("check_completion", "generate_report")
    builder.add_edge("generate_report", "send_alarm")
    builder.add_edge("send_alarm", "send_email")
    builder.add_edge("send_email", END)
    
    return builder.compile()

# ✅ 그래프 실행 함수
def run_report_workflow(user_id: Optional[int] = None):
    """보고서 생성 워크플로우 실행"""
    graph = create_report_graph()
    
    initial_state: GraphState = {
        "messages": [],
        "user_id": user_id,
        "onboarding_due": True,  # 직접 호출 시에는 항상 True
        "completed_onboarding_ids": [],
        "report_generated_ids": [],
        "alarm_events": []
    }
    
    try:
        print(f"🚀 보고서 워크플로우 시작 - user_id: {user_id}")
        final_state = graph.invoke(initial_state)
        print("✅ 보고서 워크플로우 완료")
        return final_state
    except Exception as e:
        print(f"❌ 보고서 워크플로우 실패: {e}")
        return None 