#!/usr/bin/env python3
"""
Django와 FastAPI 서버를 동시에 실행하는 스크립트
"""
import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path

# 프로젝트 루트 디렉터리
PROJECT_ROOT = Path(__file__).parent.absolute()
DJANGO_DIR = PROJECT_ROOT / "django_prj" / "onboarding_quest"
FASTAPI_DIR = PROJECT_ROOT / "fast_api"
FASTAPI_APP_DIR = PROJECT_ROOT / "fast_api" / "app"

# 서버 프로세스를 저장할 변수
django_process = None
fastapi_process = None

def run_django_server():
    """Django 개발 서버 실행"""
    global django_process
    print("🚀 Django 서버 시작 중... (http://localhost:8000)")
    
    os.chdir(DJANGO_DIR)
    try:
        django_process = subprocess.Popen([
            sys.executable, 
            "manage.py", 
            "runserver", 
            "127.0.0.1:8000"
        ])
        django_process.wait()
    except Exception as e:
        print(f"❌ Django 서버 실행 중 오류: {e}")

def run_fastapi_server():
    """FastAPI 서버 실행"""
    global fastapi_process
    print("🚀 FastAPI 서버 시작 중... (http://localhost:8001)")
    
    os.chdir(FASTAPI_DIR)
    try:
        fastapi_process = subprocess.Popen([
            sys.executable,
            "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8001",
            "--reload"
        ])
        fastapi_process.wait()
    except Exception as e:
        print(f"❌ FastAPI 서버 실행 중 오류: {e}")

def signal_handler(signum, frame):
    """종료 신호 처리"""
    print("\n🛑 서버 종료 중...")
    
    if django_process:
        django_process.terminate()
        print("✅ Django 서버 종료됨")
    
    if fastapi_process:
        fastapi_process.terminate()
        print("✅ FastAPI 서버 종료됨")
    
    sys.exit(0)

def check_requirements():
    """필요한 패키지 설치 확인"""
    print("📋 환경 검사 중...")
    
    # Django 필요 패키지 확인
    django_requirements = DJANGO_DIR / "requirements.txt"
    if django_requirements.exists():
        print("✅ Django requirements.txt 확인됨")
    else:
        print("❌ Django requirements.txt를 찾을 수 없습니다")
        return False
    
    # FastAPI 필요 패키지 확인
    fastapi_requirements = FASTAPI_APP_DIR / "requirements.txt"
    if fastapi_requirements.exists():
        print("✅ FastAPI requirements.txt 확인됨")
    else:
        print("❌ FastAPI requirements.txt를 찾을 수 없습니다")
        return False
    
    return True

def setup_database():
    """데이터베이스 초기화"""
    print("🗄️  데이터베이스 초기화 중...")
    
    # Django 마이그레이션
    os.chdir(DJANGO_DIR)
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("✅ Django 마이그레이션 완료")
    except subprocess.CalledProcessError:
        print("❌ Django 마이그레이션 실패")
        return False
    
    # FastAPI 데이터베이스 초기화
    os.chdir(FASTAPI_APP_DIR)
    try:
        subprocess.run([sys.executable, "init_db.py"], check=True)
        print("✅ FastAPI 데이터베이스 초기화 완료")
    except subprocess.CalledProcessError:
        print("⚠️  FastAPI 데이터베이스 초기화 실패 (이미 초기화되었을 수 있음)")
    
    return True

def main():
    """메인 함수"""
    print("🔧 Django + FastAPI 통합 서버 시작")
    print("=" * 50)
    
    # 종료 신호 처리 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 환경 검사
    if not check_requirements():
        print("❌ 환경 검사 실패. 종료합니다.")
        sys.exit(1)
    
    # 데이터베이스 설정
    if not setup_database():
        print("❌ 데이터베이스 설정 실패. 종료합니다.")
        sys.exit(1)
    
    print("\n🌐 서버 정보:")
    print(f"   Django:  http://localhost:8000")
    print(f"   FastAPI: http://localhost:8001")
    print(f"   API 문서: http://localhost:8001/docs")
    print(f"   통합 대시보드: http://localhost:8000/common/integrated/")
    print("\n종료하려면 Ctrl+C를 누르세요.")
    print("=" * 50)
    
    # 서버 실행 (별도 스레드에서)
    django_thread = threading.Thread(target=run_django_server)
    fastapi_thread = threading.Thread(target=run_fastapi_server)
    
    django_thread.start()
    time.sleep(2)  # Django 서버가 먼저 시작되도록 대기
    fastapi_thread.start()
    
    try:
        # 메인 스레드에서 대기
        django_thread.join()
        fastapi_thread.join()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 