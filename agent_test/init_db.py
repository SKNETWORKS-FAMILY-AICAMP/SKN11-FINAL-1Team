import sqlite3
from datetime import datetime, timedelta
import random
import os

# 1. DB 파일 제거 (기존 DB 초기화용)
db_path = "sample.db"
if os.path.exists(db_path):
    os.remove(db_path)

# 2. DB 연결 및 테이블 생성
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE task_assignment (
    task_assign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mentorship_id INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    exp INTEGER NOT NULL,
    description TEXT,
    difficulty TEXT NOT NULL,
    status TEXT NOT NULL,
    scheduled_start_date TEXT NOT NULL,
    real_end_date TEXT,
    real_start_date TEXT,
    title TEXT NOT NULL,
    scheduled_end_date TEXT NOT NULL
)
""")

# 3. 샘플 데이터 정의
statuses = ["진행 전", "진행 중"]
difficulties = ["하", "중", "상"]
titles = [
    "계정 생성", "시스템 소개", "보안 교육", "팀 소개 미팅", "업무 툴 세팅",
    "온보딩 문서 읽기", "샘플 태스크 수행", "코드베이스 이해", "프로젝트 구조 파악", "테스트 작성",
    "회의 참여", "슬랙 채널 가입", "문서화 연습", "개발환경 구성", "버그 수정",
    "리뷰 받기", "협업 도구 사용법", "배포 프로세스 학습", "보고서 작성", "최종 피드백"
]

# 4. 샘플 데이터 삽입
today = datetime.now()
for i in range(20):
    title = titles[i]
    status = random.choice(statuses)
    real_start = (today + timedelta(days=i - 1)).strftime("%Y-%m-%d") if status != "진행 전" else None

    cur.execute("""
        INSERT INTO task_assignment (
            user_id, mentorship_id, "order", exp, description,
            difficulty, status, scheduled_start_date, real_end_date,
            real_start_date, title, scheduled_end_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        random.randint(1, 3),
        random.randint(1, 2),
        i + 1,
        random.randint(10, 100),
        f"{title}에 대한 설명입니다.",
        random.choice(difficulties),
        status,
        (today + timedelta(days=i)).strftime("%Y-%m-%d"),
        None,
        real_start,
        title,
        (today + timedelta(days=i + 3)).strftime("%Y-%m-%d")
    ))

# 5. 완료
conn.commit()
conn.close()
print("✅ sample.db 초기화 및 데이터 삽입 완료!")
