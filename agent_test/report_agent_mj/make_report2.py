import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="report_agent_test.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """데이터베이스에 연결"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """테이블 생성"""
        self.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT CHECK(role IN ('mentor', 'mentee')) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS task (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            guide TEXT,
            date TEXT,
            content TEXT
        );

        CREATE TABLE IF NOT EXISTS subtask (
            subtask_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            guide TEXT,
            date TEXT,
            content TEXT,
            FOREIGN KEY(task_id) REFERENCES task(task_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS task_assign (
            task_id INTEGER NOT NULL,
            mentee_id INTEGER NOT NULL,
            mentor_id INTEGER NOT NULL,
            PRIMARY KEY (task_id, mentee_id),
            FOREIGN KEY(task_id) REFERENCES task(task_id),
            FOREIGN KEY(mentee_id) REFERENCES user(user_id),
            FOREIGN KEY(mentor_id) REFERENCES user(user_id)
        );

        CREATE TABLE IF NOT EXISTS memo (
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

        CREATE TABLE IF NOT EXISTS review (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            subtask_id INTEGER,
            create_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            content TEXT NOT NULL,
            generated_by TEXT DEFAULT '🤖리뷰봇',
            score INTEGER,
            summary TEXT,
            CHECK (
                (task_id IS NOT NULL AND subtask_id IS NULL) OR
                (task_id IS NULL AND subtask_id IS NOT NULL)
            )
        );
        """)
    
    def create_users(self):
        """사용자 데이터 생성"""
        users = [
            ("멘티", "mentee"),
            ("멘토", "mentor")
        ]
        
        self.cursor.executemany("INSERT INTO user (name, role) VALUES (?, ?)", users)
        return {
            "mentee_id": 1,
            "mentor_id": 2
        }
    
    def create_task(self, title, guide, date, content):
        """과제 생성"""
        self.cursor.execute("""
        INSERT INTO task (title, guide, date, content)
        VALUES (?, ?, ?, ?)
        """, (title, guide, date, content))
        return self.cursor.lastrowid
    
    def assign_task(self, task_id, mentee_id, mentor_id):
        """과제 할당"""
        self.cursor.execute("""
        INSERT INTO task_assign (task_id, mentee_id, mentor_id) 
        VALUES (?, ?, ?)
        """, (task_id, mentee_id, mentor_id))
    
    def create_subtask(self, task_id, title, guide, date, content):
        """하위 과제 생성"""
        self.cursor.execute("""
        INSERT INTO subtask (task_id, title, guide, date, content)
        VALUES (?, ?, ?, ?, ?)
        """, (task_id, title, guide, date, content))
        return self.cursor.lastrowid
    
    def create_review(self, task_id=None, subtask_id=None, content="", score=None, summary="", generated_by="🤖리뷰봇"):
        """리뷰 생성"""
        self.cursor.execute("""
        INSERT INTO review (task_id, subtask_id, content, score, summary, generated_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, subtask_id, content, score, summary, generated_by))
    
    def create_memo(self, content, user_id, task_id=None, subtask_id=None):
        """메모 생성"""
        self.cursor.execute("""
        INSERT INTO memo (content, task_id, subtask_id, user_id)
        VALUES (?, ?, ?, ?)
        """, (content, task_id, subtask_id, user_id))
    
    def commit(self):
        """변경사항 커밋"""
        self.conn.commit()


def create_python_basics_task(db_manager, user_ids):
    """파이썬 기초 과제 생성"""
    # 과제 생성
    task_id = db_manager.create_task(
        title="간단한 파이썬 공부하기",
        guide="기초 문법부터 실습까지 파이썬의 기본 개념을 익히는 과제입니다.",
        date="2025.07.14",
        content="자료형, 조건문, 반복문, 함수 등을 실습 중심으로 전반적인 파이썬 개념을 익혔습니다."
    )
    
    # 과제 할당
    db_manager.assign_task(task_id, user_ids["mentee_id"], user_ids["mentor_id"])
    
    # 하위 과제 데이터
    subtasks = [
        {
            "title": "파이썬 리스트 연습",
            "guide": "리스트 문법 실습",
            "date": "D-1",
            "content": "f-string을 사용해 최댓값을 출력했습니다. f-string 문법이 헷갈렸지만, 잘 이해했습니다.",
            "review_content": "리스트와 f-string을 잘 사용함",
            "review_summary": "리스트 활용 능력을 잘 보여주었습니다.",
            "mentee_memo": "f-string 문법이 헷갈렸어요.",
            "mentor_memo": "문법을 잘 정리했습니다."
        },
        {
            "title": "조건문과 반복문 연습",
            "guide": "`if`, `for`, `while` 문 사용",
            "date": "D-2",
            "content": "짝수/홀수 판단 로직 구현을 했습니다. 처음에는 들여쓰기가 어려웠지만, 핵심 조건식은 이해했습니다.",
            "review_content": "짝수/홀수 판별 로직 정확",
            "review_summary": "조건 처리가 안정적이었습니다.",
            "mentee_memo": "if문 들여쓰기가 어려웠습니다.",
            "mentor_memo": "핵심 조건식은 정확히 이해했습니다."
        },
        {
            "title": "함수 정의 및 호출",
            "guide": "함수 기본 개념과 매개변수 활용",
            "date": "D-3",
            "content": "간단한 계산기 함수를 만들었습니다. 매개변수와 반환값 개념을 이해했습니다.",
            "review_content": "함수 구조를 잘 이해하고 구현함",
            "review_summary": "함수 개념을 제대로 습득했습니다.",
            "mentee_memo": "함수 매개변수가 처음엔 어려웠어요.",
            "mentor_memo": "함수 개념을 잘 익혔네요."
        }
    ]
    
    # 하위 과제 및 관련 데이터 생성
    subtask_ids = {}
    for subtask in subtasks:
        subtask_id = db_manager.create_subtask(
            task_id=task_id,
            title=subtask["title"],
            guide=subtask["guide"],
            date=subtask["date"],
            content=subtask["content"]
        )
        subtask_ids[subtask["title"]] = subtask_id
        
        # 하위 과제 리뷰
        db_manager.create_review(
            subtask_id=subtask_id,
            content=subtask["review_content"],
            summary=subtask["review_summary"]
        )
        
        # 하위 과제 메모
        db_manager.create_memo(
            content=subtask["mentee_memo"],
            subtask_id=subtask_id,
            user_id=user_ids["mentee_id"]
        )
        db_manager.create_memo(
            content=subtask["mentor_memo"],
            subtask_id=subtask_id,
            user_id=user_ids["mentor_id"]
        )
    
    # 전체 과제 멘토 총평
    db_manager.create_memo(
        content="전체 과제를 성실히 수행했고, 실습에 대한 이해도도 높았습니다.",
        task_id=task_id,
        user_id=user_ids["mentor_id"]
    )
    
    # 전체 과제 리뷰봇 종합 코멘트
    db_manager.create_review(
        task_id=task_id,
        content="기초 문법 전반에 대한 이해도가 높으며, 실습을 통해 내용을 잘 체득함",
        score=88,
        summary="기초 개념을 우수하게 습득함",
        generated_by="🤖 리뷰봇"
    )


def create_web_crawling_task(db_manager, user_ids):
    """웹 크롤링 과제 생성"""
    # 과제 생성
    task_id = db_manager.create_task(
        title="웹 크롤링 기초 실습",
        guide="BeautifulSoup와 requests를 사용해 웹페이지에서 데이터를 추출하는 과제입니다.",
        date="2025.07.20",
        content="웹 요청, HTML 파싱, 데이터 추출 등 웹 크롤링의 기본 개념을 학습했습니다."
    )
    
    # 과제 할당
    db_manager.assign_task(task_id, user_ids["mentee_id"], user_ids["mentor_id"])
    
    # 하위 과제 데이터
    subtasks = [
        {
            "title": "requests 라이브러리 사용",
            "guide": "HTTP 요청 보내기",
            "date": "D-1",
            "content": "requests.get()을 사용해 웹페이지를 가져왔습니다. 상태 코드 확인도 해봤습니다.",
            "review_content": "HTTP 요청과 응답 처리를 잘 이해함",
            "review_summary": "웹 요청의 기본 원리를 파악했습니다.",
            "mentee_memo": "상태 코드가 무엇인지 처음 알았어요.",
            "mentor_memo": "HTTP 기본 개념을 잘 이해했습니다."
        },
        {
            "title": "BeautifulSoup HTML 파싱",
            "guide": "HTML 태그 선택과 텍스트 추출",
            "date": "D-2",
            "content": "find()와 select() 메서드를 사용해 원하는 데이터를 추출했습니다.",
            "review_content": "HTML 구조를 이해하고 정확한 선택자 사용",
            "review_summary": "파싱 기법을 효과적으로 활용했습니다.",
            "mentee_memo": "CSS 선택자가 헷갈렸습니다.",
            "mentor_memo": "선택자 사용법을 정확히 익혔네요."
        },
        {
            "title": "데이터 정리 및 저장",
            "guide": "크롤링한 데이터를 CSV로 저장",
            "date": "D-3",
            "content": "pandas를 사용해 데이터를 정리하고 CSV 파일로 저장했습니다.",
            "review_content": "데이터 후처리와 파일 저장을 체계적으로 수행",
            "review_summary": "데이터 관리 능력이 향상되었습니다.",
            "mentee_memo": "pandas 사용법이 어려웠어요.",
            "mentor_memo": "데이터 처리 방법을 체계적으로 학습했습니다."
        },
        {
            "title": "에러 처리 및 최적화",
            "guide": "예외 처리와 요청 간격 조절",
            "date": "D-4",
            "content": "try-except 문으로 에러를 처리하고 time.sleep()으로 요청 간격을 조절했습니다.",
            "review_content": "예외 처리와 윤리적 크롤링 고려",
            "review_summary": "안정적인 크롤링 코드를 작성했습니다.",
            "mentee_memo": "왜 시간 간격을 두어야 하는지 이해했어요.",
            "mentor_memo": "윤리적 크롤링 개념을 잘 습득했습니다."
        }
    ]
    
    # 하위 과제 및 관련 데이터 생성
    subtask_ids = {}
    for subtask in subtasks:
        subtask_id = db_manager.create_subtask(
            task_id=task_id,
            title=subtask["title"],
            guide=subtask["guide"],
            date=subtask["date"],
            content=subtask["content"]
        )
        subtask_ids[subtask["title"]] = subtask_id
        
        # 하위 과제 리뷰
        db_manager.create_review(
            subtask_id=subtask_id,
            content=subtask["review_content"],
            summary=subtask["review_summary"]
        )
        
        # 하위 과제 메모
        db_manager.create_memo(
            content=subtask["mentee_memo"],
            subtask_id=subtask_id,
            user_id=user_ids["mentee_id"]
        )
        db_manager.create_memo(
            content=subtask["mentor_memo"],
            subtask_id=subtask_id,
            user_id=user_ids["mentor_id"]
        )
    
    # 전체 과제 멘토 총평
    db_manager.create_memo(
        content="웹 크롤링의 전반적인 과정을 잘 이해했고, 윤리적 측면까지 고려한 점이 인상적입니다.",
        task_id=task_id,
        user_id=user_ids["mentor_id"]
    )
    
    # 전체 과제 리뷰봇 종합 코멘트
    db_manager.create_review(
        task_id=task_id,
        content="웹 크롤링의 전체 과정을 체계적으로 학습했으며, 윤리적 고려사항까지 잘 이해함",
        score=92,
        summary="웹 크롤링 기술을 우수하게 습득함",
        generated_by="🤖 리뷰봇"
    )


def main():
    """메인 실행 함수"""
    # 데이터베이스 매니저 초기화
    db_manager = DatabaseManager()
    
    try:
        # 데이터베이스 연결
        db_manager.connect()
        
        # 테이블 생성
        db_manager.create_tables()
        
        # 사용자 생성
        user_ids = db_manager.create_users()
        
        # 과제들 생성
        create_python_basics_task(db_manager, user_ids)
        create_web_crawling_task(db_manager, user_ids)
        
        # 변경사항 커밋
        db_manager.commit()
        
        print("✅ DB 초기화 및 데이터 삽입 완료:", os.path.abspath(db_manager.db_path))
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        # 데이터베이스 연결 종료
        db_manager.close()


if __name__ == "__main__":
    main()