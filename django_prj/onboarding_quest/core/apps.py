from django.apps import AppConfig
import psycopg2
import os

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Django 앱이 준비되면 안전하게 Agent 시스템을 백그라운드에서 시작"""
        import threading
        def start_agent():
            try:
                from agent_integration import start_agent_system
                start_agent_system()
            except ImportError:
                print("⚠️ agent_integration 모듈을 찾을 수 없습니다.")
            except Exception as e:
                print(f"❌ Agent 시스템 자동 시작 실패: {e}")
        threading.Thread(target=start_agent, daemon=True).start()


# init_db.py


def enable_wal_mode():
    """PostgreSQL에서는 WAL 모드가 기본적으로 활성화되어 있음"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # PostgreSQL 연결 설정 (.env 파일 기반)
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'onboarding_quest_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        conn = psycopg2.connect(**db_config)
        conn.close()
        
        print(f"✅ PostgreSQL 연결 확인 완료: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    except Exception as e:
        print(f"❌ PostgreSQL 연결 중 오류: {e}")

if __name__ == "__main__":
    enable_wal_mode()
