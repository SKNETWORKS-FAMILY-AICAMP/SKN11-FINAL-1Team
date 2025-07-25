import multiprocessing
from datetime import datetime
from config import settings

bind = "0.0.0.0:8001"  # 바인드할 주소와 포트
workers = multiprocessing.cpu_count() * 2 + 1  # 워커 개수(코어 수 기반)
worker_class = "uvicorn.workers.UvicornWorker"  # Uvicorn 워커 클래스
daemon = False  # 데몬 실행 여부
timeout = 30  # 워커 타임아웃(초)
keepalive = 2  # keepalive 타임아웃(초)

# 로그 파일 및 레벨 설정 (옵션)
loglevel = settings.log_level.lower()
accesslog = f"/log/uvicorn/access_{datetime.now().strftime('%Y-%m-%d_%H')}.log"
errorlog = f"/log/uvicorn/error_{datetime.now().strftime('%Y-%m-%d_%H')}.log"

# 필요시 추가 설정
# graceful_timeout = 30
# max_requests = 1000
# max_requests_jitter = 50
# preload_app = False
reload = settings.debug  # 디버그 모드에서 자동 리로드 활성화