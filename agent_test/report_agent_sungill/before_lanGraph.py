from typing import Dict, Any, Optional
from openai import OpenAI
from datetime import datetime
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# SQLite 데이터베이스 설정
DB_PATH = 'task_management.db'

# OpenAI 클라이언트 초기화
api_key = os.getenv('OPENAI_API_KEY') 
client = OpenAI(api_key=api_key)

class ReportAgent:
    def __init__(self):
        self.db_path = DB_PATH
    
    def create_connection(self):
        """SQLite 데이터베이스 연결 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            return None
    
    def get_mentorship_info(self, mentee_user_id: str) -> Dict[str, Any]:
        """멘티의 멘토쉽 정보 및 멘토 정보 가져오기"""
        conn = self.create_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # 멘티의 멘토쉽 ID 찾기
            cursor.execute('''
                SELECT DISTINCT mentorship_id FROM task_assign 
                WHERE user_id = ?
            ''', (mentee_user_id,))
            
            mentorship_result = cursor.fetchone()
            if not mentorship_result:
                return {}
            
            mentorship_id = mentorship_result[0]
            
            # 해당 멘토쉽의 멘토 정보 찾기 (수정된 로직)
            # 멘토쉽 ID에 따른 멘토 user_id 계산: 멘토쉽 1 -> 멘토 user_id 1, 멘토쉽 2 -> 멘토 user_id 3, 등등
            mentor_user_id = (mentorship_id - 1) * 2 + 1
            
            cursor.execute('''
                SELECT user_id, username, email, role 
                FROM users 
                WHERE role = 'mentor' AND user_id = ?
            ''', (mentor_user_id,))
            
            mentor_result = cursor.fetchone()
            if not mentor_result:
                return {}
            
            mentor_info = {
                'user_id': mentor_result[0],
                'username': mentor_result[1],
                'email': mentor_result[2],
                'role': mentor_result[3]
            }
            
            return {
                'mentorship_id': mentorship_id,
                'mentor_info': mentor_info
            }
            
        except Exception as e:
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def fetch_comprehensive_user_data(self, user_id: str) -> Dict[str, Any]:
        """사용자의 종합적인 데이터를 모든 테이블에서 가져오기 (멘토 메모 포함)"""
        conn = self.create_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # 사용자 기본 정보 확인 (멘티인지 확인)
            cursor.execute('''
                SELECT user_id, username, email, role, created_at
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            user_result = cursor.fetchone()
            if not user_result:
                print(f"사용자 ID {user_id}를 찾을 수 없습니다.")
                return {}
            
            # 멘티가 아닌 경우 체크
            if user_result[3] != 'mentee':
                print(f"사용자 ID {user_id}는 멘티가 아닙니다. (역할: {user_result[3]})")
                return {}
            
            user_info = {
                'user_id': user_result[0],
                'username': user_result[1],
                'email': user_result[2],
                'role': user_result[3],
                'created_at': user_result[4]
            }
            
            print(f"멘티 정보 확인: {user_info['username']} (ID: {user_info['user_id']})")
            
            # 멘토쉽 정보 가져오기
            mentorship_info = self.get_mentorship_info(user_info['user_id'])
            
            # 할당된 작업 정보
            cursor.execute('''
                SELECT task_assign_id, title, start_date, end_date, status, 
                       difficulty, guide, exp, order_num, mentorship_id
                FROM task_assign 
                WHERE user_id = ?
                ORDER BY order_num, start_date
            ''', (user_info['user_id'],))
            
            task_results = cursor.fetchall()
            print(f"할당된 작업 수: {len(task_results)}")
            
            tasks = []
            for row in task_results:
                task_data = {
                    'task_assign_id': row[0],
                    'title': row[1],
                    'start_date': row[2],
                    'end_date': row[3],
                    'status': row[4],
                    'difficulty': row[5],
                    'guide': row[6],
                    'exp': row[7],
                    'order_num': row[8],
                    'mentorship_id': row[9]
                }
                
                # 각 작업의 하위 작업 정보
                cursor.execute('''
                    SELECT subtask_id, subtask_title, guide, content
                    FROM subtask 
                    WHERE task_assign_id = ?
                ''', (row[0],))
                
                subtasks = []
                for subtask_row in cursor.fetchall():
                    subtasks.append({
                        'subtask_id': subtask_row[0],
                        'subtask_title': subtask_row[1],
                        'guide': subtask_row[2],
                        'content': subtask_row[3]
                    })
                
                task_data['subtasks'] = subtasks
                
                # 각 작업의 메모 정보 (멘토와 멘티 메모 모두 포함)
                cursor.execute('''
                    SELECT m.memo_id, m.create_date, m.comment, m.user_id, u.username, u.role
                    FROM memo m
                    JOIN users u ON m.user_id = u.user_id
                    WHERE m.task_assign_id = ?
                    ORDER BY m.create_date ASC
                ''', (row[0],))
                
                memos = []
                mentor_memos = []
                mentee_memos = []
                
                for memo_row in cursor.fetchall():
                    memo_data = {
                        'memo_id': memo_row[0],
                        'create_date': memo_row[1],
                        'comment': memo_row[2],
                        'user_id': memo_row[3],
                        'username': memo_row[4],
                        'role': memo_row[5]
                    }
                    memos.append(memo_data)
                    
                    # 역할별로 메모 분류
                    if memo_row[5] == 'mentor':
                        mentor_memos.append(memo_data)
                    elif memo_row[5] == 'mentee':
                        mentee_memos.append(memo_data)
                
                task_data['memos'] = memos
                task_data['mentor_memos'] = mentor_memos
                task_data['mentee_memos'] = mentee_memos
                tasks.append(task_data)
            
            user_data = {
                'user_info': user_info,
                'mentorship_info': mentorship_info,
                'tasks': tasks,
                'total_tasks': len(tasks),
                'completed_tasks': len([t for t in tasks if t['status'] == 2]),
                'in_progress_tasks': len([t for t in tasks if t['status'] == 1]),
                'total_exp': sum([t['exp'] for t in tasks if t['exp']]),
                'all_memos': [],
                'all_mentor_memos': [],
                'all_mentee_memos': []
            }
            
            # 모든 메모를 한 곳에 모으기
            for task in tasks:
                user_data['all_memos'].extend(task['memos'])
                user_data['all_mentor_memos'].extend(task['mentor_memos'])
                user_data['all_mentee_memos'].extend(task['mentee_memos'])
            
            print(f"총 메모 수: {len(user_data['all_memos'])}")
            return user_data
            
        except Exception as e:
            print(f"데이터 조회 중 오류: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def prepare_comprehensive_content_with_mentor(self, user_data: Dict[str, Any]) -> str:
        """멘토 메모를 포함한 사용자의 모든 데이터를 종합하여 분석용 텍스트로 준비"""
        user_info = user_data['user_info']
        mentorship_info = user_data['mentorship_info']
        tasks = user_data['tasks']
        
        content_parts = []
        
        # 사용자 기본 정보
        content_parts.append(f"=== 멘티 정보 ===")
        content_parts.append(f"멘티명: {user_info['username']}")
        content_parts.append(f"이메일: {user_info['email']}")
        content_parts.append(f"가입일: {user_info['created_at']}")
        content_parts.append(f"총 작업 수: {user_data['total_tasks']}")
        content_parts.append(f"완료된 작업 수: {user_data['completed_tasks']}")
        content_parts.append(f"진행중인 작업 수: {user_data['in_progress_tasks']}")
        content_parts.append(f"총 경험치: {user_data['total_exp']}")
        content_parts.append("")
        
        # 멘토 정보
        if mentorship_info and 'mentor_info' in mentorship_info:
            mentor = mentorship_info['mentor_info']
            content_parts.append(f"=== 담당 멘토 정보 ===")
            content_parts.append(f"멘토명: {mentor['username']}")
            content_parts.append(f"멘토쉽 ID: {mentorship_info['mentorship_id']}")
            content_parts.append("")
        
        # 작업별 상세 정보 (멘토-멘티 대화 포함)
        for i, task in enumerate(tasks, 1):
            content_parts.append(f"=== 작업 {i}: {task['title']} ===")
            content_parts.append(f"기간: {task['start_date']} ~ {task['end_date']}")
            content_parts.append(f"난이도: {task['difficulty']}")
            
            # 상태 표시 개선
            status_text = {0: '시작 전', 1: '진행중', 2: '완료'}.get(task['status'], '알 수 없음')
            content_parts.append(f"상태: {status_text}")
            content_parts.append(f"경험치: {task['exp']}")
            
            if task['guide']:
                content_parts.append(f"가이드: {task['guide']}")
            
            # 하위 작업 정보
            if task['subtasks']:
                content_parts.append("하위 작업:")
                for j, subtask in enumerate(task['subtasks'], 1):
                    content_parts.append(f"  {j}. {subtask['subtask_title']}")
                    if subtask['content']:
                        content_parts.append(f"     내용: {subtask['content']}")
                    if subtask['guide']:
                        content_parts.append(f"     가이드: {subtask['guide']}")
            
            # 멘토-멘티 대화 메모 (시간순 정렬)
            if task['memos']:
                content_parts.append("멘토링 대화 기록:")
                for memo in task['memos']:
                    role_indicator = "🎓 멘토" if memo['role'] == 'mentor' else "👨‍💻 멘티"
                    content_parts.append(f"  [{memo['create_date']}] {role_indicator} {memo['username']}: {memo['comment']}")
            
            content_parts.append("")
        
        return "\n".join(content_parts)
    
    def create_integrated_summary_with_mentor(self, comprehensive_content: str) -> str:
        """멘토 피드백을 포함한 종합적인 사용자 데이터를 바탕으로 통합 요약 생성"""
        if not comprehensive_content.strip():
            return "분석할 데이터가 없습니다."
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 경험이 풍부한 조직 개발 전문가이자 멘토링 프로그램 매니저입니다. 
                        다음과 같은 전문성을 가지고 있습니다:
                        - 신입 직원 온보딩 프로그램 설계 및 운영 경험 15년 이상
                        - 멘토-멘티 관계 분석 및 멘토링 효과성 평가 전문가
                        - 멘티의 성장과 적응도를 객관적으로 평가하는 전문 지식
                        - 멘토의 지도 방식과 피드백 품질 분석 능력
                        - 건설적 피드백 제공 및 개선 방안 도출 능력
                        
                        주어진 멘티의 종합적인 온보딩 데이터와 멘토의 피드백을 분석하여 다음을 포함하는 평가 보고서를 작성하세요:
                        
                        1. **멘토링 관계 평가**
                           - 멘토의 지도 방식과 피드백 품질
                           - 멘티의 반응성과 학습 태도
                           - 멘토-멘티 간 커뮤니케이션 효과성
                        
                        2. **멘티 성과 분석**
                           - 작업 수행 능력 및 성장 패턴
                           - 문제 해결 능력과 자기주도 학습 정도
                           - 기술적 역량 발전 상황
                        
                        3. **멘토 피드백 분석**
                           - 멘토가 제공한 조언의 적절성과 구체성
                           - 멘티의 성장을 돕는 효과적인 지도 사례
                           - 멘토의 전문성이 드러나는 부분
                        
                        4. **종합 평가 및 권장사항**
                           - 멘티의 강점과 개선이 필요한 영역
                           - 멘토링 프로세스 개선점
                           - 향후 발전 방향 및 구체적 권장사항
                        
                        평가는 15-20줄의 종합적이고 구체적인 내용으로 작성해주세요. 
                        멘토의 피드백과 멘티의 응답을 연결지어 분석하고, 실제 대화 내용에서 나타나는 구체적인 사례를 인용해주세요."""
                    },
                    {
                        "role": "user",
                        "content": f"다음은 멘티의 종합적인 온보딩 데이터와 멘토의 피드백이 포함된 데이터입니다. 이를 분석하여 멘토링 관계를 고려한 종합 평가 보고서를 작성해주세요:\n\n{comprehensive_content}"
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            return result
            
        except Exception as e:
            return f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
    
    def create_report_summary(self, user_id: str) -> str:
        """사용자별 종합 리포트 생성 (멘토 메모 포함)"""
        comprehensive_data = self.fetch_comprehensive_user_data(user_id)
        
        if not comprehensive_data:
            return "해당 멘티의 데이터가 없습니다."
        
        # 모든 데이터를 종합하여 통합 요약 생성
        all_content = self.prepare_comprehensive_content_with_mentor(comprehensive_data)
        combined_summary = self.create_integrated_summary_with_mentor(all_content)
        
        return combined_summary

def extract_user_id(input_query: str) -> str:
    """입력 쿼리에서 사용자 ID 추출"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """사용자가 "[누군가]의 보고서를 작성해줘" 또는 "[누군가]에 대한 보고서를 써줘" 형식의 요청을 할 때, 
                    그 사람의 이름이나 식별자만 추출해서 응답하세요. 
                    예시:
                    - "User123의 보고서를 작성해줘" → "User123"
                    - "김철수에 대한 보고서를 써줘" → "김철수"
                    - "user2의 보고서를 작성해줘" → "2"
                    - "2번 사용자의 보고서를 작성해줘" → "2"
                    
                    만약 명확한 대상이 없다면 "2"라고 응답하세요. (멘티 기본값)"""
                },
                {
                    "role": "user",
                    "content": f"{input_query}"
                }
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        if response.choices[0].message.content:
            extracted_id = response.choices[0].message.content.strip()
            
            # 추가 검증: 만약 응답이 너무 길거나 이상하면 기본값 사용
            if len(extracted_id) <= 10 and "보고서" not in extracted_id:
                return extracted_id
                
    except Exception as e:
        pass
    
    return "2"  # 기본값

def generate_report(input_query: str):
    """메인 보고서 생성 함수"""
    # 보고서 관련 키워드 체크
    report_keywords = ["보고서", "리포트", "report", "요약", "summary", "평가"]
    
    if not any(keyword in input_query.lower() for keyword in report_keywords):
        print("일반적인 질문에 대한 응답입니다.")
        return
    
    # 사용자 ID 추출
    user_id = extract_user_id(input_query)
    print(f"요청된 사용자 ID: {user_id}")
    
    # 보고서 생성 및 출력
    agent = ReportAgent()
    report = agent.create_report_summary(user_id)
    
    if report == "해당 멘티의 데이터가 없습니다.":
        print(f"사용자 ID {user_id}에 해당하는 멘티 데이터를 찾을 수 없습니다.")
        print("데이터베이스에 존재하는 멘티 목록을 확인해보세요.")
        
        # 가능한 멘티 목록 조회
        conn = agent.create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, role FROM users WHERE role = 'mentee' ORDER BY user_id")
                mentees = cursor.fetchall()
                if mentees:
                    print("\n사용 가능한 멘티 목록:")
                    for mentee in mentees:
                        print(f"  - ID {mentee[0]}: {mentee[1]} ({mentee[2]})")
                else:
                    print("멘티가 없습니다.")
                cursor.close()
            except Exception as e:
                print(f"멘티 목록 조회 중 오류: {e}")
            finally:
                conn.close()
    else:
        print("\n" + "="*80)
        print("멘토링 기반 종합 평가 보고서")
        print("="*80)
        print(report)
        print("="*80)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 명령행 인자가 있으면 해당 쿼리로 실행
        query = " ".join(sys.argv[1:])
        generate_report(query)
    else:
        # 기본 테스트 실행
        generate_report("2번 멘티의 보고서를 작성해줘")