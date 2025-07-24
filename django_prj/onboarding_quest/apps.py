# Django 앱 설정 파일
from django.apps import AppConfig

class OnboardingQuestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'onboarding_quest'
    
    def ready(self):
        """Django 앱이 준비되었을 때 안전하게 Agent 시스템을 백그라운드에서 시작"""
        import threading
        def start_agent():
            try:
                from .agent_integration import start_agent_system
                start_agent_system()
                print("🤖 Onboarding Agent 시스템이 시작되었습니다. (agent_langgraph.py 연동)")
            except Exception as e:
                print(f"⚠️ Agent 시스템 시작 실패: {e}")
        threading.Thread(target=start_agent, daemon=True).start()
