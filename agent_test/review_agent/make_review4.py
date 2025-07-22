'''
실제 기업 클린코드만들기
'''


import sqlite3
import os

# DB 파일 경로
db_path = "my_database4.db"

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
    "파이썬 공부하기",
    "파이썬의 기초 문법부터 간단한 실습까지 따라하면서, 프로그래밍의 기본 개념을 익힙니다.",
    "D-1",
    "파이썬의 가독성을 위한 코드 작성을 연습했습니다"
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
        "파이썬 연습",
        "파이썬의 가독성을 위해 클린코드를 작성해보세요",
        "D-1",
        """
        from datetime import datetime

        def is_adult(age):
            return age >= 18

        def joined_in_2020(joined_date):
            try:
                return datetime.strptime(joined_date, "%Y-%m-%d").year == 2020
            except ValueError:
                return False

        def describe_user(user):
            name = user.get("name", "이름 없음")
            age = user.get("age", 0)
            joined = user.get("joined", "1900-01-01")

            if is_adult(age):
                print(f"{name}은 성인입니다.")
                if joined_in_2020(joined):
                    print("2020년에 가입한 사용자입니다.")
            else:
                print(f"{name}은 미성년자입니다.")

        def process_users(users):
            for user in users:
                describe_user(user)




        이 코드를
        import datetime

        def process_users(users):
            for user in users:
                if user["age"] > 18:
                    print(user["name"] + "은 성인입니다.")
                    if user["joined"].split("-")[0] == "2020":
                        print("2020년에 가입한 사용자입니다.")
                else:
                    print(user["name"] + "은 미성년자입니다.")

        users = [
            {"name": "홍길동", "age": 25, "joined": "2020-05-01"},
            {"name": "김철수", "age": 17, "joined": "2021-03-10"}
        ]

        process_users(users)


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
