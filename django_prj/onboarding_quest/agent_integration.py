# Agent_LangGraph_final.py와 onboarding_quest 통합
"""
Django와 LangGraph Agent 시스템 통합 모듈

1. 통합 아키텍처:
   - Django 뷰에서 Agent 시스템 트리거
   - 백그라운드 스케줄러로 LangGraph 실행
   - FastAPI와 Django ORM 동시 지원

2. 주요 통합 포인트:
   - mentee/views.py의 update_task_status() 함수
   - 태스크 상태 변화 이벤트 감지
   - 자동 알림 및 리뷰 시스템
   - 스케줄러 기반 백그라운드 실행
"""

from typing import Optional, Dict, List
import logging
from datetime import datetime, date, timedelta
from collections import defaultdict
import threading
import time
import os
import sys

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onboarding_quest.settings')
import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings

# OpenAI 설정
from dotenv import load_dotenv
load_dotenv()

try:
    from openai import OpenAI
    from langchain_openai import ChatOpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        client = OpenAI(api_key=openai_api_key)
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=openai_api_key)
    else:
        client = None
        llm = None
        print("⚠️ OpenAI API 키가 설정되지 않았습니다.")
except ImportError:
    client = None
    llm = None
    print("⚠️ OpenAI 관련 라이브러리가 설치되지 않았습니다.")

# LangGraph Agent 시스템 임포트
try:
    # onboarding_quest 프로젝트 내의 agent_langgraph.py에서 스케줄러 함수들 임포트
    from agent_langgraph import (
        start_background_agent,
        stop_background_agent, 
        trigger_immediate_check,
        get_agent_status
    )
    print("✅ LangGraph Agent 시스템 임포트 성공")
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ LangGraph Agent 시스템 임포트 실패: {e}")
    LANGGRAPH_AVAILABLE = False

class OnboardingAgentIntegrator:
    """Django와 LangGraph Agent 시스템을 연결하는 통합 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.agent_thread = None
        self.last_deadline_check = None
        self.reviewed_task_ids = set()
        self.langgraph_enabled = LANGGRAPH_AVAILABLE
        
    def start_langgraph_agent(self):
        """LangGraph Agent 백그라운드 시스템 시작"""
        if not self.langgraph_enabled:
            self.logger.warning("⚠️ LangGraph Agent 시스템이 사용할 수 없습니다.")
            return None
            
        try:
            agent_thread = start_background_agent()
            self.logger.info("🚀 LangGraph Agent 백그라운드 시스템 시작됨")
            return agent_thread
        except Exception as e:
            self.logger.error(f"❌ LangGraph Agent 시작 실패: {e}")
            return None
    
    def stop_langgraph_agent(self):
        """LangGraph Agent 백그라운드 시스템 중지"""
        if not self.langgraph_enabled:
            return
            
        try:
            stop_background_agent()
            self.logger.info("🛑 LangGraph Agent 백그라운드 시스템 중지됨")
        except Exception as e:
            self.logger.error(f"❌ LangGraph Agent 중지 실패: {e}")
    
    def trigger_langgraph_check(self):
        """LangGraph Agent 즉시 체크 트리거"""
        if not self.langgraph_enabled:
            return
            
        try:
            trigger_immediate_check()
            self.logger.info("⚡ LangGraph Agent 즉시 체크 트리거됨")
        except Exception as e:
            self.logger.error(f"❌ LangGraph Agent 트리거 실패: {e}")
    
    def get_langgraph_status(self):
        """LangGraph Agent 상태 조회"""
        if not self.langgraph_enabled:
            return {"is_running": False, "error": "LangGraph not available"}
            
        try:
            return get_agent_status()
        except Exception as e:
            self.logger.error(f"❌ LangGraph Agent 상태 조회 실패: {e}")
            return {"is_running": False, "error": str(e)}
        
    def trigger_status_change_event(self, task_id: int, old_status: str, new_status: str, user_id: int):
        """
        태스크 상태 변화 이벤트를 Agent 시스템에 전달
        
        Args:
            task_id: 변경된 태스크 ID
            old_status: 이전 상태
            new_status: 새로운 상태  
            user_id: 사용자 ID
        """
        try:
            self.logger.info(f"🤖 상태 변화 이벤트 감지: task_id={task_id}, {old_status} -> {new_status}")
            
            # 검토 요청 상태로 변경된 경우 자동 리뷰 트리거
            if new_status == '검토요청' and old_status in ['진행전', '진행중']:
                if task_id not in self.reviewed_task_ids:
                    self._trigger_auto_review(task_id, user_id)
                    self.reviewed_task_ids.add(task_id)
                    # LangGraph Agent에도 즉시 체크 트리거
                    self.trigger_langgraph_check()
                
            # 완료 상태로 변경된 경우 온보딩 완료 체크
            elif new_status == '완료':
                self._check_onboarding_completion(user_id)
                # LangGraph Agent에도 즉시 체크 트리거
                self.trigger_langgraph_check()
                
            self.logger.info(f"✅ 상태 변화 이벤트 처리 완료: task_id={task_id}, {old_status} -> {new_status}")
            
        except Exception as e:
            self.logger.error(f"❌ 상태 변화 이벤트 처리 실패: {e}")
    
    def _trigger_auto_review(self, task_id: int, user_id: int):
        """자동 리뷰 생성 트리거 (Agent_LangGraph_final.py의 ReviewAgent 로직)"""
        try:
            from core.models import TaskAssign, Mentorship, Memo, User
            
            # 태스크 정보 조회
            try:
                task_assign = TaskAssign.objects.get(task_assign_id=task_id)
            except TaskAssign.DoesNotExist:
                self.logger.error(f"❌ 태스크 {task_id}를 찾을 수 없습니다.")
                return
            
            # 멘토십 정보 조회
            mentorship = task_assign.mentorship_id
            if not mentorship:
                self.logger.error(f"❌ 태스크 {task_id}의 멘토십 정보가 없습니다.")
                return
            
            # 하위 태스크들 조회
            subtasks = TaskAssign.objects.filter(parent=task_assign)
            
            if not subtasks.exists() and not llm:
                self.logger.warning(f"⚠️ 하위 태스크가 없고 LLM이 설정되지 않아 자동 리뷰를 생성할 수 없습니다.")
                return
            
            # 자동 피드백 생성
            if llm:
                subtask_text = "\n".join([
                    f"- {subtask.title}: {subtask.description or '내용 없음'}" 
                    for subtask in subtasks
                ]) if subtasks.exists() else "하위 태스크 없음"
                
                prompt = f"""너는 IT 멘토입니다. 상위 업무는 '{task_assign.title}'이고, 하위 작업은 다음과 같습니다:
{subtask_text}

