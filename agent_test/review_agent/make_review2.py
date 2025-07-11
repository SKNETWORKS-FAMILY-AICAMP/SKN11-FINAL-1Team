'''
틀린 파이썬 코드를 올바른 코드로 수정하고 리뷰받음 
'''


import sqlite3
import os

# DB 파일 경로
db_path = "my_database2.db"

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
    "간단한 파이썬 공부하기",
    "파이썬의 기초 문법부터 간단한 실습까지 따라하면서, 프로그래밍의 기본 개념을 익힙니다.",
    "D-1",
    "자료형, 조건문, 반복문, 함수 등을 중심으로 파이썬의 핵심 개념을 실습 위주로 학습합니다."
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
        "파이썬 리스트 연습",
        "간단한 Python 리스트 연습을 해보세요.",
        "D-1",
        """
        numbers = [3, 7, 1, 15, 9]
        max_num = max(numbers)
        print(최댓값은 {max_num}입니다.)

        이 코드를

        numbers = [3, 7, 1, 15, 9]
        max_num = max(numbers)
        print(f"최댓값은 {max_num}입니다.")

        이렇게 수정하였습니다.
        """
    ),
    (
        "조건문과 반복문 연습",
        "`if`, `for`, `while` 문을 활용한 분기 및 반복 흐름을 익혀보세요.",
        "D-2",
        """
        num = int(input('숫자를 입력하세요:'))
            if num // 2 == 0:
                print('짝수입니다.')
            else:
                print('홀수입니다.')

            이 코드를 

            num = int(input('숫자를 입력하세요: '))
            if num % 2 == 0:
                print('짝수입니다.')
            else:
                print('홀수입니다.')

            이렇게 수정하였습니다.
        """
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
