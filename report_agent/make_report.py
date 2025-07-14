import sqlite3
import sqlite3
import os

db_path = "report_agent_test.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# === 테이블 생성 ===
cursor.executescript("""
CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT CHECK(role IN ('mentor', 'mentee')) NOT NULL
);

CREATE TABLE task (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    guide TEXT,
    date TEXT,
    content TEXT
);

CREATE TABLE subtask (
    subtask_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    guide TEXT,
    date TEXT,
    content TEXT,
    FOREIGN KEY(task_id) REFERENCES task(task_id) ON DELETE CASCADE
);

CREATE TABLE task_assign (
    task_id INTEGER NOT NULL,
    mentee_id INTEGER NOT NULL,
    mentor_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, mentee_id),
    FOREIGN KEY(task_id) REFERENCES task(task_id),
    FOREIGN KEY(mentee_id) REFERENCES user(user_id),
    FOREIGN KEY(mentor_id) REFERENCES user(user_id)
);

CREATE TABLE memo (
    memo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    create_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    content TEXT NOT NULL,
    task_id INTEGER,
    subtask_id INTEGER,
    user_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(user_id),
    CHECK (
        (task_id IS NOT NULL AND subtask_id IS NULL) OR
        (task_id IS NULL AND subtask_id IS NOT NULL)
    )
);

CREATE TABLE review (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    subtask_id INTEGER,
    create_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    content TEXT NOT NULL,
    generated_by TEXT DEFAULT '리뷰봇',
    score INTEGER,
    summary TEXT,
    CHECK (
        (task_id IS NOT NULL AND subtask_id IS NULL) OR
        (task_id IS NULL AND subtask_id IS NOT NULL)
    )
);
""")

# === 샘플 데이터 삽입 ===

# 유저
cursor.executemany("INSERT INTO user (name, role) VALUES (?, ?)", [
    ("멘티", "mentee"),
    ("멘토", "mentor")
])

# === 첫 번째 과제 ===
cursor.execute("""
INSERT INTO task (title, guide, date, content)
VALUES (?, ?, ?, ?)
""", (
    "간단한 파이썬 공부하기",
    "기초 문법부터 실습까지 파이썬의 기본 개념을 익히는 과제입니다.",
    "2025.07.14",
    "자료형, 조건문, 반복문, 함수 등을 실습 중심으로 전반적인 파이썬 개념을 익혔습니다."
))
task1_id = cursor.lastrowid

# 첫 번째 과제 할당
cursor.execute("INSERT INTO task_assign (task_id, mentee_id, mentor_id) VALUES (?, ?, ?)", (task1_id, 1, 2))

# 첫 번째 과제의 하위 과제
subtasks1 = [
    ("파이썬 리스트 연습", "리스트 문법 실습", "D-1", "f-string을 사용해 최댓값을 출력했습니다. f-string 문법이 헷갈렸지만, 잘 이해했습니다."),
    ("조건문과 반복문 연습", "`if`, `for`, `while` 문 사용", "D-2", "짝수/홀수 판단 로직 구현을 했습니다. 처음에는 들여쓰기가 어려웠지만, 핵심 조건식은 이해했습니다."),
    ("함수 정의 및 호출", "함수 기본 개념과 매개변수 활용", "D-3", "간단한 계산기 함수를 만들었습니다. 매개변수와 반환값 개념을 이해했습니다.")
]
subtask1_map = {}
for title, guide, date, content in subtasks1:
    cursor.execute("""
    INSERT INTO subtask (task_id, title, guide, date, content)
    VALUES (?, ?, ?, ?, ?)
    """, (task1_id, title, guide, date, content))
    subtask1_map[title] = cursor.lastrowid

# 첫 번째 과제의 하위 태스크 리뷰
cursor.executemany("""
INSERT INTO review (task_id, subtask_id, content, summary)
VALUES (?, ?, ?, ?)
""", [
    (None, subtask1_map["파이썬 리스트 연습"], "리스트와 f-string을 잘 사용함", "리스트 활용 능력을 잘 보여주었습니다."),
    (None, subtask1_map["조건문과 반복문 연습"], "짝수/홀수 판별 로직 정확", "조건 처리가 안정적이었습니다."),
    (None, subtask1_map["함수 정의 및 호출"], "함수 구조를 잘 이해하고 구현함", "함수 개념을 제대로 습득했습니다.")
])

# 첫 번째 과제의 하위 태스크 메모
cursor.executemany("""
INSERT INTO memo (content, task_id, subtask_id, user_id)
VALUES (?, ?, ?, ?)
""", [
    ("f-string 문법이 헷갈렸어요.", None, subtask1_map["파이썬 리스트 연습"], 1),
    ("문법을 잘 정리했습니다.", None, subtask1_map["파이썬 리스트 연습"], 2),
    ("if문 들여쓰기가 어려웠습니다.", None, subtask1_map["조건문과 반복문 연습"], 1),
    ("핵심 조건식은 정확히 이해했습니다.", None, subtask1_map["조건문과 반복문 연습"], 2),
    ("함수 매개변수가 처음엔 어려웠어요.", None, subtask1_map["함수 정의 및 호출"], 1),
    ("함수 개념을 잘 익혔네요.", None, subtask1_map["함수 정의 및 호출"], 2)
])

# 첫 번째 과제의 멘토 총평 메모
cursor.execute("""
INSERT INTO memo (content, task_id, subtask_id, user_id)
VALUES (?, ?, NULL, ?)
""", ("전체 과제를 성실히 수행했고, 실습에 대한 이해도도 높았습니다.", task1_id, 2))