다음 형식으로 피드백 작성:
- 👍 잘한 점:
- 🔧 개선할 점:
- 🧾 요약 피드백:
---"""
                
                try:
                    feedback = llm.invoke(prompt).content
                    
                    # 멘토 객체 조회
                    from core.models import User
                    mentor = User.objects.get(user_id=mentorship.mentor_id)
                    
                    # 피드백을 메모로 저장
                    Memo.objects.create(
                        task_assign=task_assign,
                        user=mentor,
                        comment=feedback
                    )
                    
                    self.logger.info(f"✅ 자동 리뷰 생성 완료: task_id={task_id}")
                    
                    # 멘티에게 알림
                    self._send_review_notification(task_assign.mentorship_id.mentee_id, task_assign.title)
                    
                except Exception as llm_error:
                    self.logger.error(f"❌ LLM 피드백 생성 실패: {llm_error}")
            else:
                # LLM이 없는 경우 기본 피드백
                basic_feedback = f"""
자동 생성된 리뷰입니다.

👍 잘한 점:
- '{task_assign.title}' 태스크를 검토 요청 상태로 변경하여 적극적으로 진행하고 있습니다.

🔧 개선할 점:
- 담당 멘토가 직접 상세한 피드백을 제공할 예정입니다.

🧾 요약 피드백:
해당 태스크가 검토 단계에 도달했습니다. 곧 담당 멘토의 상세한 검토가 이루어질 예정입니다.
"""
                
                # 멘토 객체 조회
                from core.models import User
                mentor = User.objects.get(user_id=mentorship.mentor_id)
                
                Memo.objects.create(
                    task_assign=task_assign,
                    user=mentor,
                    comment=basic_feedback
                )
                
                self.logger.info(f"✅ 기본 자동 리뷰 생성 완료: task_id={task_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 자동 리뷰 생성 실패: {e}")
    
    def _send_review_notification(self, mentee_id: int, task_title: str):
        """멘티에게 리뷰 완료 알림 발송"""
        try:
            from core.models import User, Alarm
            
            mentee = User.objects.get(user_id=mentee_id)
            
            # 내부 알림 생성
            Alarm.objects.create(
                user=mentee,
                message=f"'{task_title}' 태스크에 대한 멘토의 리뷰가 작성되었습니다. 확인해 주세요.",
                is_active=True
            )
            
            self.logger.info(f"✅ 리뷰 완료 알림 발송: mentee_id={mentee_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 리뷰 완료 알림 발송 실패: {e}")
    
    def _check_onboarding_completion(self, user_id: int):
        """온보딩 완료 여부 체크 및 보고서 생성 (Agent_LangGraph_final.py의 EventAgent.check_completion 로직)"""
        try:
            from core.models import Mentorship, TaskAssign, User
            
            # 사용자의 활성 멘토십 조회
            active_mentorship = Mentorship.objects.filter(
                mentee_id=user_id,
                is_active=True
            ).first()
            
            if not active_mentorship:
                return
            
            # 해당 멘토십의 모든 태스크 조회
            all_tasks = TaskAssign.objects.filter(
                mentorship_id=active_mentorship,
                parent__isnull=True  # 상위 태스크만
            )
            
            # 모든 태스크가 완료되었는지 확인
            incomplete_tasks = all_tasks.exclude(status='완료')
            
            if not incomplete_tasks.exists():
                self.logger.info(f"🎉 온보딩 완료 감지: user_id={user_id}")
                self._generate_final_report(user_id, active_mentorship)
                
        except Exception as e:
            self.logger.error(f"❌ 온보딩 완료 체크 실패: {e}")
    
    def _generate_final_report(self, user_id: int, mentorship):
        """최종 보고서 생성 (Agent_LangGraph_final.py의 ReportAgent 로직)"""
        try:
            from core.models import User, TaskAssign, Memo
            
            mentee = User.objects.get(user_id=user_id)
            full_name = f"{mentee.last_name}{mentee.first_name}"
            
            # 모든 태스크 및 메모 조회
            all_tasks = TaskAssign.objects.filter(mentorship_id=mentorship)
            all_memos = Memo.objects.filter(task_assign__in=all_tasks)
            
            if llm:
                # AI 기반 종합 보고서 생성
                report_data = f"""
