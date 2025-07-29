import os
from typing import TypedDict, List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, date
from dotenv import load_dotenv
from openai import OpenAI
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
class ReportNodes:
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
    
    

    def generate_report(self, state: GraphState) -> GraphState:
        """보고서 생성 노드"""
        user_id = state.get("user_id")
        print(f"generate_report() 실행 시작 - user_id: {user_id}")
        if not user_id:
            return state

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # 사용자 정보 조회 - 멘토십 정보와 함께
            cur.execute("""
                SELECT 
                    u.first_name, u.last_name, u.role,
                    m.mentorship_id, m.mentor_id, m.is_active,
                    mentor.email as mentor_email,
                    mentor.first_name as mentor_first_name,
                    mentor.last_name as mentor_last_name
                FROM core_user u
                JOIN core_mentorship m ON u.user_id = m.mentee_id
                JOIN core_user mentor ON mentor.user_id = m.mentor_id
                WHERE u.user_id = %s
                ORDER BY m.is_active DESC
                LIMIT 1
            """, (user_id,))
            user_row = cur.fetchone()
            
            if not user_row:
                print("❌ 사용자 정보를 찾을 수 없습니다.")
                return state
            
            print(f"✅ 사용자 정보 조회 성공: {user_row['first_name']}{user_row['last_name']}")
            print(f"✅ 멘토 정보: {user_row['mentor_last_name']}{user_row['mentor_first_name']} ({user_row['mentor_email']})")
            
            # 태스크 정보 조회
            cur.execute("""
                SELECT ta.task_assign_id, ta.title, ta.description, ta.status,
                       ta.scheduled_start_date, ta.scheduled_end_date,
                       ta.real_start_date, ta.real_end_date
                FROM core_taskassign ta
                WHERE ta.mentorship_id_id = %s
                ORDER BY ta.task_assign_id
            """, (user_row['mentorship_id'],))
            tasks = cur.fetchall()
            
            # 보고서 생성을 위한 데이터 구성
            report_data = {
                'mentee_name': f"{user_row['last_name']}{user_row['first_name']}",
                'role': user_row['role'],
                'mentor_name': f"{user_row['mentor_last_name']}{user_row['mentor_first_name']}",
                'tasks': [{
                    'id': task['task_assign_id'],
                    'title': task['title'],
                    'description': task['description'],
                    'status': task['status'],
                    'start_date': task['scheduled_start_date'],
                    'end_date': task['scheduled_end_date'],
                    'real_start_date': task['real_start_date'],
                    'real_end_date': task['real_end_date']
                } for task in tasks]
            }
            
            # GPT를 사용한 보고서 생성
            prompt = f"""
            다음 정보를 바탕으로 {report_data['mentee_name']} 멘티의 온보딩 최종 보고서를 작성해주세요.

            **요구사항:**
            - 마크다운 문법(##, **, - 등)을 절대 사용하지 말고, 문단 단위의 평문으로 작성할 것.
            - 태스크 수행 내용이 없거나 미흡한 경우, 해당 내용을 명시적으로 평가에 반영할 것.
            - 각 태스크의 제목, 상태, 세부 설명(description) 및 기록을 바탕으로 멘티가 수행한 활동을 평가할 것.
            - 멘티가 수행한 태스크와 상태를 기반으로 성실도, 진행 상황, 개선점을 분석할 것.
            - 최종 평가 보고서는 아래의 네 가지 항목 구조를 반드시 유지할 것:
            1. 전체 온보딩 과정 요약
            2. 주요 성과 및 습득 역량
            3. 개선 필요 사항
            4. 종합 평가

            멘티 정보:
            이름: {report_data['mentee_name']}
            역할: {report_data['role']}
            담당 멘토: {report_data['mentor_name']}

            수행한 태스크:
            {chr(10).join([
                f"- {t['title']}: {t['status']}" +
                (f" (시작: {t['real_start_date']}, 완료: {t['real_end_date']})" if t['real_end_date'] else "")
                for t in report_data['tasks']
            ])}

            위 정보를 바탕으로 태스크 수행 여부를 객관적으로 평가하고, 수행 기록이 부족하거나 없을 경우 그 점을 언급하며 최종 보고서를 작성하세요.
            """
            
            report = llm.invoke(prompt).content
            
            # 보고서 저장
            cur.execute("""
                UPDATE core_mentorship 
                SET report = %s 
                WHERE mentorship_id = %s
            """, (report, user_row['mentorship_id']))
            conn.commit()
            
            # 알림 이벤트 생성
            alarm_events = state.get("alarm_events", [])
            alarm_events.append({
                "event_type": "final_report_ready",
                "user_id": user_id,
                "mentor_id": user_row['mentor_id'],
                "mentor_email": user_row['mentor_email'],
                "mentorship_id": user_row['mentorship_id'],
                "message": f"{report_data['mentee_name']} 멘티의 최종 평가 보고서가 생성되었습니다."
            })
            
            conn.close()
            
            return {
                **state,
                "report_generated_ids": state.get("report_generated_ids", []) + [user_id],
                "alarm_events": alarm_events
            }
            
        except Exception as e:
            print(f"❌ 보고서 생성 실패: {e}")
            return state

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
    nodes = ReportNodes()
    builder = StateGraph(GraphState)
    
    # 노드 추가
    builder.add_node("check_completion", nodes.check_completion)
    builder.add_node("generate_report", nodes.generate_report)
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