# 첫 번째 과제의 리뷰봇 종합 코멘트 (상위 task에만 score 포함)
cursor.execute("""
INSERT INTO review (task_id, subtask_id, content, score, summary, generated_by)
VALUES (?, NULL, ?, ?, ?, ?)
""", (
    task1_id,
    "기초 문법 전반에 대한 이해도가 높으며, 실습을 통해 내용을 잘 체득함",
    88,
    "기초 개념을 우수하게 습득함",
    "🤖 리뷰봇"
))

# === 두 번째 과제 ===
cursor.execute("""
INSERT INTO task (title, guide, date, content)
VALUES (?, ?, ?, ?)
""", (
    "웹 크롤링 기초 실습",
    "BeautifulSoup와 requests를 사용해 웹페이지에서 데이터를 추출하는 과제입니다.",
    "2025.07.20",
    "웹 요청, HTML 파싱, 데이터 추출 등 웹 크롤링의 기본 개념을 학습했습니다."
))
task2_id = cursor.lastrowid

# 두 번째 과제 할당
cursor.execute("INSERT INTO task_assign (task_id, mentee_id, mentor_id) VALUES (?, ?, ?)", (task2_id, 1, 2))

# 두 번째 과제의 하위 과제
subtasks2 = [
    ("requests 라이브러리 사용", "HTTP 요청 보내기", "D-1", "requests.get()을 사용해 웹페이지를 가져왔습니다. 상태 코드 확인도 해봤습니다."),
    ("BeautifulSoup HTML 파싱", "HTML 태그 선택과 텍스트 추출", "D-2", "find()와 select() 메서드를 사용해 원하는 데이터를 추출했습니다."),
    ("데이터 정리 및 저장", "크롤링한 데이터를 CSV로 저장", "D-3", "pandas를 사용해 데이터를 정리하고 CSV 파일로 저장했습니다."),
    ("에러 처리 및 최적화", "예외 처리와 요청 간격 조절", "D-4", "try-except 문으로 에러를 처리하고 time.sleep()으로 요청 간격을 조절했습니다.")
]
subtask2_map = {}
for title, guide, date, content in subtasks2:
    cursor.execute("""
    INSERT INTO subtask (task_id, title, guide, date, content)
    VALUES (?, ?, ?, ?, ?)
    """, (task2_id, title, guide, date, content))
    subtask2_map[title] = cursor.lastrowid

# 두 번째 과제의 하위 태스크 리뷰 (score 제거)
cursor.executemany("""
INSERT INTO review (task_id, subtask_id, content, summary)
VALUES (?, ?, ?, ?)
""", [
    (None, subtask2_map["requests 라이브러리 사용"], "HTTP 요청과 응답 처리를 잘 이해함", "웹 요청의 기본 원리를 파악했습니다."),
    (None, subtask2_map["BeautifulSoup HTML 파싱"], "HTML 구조를 이해하고 정확한 선택자 사용", "파싱 기법을 효과적으로 활용했습니다."),
    (None, subtask2_map["데이터 정리 및 저장"], "데이터 후처리와 파일 저장을 체계적으로 수행", "데이터 관리 능력이 향상되었습니다."),
    (None, subtask2_map["에러 처리 및 최적화"], "예외 처리와 윤리적 크롤링 고려", "안정적인 크롤링 코드를 작성했습니다.")
])

# 두 번째 과제의 하위 태스크 메모
cursor.executemany("""
INSERT INTO memo (content, task_id, subtask_id, user_id)
VALUES (?, ?, ?, ?)
""", [
    ("상태 코드가 무엇인지 처음 알았어요.", None, subtask2_map["requests 라이브러리 사용"], 1),
    ("HTTP 기본 개념을 잘 이해했습니다.", None, subtask2_map["requests 라이브러리 사용"], 2),
    ("CSS 선택자가 헷갈렸습니다.", None, subtask2_map["BeautifulSoup HTML 파싱"], 1),
    ("선택자 사용법을 정확히 익혔네요.", None, subtask2_map["BeautifulSoup HTML 파싱"], 2),
    ("pandas 사용법이 어려웠어요.", None, subtask2_map["데이터 정리 및 저장"], 1),
    ("데이터 처리 방법을 체계적으로 학습했습니다.", None, subtask2_map["데이터 정리 및 저장"], 2),
    ("왜 시간 간격을 두어야 하는지 이해했어요.", None, subtask2_map["에러 처리 및 최적화"], 1),
    ("윤리적 크롤링 개념을 잘 습득했습니다.", None, subtask2_map["에러 처리 및 최적화"], 2)
])

# 두 번째 과제의 멘토 총평 메모
cursor.execute("""
INSERT INTO memo (content, task_id, subtask_id, user_id)
VALUES (?, ?, NULL, ?)
""", ("웹 크롤링의 전반적인 과정을 잘 이해했고, 윤리적 측면까지 고려한 점이 인상적입니다.", task2_id, 2))

# 두 번째 과제의 리뷰봇 종합 코멘트 (상위 task에만 score 포함)
cursor.execute("""
INSERT INTO review (task_id, subtask_id, content, score, summary, generated_by)
VALUES (?, NULL, ?, ?, ?, ?)
""", (
    task2_id,
    "웹 크롤링의 전체 과정을 체계적으로 학습했으며, 윤리적 고려사항까지 잘 이해함",
    92,
    "웹 크롤링 기술을 우수하게 습득함",
    "🤖 리뷰봇"
))

conn.commit()
conn.close()

print("✅ DB 초기화 및 데이터 삽입 완료:", os.path.abspath(db_path))