멘티: {full_name}
멘토십 ID: {mentorship.mentorship_id}
총 태스크 수: {all_tasks.count()}
완료된 태스크 수: {all_tasks.filter(status='완료').count()}

태스크별 상세 정보:
"""
                for task in all_tasks.filter(parent__isnull=True):  # 상위 태스크만
                    task_memos = task.memo_set.all()
                    memo_text = "\n".join([memo.comment for memo in task_memos]) if task_memos.exists() else "메모 없음"
                    
                    report_data += f"""
- {task.title}
  상태: {task.status}
  설명: {task.description or '설명 없음'}
  피드백: {memo_text}
"""
                
                prompt = f"""다음 정보를 바탕으로 신입사원 온보딩 과정에 대한 종합 평가 보고서를 작성해주세요:

{report_data}

다음 구조로 작성해주세요:
1. 전체 학습 과정 요약
2. 주요 성취사항
3. 개선이 필요한 영역
4. 종합 평가 및 추천사항
"""
                
                try:
                    final_report = llm.invoke(prompt).content
                except Exception as llm_error:
                    self.logger.error(f"❌ AI 보고서 생성 실패: {llm_error}")
                    final_report = self._generate_basic_report(mentee, all_tasks, all_memos)
            else:
                final_report = self._generate_basic_report(mentee, all_tasks, all_memos)
            
            # 보고서를 파일로 저장하거나 데이터베이스에 저장
            self._save_final_report(user_id, mentorship.mentorship_id, final_report)
            
            # 멘토에게 보고서 완성 알림
            self._notify_mentor_report_ready(mentorship.mentor_id, full_name)
            
            self.logger.info(f"✅ 최종 보고서 생성 완료: user_id={user_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 최종 보고서 생성 실패: {e}")
    
    def _generate_basic_report(self, mentee, all_tasks, all_memos):
        """기본 보고서 생성 (AI 없이)"""
        full_name = f"{mentee.last_name}{mentee.first_name}"
        total_tasks = all_tasks.count()
        completed_tasks = all_tasks.filter(status='완료').count()
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return f"""
{full_name} 멘티 온보딩 완료 보고서

1. 전체 학습 과정 요약
- 총 태스크 수: {total_tasks}개
- 완료된 태스크: {completed_tasks}개  
- 완료율: {completion_rate:.1f}%

2. 태스크별 상세 현황
{chr(10).join([f"- {task.title}: {task.status}" for task in all_tasks.filter(parent__isnull=True)])}

3. 종합 평가
모든 온보딩 과정을 성공적으로 완료하였습니다.
총 {all_memos.count()}개의 피드백이 제공되었습니다.

