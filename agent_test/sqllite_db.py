import sqlite3
from datetime import datetime

# DB 연결
conn = sqlite3.connect("test.db")
cursor = conn.cursor()

# 1. 유저 테이블
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_db (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    personal_email TEXT
)
""")

# 2. 멘토십 테이블
cursor.execute("""
CREATE TABLE IF NOT EXISTS mentorship_db (
    mentorship_id INTEGER PRIMARY KEY,
    mentor_id INTEGER,
    mentee_id INTEGER
)
""")

# 3. 발신자 설정 테이블
cursor.execute("""
CREATE TABLE IF NOT EXISTS email_config (
    id INTEGER PRIMARY KEY,
    sender_email TEXT,
    sender_password TEXT,
    sender_name TEXT,
    created_at TEXT
)
""")

# 4. 샘플 데이터 초기화
cursor.execute("DELETE FROM user_db")
cursor.execute("DELETE FROM mentorship_db")
cursor.execute("DELETE FROM email_config")

# 5. 샘플 유저 입력 (멘토 & 멘티)
cursor.execute("INSERT INTO user_db VALUES (1, '김사수', 'mentor@corp.com', 'sjin0422@gmail.com')")
cursor.execute("INSERT INTO user_db VALUES (2, '박신입', 'mentee@corp.com', 'mentee.park@gmail.com')")

# 6. 멘토-멘티 연결
cursor.execute("INSERT INTO mentorship_db VALUES (1, 1, 2)")

# 7. 발신자 설정 입력
cursor.execute("""
INSERT INTO email_config (sender_email, sender_password, sender_name, created_at)
VALUES (?, ?, ?, ?)
""", (
    "jinseulshin1@gmail.com",            # 실제 Gmail 주소
    "bxlu agsc hahu iidh",                # 앱 비밀번호 (16자리) -> jinseulshin1@gmail.com에 발급받은 앱 비밀번호
    "HR 알림봇",
    datetime.utcnow().isoformat()
))

conn.commit()
conn.close()
print("✅ DB 및 샘플 데이터 생성 완료")
