from django.apps import AppConfig
import psycopg2
import os

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Django 앱이 준비되면 Agent 시스템 시작"""
        try:
            # Agent 통합 시스템 임포트 및 시작
            from agent_integration import start_agent_system
            start_agent_system()
        except ImportError:
            print("⚠️ agent_integration 모듈을 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ Agent 시스템 자동 시작 실패: {e}")


# init_db.py


def enable_wal_mode():
    """PostgreSQL에서는 WAL 모드가 기본적으로 활성화되어 있음"""
    try:
        # PostgreSQL 연결 설정
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'onboarding_quest'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        conn = psycopg2.connect(**db_config)
        conn.close()
        
        print("PostgreSQL 연결 확인 완료")
    except Exception as e:
        print(f"PostgreSQL 연결 중 오류: {e}")

if __name__ == "__main__":
    enable_wal_mode()