보고서 생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def _save_final_report(self, user_id: int, mentorship_id: int, report_content: str):
        """최종 보고서 저장"""
        try:
            # 보고서 파일로 저장
            report_dir = os.path.join(os.path.dirname(__file__), 'reports')
            os.makedirs(report_dir, exist_ok=True)
            
            filename = f"onboarding_report_{user_id}_{mentorship_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(report_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"✅ 보고서 파일 저장 완료: {filepath}")
            
            # 추가로 데이터베이스에도 저장할 수 있음
            # Report 모델이 있다면 여기서 저장
            
        except Exception as e:
            self.logger.error(f"❌ 보고서 저장 실패: {e}")
    
    def _notify_mentor_report_ready(self, mentor_id: int, mentee_name: str):
        """멘토에게 보고서 완성 알림"""
        try:
            from core.models import User, Alarm
            
            mentor = User.objects.get(user_id=mentor_id)
            
            Alarm.objects.create(
                user=mentor,
                message=f"{mentee_name} 멘티의 온보딩 과정이 완료되어 최종 평가 보고서가 생성되었습니다.",
                is_active=True
            )
            
            self.logger.info(f"✅ 멘토 보고서 완성 알림 발송: mentor_id={mentor_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 멘토 보고서 완성 알림 발송 실패: {e}")
    
    def start_monitoring(self):
        """통합 모니터링 시작 (기존 + LangGraph Agent)"""
        if not self.is_running:
            # 기존 Django 기반 모니터링 시작
            self.is_running = True
            self.agent_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.agent_thread.start()
            self.logger.info("🤖 Django Agent 모니터링 시작됨")
            
            # LangGraph Agent 백그라운드 시스템도 시작
            langgraph_thread = self.start_langgraph_agent()
            if langgraph_thread:
                self.logger.info("🚀 통합 Agent 시스템 (Django + LangGraph) 시작 완료")
            else:
                self.logger.info("🤖 Django Agent 모니터링만 시작됨 (LangGraph 사용 불가)")
    
    def stop_monitoring(self):
        """통합 모니터링 중지 (기존 + LangGraph Agent)"""
        # Django 기반 모니터링 중지
        self.is_running = False
        if self.agent_thread:
            self.agent_thread.join(timeout=10)
        self.logger.info("🤖 Django Agent 모니터링 중지됨")
        
        # LangGraph Agent 백그라운드 시스템도 중지
        self.stop_langgraph_agent()
        self.logger.info("🛑 통합 Agent 시스템 (Django + LangGraph) 중지 완료")
    
    def _monitoring_loop(self):
        """지속적인 모니터링 루프 (Agent_LangGraph_final.py의 메인 루프와 동일)"""
        while self.is_running:
            try:
                # 마감일 체크 (하루에 한 번만)
                today = date.today()
                if self.last_deadline_check != today:
                    self._check_deadlines()
                    self.last_deadline_check = today
                
                # 온보딩 완료 상태 체크  
                self._check_all_onboarding_completions()
                
                time.sleep(300)  # 5분 간격으로 체크 (Django 기반 모니터링)
                
            except Exception as e:
                self.logger.error(f"❌ Django 모니터링 루프 오류: {e}")
                time.sleep(300)  # 오류 시 5분 대기
    
    def _check_deadlines(self):
        """모든 활성 멘티의 마감일 체크 (Agent_LangGraph_final.py의 EventAgent 로직)"""
        try:
            from core.models import User, TaskAssign, Alarm, Mentorship
            
            today = date.today()
            tomorrow = today + timedelta(days=1)
            
            # 멘티들의 태스크 조회
            mentees = User.objects.filter(role='mentee')
            
            for mentee in mentees:
                # 해당 멘티의 멘토십 조회
                mentorships = Mentorship.objects.filter(mentee_id=mentee.user_id, is_active=True)
                if not mentorships.exists():
                    continue
                
                # 해당 멘티의 태스크들 중 마감일이 오늘이거나 내일인 것들
                today_tasks = TaskAssign.objects.filter(
                    mentorship_id__in=mentorships,
                    scheduled_end_date=today,
                    status__in=['진행전', '진행중']
                )
                
                tomorrow_tasks = TaskAssign.objects.filter(
                    mentorship_id__in=mentorships,
                    scheduled_end_date=tomorrow,
                    status__in=['진행전', '진행중']
                )
                
                overdue_tasks = TaskAssign.objects.filter(
                    mentorship_id__in=mentorships,
                    scheduled_end_date__lt=today,
                    status__in=['진행전', '진행중']
                )
                
                # 알림 메시지 생성
                if today_tasks.exists() or tomorrow_tasks.exists() or overdue_tasks.exists():
                    message_parts = [f"안녕하세요, {mentee.last_name}{mentee.first_name}님."]
                    
                    if overdue_tasks.exists():
                        overdue_titles = [task.title for task in overdue_tasks[:3]]
                        message_parts.append(f"마감일이 지난 태스크: {', '.join(overdue_titles)}")
                    
                    if today_tasks.exists():
                        today_titles = [task.title for task in today_tasks[:3]]
                        message_parts.append(f"오늘 마감인 태스크: {', '.join(today_titles)}")
                    
                    if tomorrow_tasks.exists():
                        tomorrow_titles = [task.title for task in tomorrow_tasks[:3]]
                        message_parts.append(f"내일 마감인 태스크: {', '.join(tomorrow_titles)}")
                    
                    message_parts.append("마감일을 놓치지 않도록 확인해 주세요.")
                    
                    full_message = "\n".join(message_parts)
                    
                    # 알림 생성
                    Alarm.objects.create(
                        user=mentee,
                        message=full_message,
                        is_active=True
                    )
            
            self.logger.info(f"✅ 마감일 체크 완료: {today}")
            
        except Exception as e:
            self.logger.error(f"❌ 마감일 체크 실패: {e}")
    
    def _check_all_onboarding_completions(self):
        """모든 멘티의 온보딩 완료 상태 체크"""
        try:
            from core.models import User, Mentorship
            
            # 활성 멘토십이 있는 모든 멘티 조회
            active_mentorships = Mentorship.objects.filter(is_active=True)
            mentee_ids = [m.mentee_id for m in active_mentorships]
            mentees = User.objects.filter(
                role='mentee',
                user_id__in=mentee_ids
            ).distinct()
            
            for mentee in mentees:
                self._check_onboarding_completion(mentee.user_id)
            
        except Exception as e:
            self.logger.error(f"❌ 전체 온보딩 완료 체크 실패: {e}")


