'''
Task Agent 설계 시키기
'''


import sqlite3
import os

# DB 파일 경로
db_path = "my_database.db"

# 연결 및 FK 제약조건 활성화
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# ✅ tasks 테이블 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    guide TEXT,
    date TEXT,
    content TEXT
)
""")

# ✅ subtasks 테이블 생성 (tasks.id 참조)
cursor.execute("""
CREATE TABLE IF NOT EXISTS subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    guide TEXT,
    date TEXT,
    content TEXT,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
)
""")

# ✅ 메인 task 삽입
main_task = (
    "Task Agent 구현하기",
    "LangGraph 기반 멀티에이전트 시스템 내에서, 자연어 명령을 기반으로 태스크를 생성·관리하는 Task Agent를 구현합니다.",
    "D-1",
    "사용자 요청으로부터 task 생성, subtasks 분해, DB 저장, 상태 변경 트리거까지 전 과정을 자동화하는 Task Agent 개발을 목표로 합니다."
)

cursor.execute("""
INSERT INTO tasks (title, guide, date, content)
VALUES (?, ?, ?, ?)
""", main_task)

# ✅ 방금 삽입한 task의 ID 가져오기
task_id = cursor.lastrowid

# ✅ subtasks 삽입
subtasks = [
    (
        "요구사항 정의 및 기능 목록 도출",
        "Task Agent가 처리할 수 있는 기능 목록을 정리하고 요구사항 명세서를 작성하세요.",
        "D-1",
        "Task 생성, subtasks 분해, 상태 변경 감지, LangGraph 내 위치 정의 등 포함."
    ),
    (
        "DB 스키마 설계 및 구축",
        "tasks / subtasks 구조로 테이블을 설계하고, 필요한 제약조건(FK, 삭제시 CASCADE 등)을 명확히 하세요.",
        "D-2",
        "SQLite 기반으로 tasks, subtasks 테이블 설계 및 예시 데이터 작성 완료."
    ),
    (
        "LangGraph 내 Task Agent 진입 조건 설계",
        "LangGraph 상에서 Task Agent가 언제 호출될지, 분기 흐름을 정의하세요.",
        "D-2",
        "`event_type == 'create_task'` 조건에서 Task Agent 진입되도록 설정함."
    ),
    (
        "사용자 자연어 입력 파싱 및 태스크 자동 생성",
        "LLM을 사용해 자연어 입력에서 태스크 제목과 세부 작업 목록을 자동 생성하는 기능을 구현하세요.",
        "D-3",
        "ChatOpenAI 기반으로 입력을 파싱하고 subtasks 리스트 자동 생성 완료."
    ),
    (
        "태스크 상태 관리 및 검토 요청 감지 트리거 구현",
        "태스크가 특정 상태로 변경되었을 때 알림 또는 후속 에이전트가 작동되도록 감지 코드를 작성하세요.",
        "D-4",
        "진행 중 → 검토 요청 시 알림 발생 / scheduled_end_date 감지까지 구현."
    ),
    (
        "Agent 통합 및 LangGraph 내 테스트 수행",
        "전체 시스템 상에서 Task Agent가 정상적으로 작동하는지 테스트하세요.",
        "D-5",
        "LangGraph Flow에서 정상 작동 확인 / 각 상태별 흐름 검증 완료."
    )
]

cursor.executemany("""
INSERT INTO subtasks (title, guide, date, content, task_id)
VALUES (?, ?, ?, ?, ?)
""", [(*subtask, task_id) for subtask in subtasks])

# ✅ 저장 및 종료
conn.commit()
conn.close()

# ✅ 경로 확인
print("📁 DB 생성 완료:", os.path.abspath(db_path))