# 전역 인스턴스
agent_integrator = OnboardingAgentIntegrator()

# Django 앱 시작/종료 시 통합 Agent 시스템 제어
def start_agent_system():
    """Django 앱 시작 시 호출되는 함수 - 통합 Agent 시스템 시작"""
    try:
        agent_integrator.start_monitoring()
        print("🚀 통합 Agent 시스템 (Django + LangGraph) 시작 완료")
    except Exception as e:
        print(f"❌ 통합 Agent 시스템 시작 실패: {e}")

def stop_agent_system():
    """Django 앱 종료 시 호출되는 함수 - 통합 Agent 시스템 중지"""
    try:
        agent_integrator.stop_monitoring()
        print("🛑 통합 Agent 시스템 (Django + LangGraph) 중지 완료")
    except Exception as e:
        print(f"❌ 통합 Agent 시스템 중지 실패: {e}")

# 외부에서 사용할 수 있는 함수들
def trigger_agent_check():
    """이벤트 발생 시 즉시 Agent 체크 (Django + LangGraph)"""
    try:
        # Django 기반 체크도 가능하면 추가
        agent_integrator.trigger_langgraph_check()
        print("⚡ Agent 체크 트리거 완료")
    except Exception as e:
        print(f"❌ Agent 체크 트리거 실패: {e}")

def get_agent_current_status():
    """통합 Agent 상태 조회 (Django + LangGraph)"""
    try:
        django_status = {
            "django_monitoring": agent_integrator.is_running,
            "reviewed_tasks": len(agent_integrator.reviewed_task_ids),
            "last_deadline_check": agent_integrator.last_deadline_check
        }
        
        langgraph_status = agent_integrator.get_langgraph_status()
        
        return {
            "django_agent": django_status,
            "langgraph_agent": langgraph_status,
            "integration_enabled": agent_integrator.langgraph_enabled
        }
    except Exception as e:
        return {"error": str(e)}

# 태스크 상태 변화 이벤트 처리 (Django 뷰에서 호출)
def handle_task_status_change(task_id: int, old_status: str, new_status: str, user_id: int):
    """태스크 상태 변화 이벤트 처리 (Django 뷰에서 호출)"""
    try:
        agent_integrator.trigger_status_change_event(task_id, old_status, new_status, user_id)
        print(f"✅ 태스크 상태 변화 이벤트 처리 완료: {task_id} ({old_status} → {new_status})")
    except Exception as e:
        print(f"❌ 태스크 상태 변화 이벤트 처리 실패: {e}")
