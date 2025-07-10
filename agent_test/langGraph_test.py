from csv import unregister_dialect
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from typing import Dict, List, Any, Optional
from openai import OpenAI
from datetime import datetime
import os
import sqlite3
import sys
from dotenv import load_dotenv

load_dotenv()

# SQLite 데이터베이스 설정
DB_PATH = 'task_management.db'

# OpenAI 클라이언트 초기화 (API 키가 없어도 작동하도록 수정)
print("OpenAI 초기화 시작...")

# .env 파일에서 환경 변수 로드
api_key = os.getenv('OPENAI_API_KEY') 
print(f"API 키 상태: {'설정됨' if api_key else '설정되지 않음'}")

try:
    if api_key:
        client = OpenAI(api_key=api_key)
        OPENAI_AVAILABLE = True
        print("OpenAI 클라이언트 초기화 성공")
    else:
        client = None
        OPENAI_AVAILABLE = False
        print("OpenAI API 키가 없어서 클라이언트를 초기화하지 않음")
except Exception as e:
    client = None
    OPENAI_AVAILABLE = False
    print(f"OpenAI 클라이언트 초기화 실패: {e}")

print(f"OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")





class ReportAgent:
    def __init__(self):
        self.db_path = DB_PATH
    
    def create_connection(self):
        """SQLite 데이터베이스 연결 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            print(f"데이터베이스 연결 실패: {e}")
            return None
    
        





    
    def fetch_comprehensive_user_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자의 종합적인 데이터를 모든 테이블에서 가져오기"""
        conn = self.create_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # 사용자 기본 정보
            if user_id:
                cursor.execute('''
                    SELECT user_id, username, email, created_at
                    FROM users 
                    WHERE user_id = ?
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT user_id, username, email, created_at
                    FROM users 
                    ORDER BY user_id
                ''')
            
            users_data = []
            for row in cursor.fetchall():
                users_data.append({
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'created_at': row[3]
                })
            
            # 각 사용자별로 상세 데이터 수집
            comprehensive_data = {}
            
            for user in users_data:
                uid = str(user['user_id'])
                
                # 특정 사용자만 요청된 경우 해당 사용자만 처리
                if user_id and str(user_id) != uid:
                    continue
                
                # 할당된 작업 정보
                cursor.execute('''
                    SELECT task_assign_id, title, start_date, end_date, status, 
                           difficulty, guide, exp, order_num, mentorship_id
                    FROM task_assign 
                    WHERE user_id = ?
                    ORDER BY order_num, start_date
                ''', (user['user_id'],))
                
                tasks = []
                for row in cursor.fetchall():
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
                    
                    # 각 작업의 메모 정보
                    cursor.execute('''
                        SELECT memo_id, create_date, comment
                        FROM memo 
                        WHERE task_assign_id = ?
                        ORDER BY create_date DESC
                    ''', (row[0],))
                    
                    memos = []
                    for memo_row in cursor.fetchall():
                        memos.append({
                            'memo_id': memo_row[0],
                            'create_date': memo_row[1],
                            'comment': memo_row[2]
                        })
                    
                    task_data['memos'] = memos
                    tasks.append(task_data)
                
                comprehensive_data[uid] = {
                    'user_info': user,
                    'tasks': tasks,
                    'total_tasks': len(tasks),
                    'completed_tasks': len([t for t in tasks if t['status'] == 1]),
                    'total_exp': sum([t['exp'] for t in tasks if t['exp']]),
                    'all_memos': []
                }
                
                # 모든 메모를 한 곳에 모으기
                for task in tasks:
                    comprehensive_data[uid]['all_memos'].extend(task['memos'])
                
                print(f"사용자 {uid}({user['username']})의 데이터:")
                print(f"  - 총 작업 수: {len(tasks)}")
                print(f"  - 완료된 작업 수: {len([t for t in tasks if t['status'] == 1])}")
                print(f"  - 총 메모 수: {len(comprehensive_data[uid]['all_memos'])}")
                print(f"  - 총 경험치: {comprehensive_data[uid]['total_exp']}")
            
            return comprehensive_data
            
        except Exception as e:
            print(f"데이터 조회 오류: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    










    
    def create_report_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자별 종합 리포트 생성 (모든 테이블 데이터 활용)"""
        comprehensive_data = self.fetch_comprehensive_user_data(user_id)
        
        if not comprehensive_data:
            return {
                'user_id': user_id,
                'total_tasks': 0,
                'total_memos': 0,
                'summary': '해당 사용자의 데이터가 없습니다.',
                'combined_summary': '데이터가 없습니다.',
                'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 특정 사용자 요청 시 해당 사용자 데이터만 반환
        if user_id and str(user_id) in comprehensive_data:
            user_data = comprehensive_data[str(user_id)]
            print(f"DEBUG: 사용자 {user_id} 데이터 찾음")
            print(f"  - 사용자명: {user_data['user_info']['username']}")
            print(f"  - 총 작업 수: {user_data['total_tasks']}")
            print(f"  - 완료된 작업 수: {user_data['completed_tasks']}")
            print(f"  - 총 메모 수: {len(user_data['all_memos'])}")
            print(f"  - 총 경험치: {user_data['total_exp']}")
            
            # 모든 데이터를 종합하여 통합 요약 생성
            all_content = self.prepare_comprehensive_content(user_data)
            combined_summary = self.create_integrated_summary_comprehensive(all_content)
            print(f"DEBUG: 종합 통합 요약 생성됨: {combined_summary[:100]}...")
            
            return {
                'user_id': user_id,
                'user_info': user_data['user_info'],
                'total_tasks': user_data['total_tasks'],
                'completed_tasks': user_data['completed_tasks'],
                'total_memos': len(user_data['all_memos']),
                'total_exp': user_data['total_exp'],
                'tasks_detail': user_data['tasks'],
                'combined_summary': combined_summary,
                'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        print(f"DEBUG: 사용자 {user_id} 데이터를 찾을 수 없음")
        
        # 전체 사용자 데이터 반환
        return {
            'all_users': comprehensive_data,
            'total_users': len(comprehensive_data),
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def prepare_comprehensive_content(self, user_data: Dict[str, Any]) -> str:
        """사용자의 모든 데이터를 종합하여 분석용 텍스트로 준비"""
        user_info = user_data['user_info']
        tasks = user_data['tasks']
        
        content_parts = []
        
        # 사용자 기본 정보
        content_parts.append(f"=== 사용자 정보 ===")
        content_parts.append(f"사용자명: {user_info['username']}")
        content_parts.append(f"이메일: {user_info['email']}")
        content_parts.append(f"가입일: {user_info['created_at']}")
        content_parts.append(f"총 작업 수: {user_data['total_tasks']}")
        content_parts.append(f"완료된 작업 수: {user_data['completed_tasks']}")
        content_parts.append(f"총 경험치: {user_data['total_exp']}")
        content_parts.append("")
        
        # 작업별 상세 정보
        for i, task in enumerate(tasks, 1):
            content_parts.append(f"=== 작업 {i}: {task['title']} ===")
            content_parts.append(f"기간: {task['start_date']} ~ {task['end_date']}")
            content_parts.append(f"난이도: {task['difficulty']}")
            content_parts.append(f"상태: {'완료' if task['status'] == 1 else '진행중'}")
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
            
            # 메모 정보
            if task['memos']:
                content_parts.append("작업 메모:")
                for j, memo in enumerate(task['memos'], 1):
                    content_parts.append(f"  [{memo['create_date']}] {memo['comment']}")
            
            content_parts.append("")
        
        return "\n".join(content_parts)
    
    def create_integrated_summary_comprehensive(self, comprehensive_content: str) -> str:
        """종합적인 사용자 데이터를 바탕으로 통합 요약 생성"""
        print(f"DEBUG: create_integrated_summary_comprehensive 호출됨")
        print(f"DEBUG: 종합 콘텐츠 길이: {len(comprehensive_content)}")
        
        if not comprehensive_content.strip():
            return "분석할 데이터가 없습니다."
        
        # OpenAI로 종합 분석 및 요약 생성
        print(f"DEBUG: OPENAI_AVAILABLE={OPENAI_AVAILABLE}, client={client is not None}")
        if OPENAI_AVAILABLE and client:
            try:
                print("DEBUG: OpenAI API 호출 시도 (종합 분석)")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": """당신은 경험이 풍부한 조직 개발 전문가이자 멘토링 프로그램 매니저입니다. 
                            다음과 같은 전문성을 가지고 있습니다:
                            - 신입 직원 온보딩 프로그램 설계 및 운영 경험 10년 이상
                            - 멘티의 성장과 적응도를 객관적으로 평가하는 전문 지식
                            - 조직 내 인재 개발 및 성과 관리 전문성
                            - 건설적 피드백 제공 및 개선 방안 도출 능력
                            
                            주어진 멘티의 종합적인 온보딩 데이터를 분석하여 다음을 포함하는 평가 보고서를 작성하세요:
                            1. 전반적인 온보딩 진행 상황 평가
                            2. 작업 수행 능력 및 성장 패턴 분석
                            3. 메모를 통해 나타나는 학습 태도 및 문제 해결 능력
                            4. 강점과 개선이 필요한 영역
                            5. 향후 발전 방향 및 권장사항
                            
                            평가는 12-15줄의 종합적이고 구체적인 내용으로 작성해주세요."""
                        },
                        {
                            "role": "user",
                            "content": f"다음은 멘티의 종합적인 온보딩 데이터입니다. 이를 분석하여 평가 보고서를 작성해주세요:\n\n{comprehensive_content}"
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
                print(f"DEBUG: OpenAI 종합 분석 응답 받음 (길이: {len(result)})")
                return result
                
            except Exception as e:
                print(f"DEBUG: OpenAI API 호출 중 오류 발생: {e}")
                print(f"DEBUG: 오류 타입: {type(e)}")
        else:
            print("DEBUG: OpenAI 사용 불가 - 대체 요약 사용")
        
        # OpenAI 사용 불가시 간단한 분석
        fallback_result = self.create_simple_comprehensive_summary(comprehensive_content)
        print(f"DEBUG: 대체 종합 요약 사용: {fallback_result}")
        return fallback_result
    
    def create_simple_comprehensive_summary(self, content: str) -> str:
        """OpenAI 사용 불가시 간단한 종합 요약"""
        lines = content.split('\n')
        
        # 기본 정보 추출
        summary_parts = []
        summary_parts.append("=== 온보딩 진행 상황 요약 ===")
        
        # 사용자 정보 및 통계 찾기
        for line in lines:
            if "총 작업 수:" in line or "완료된 작업 수:" in line or "총 경험치:" in line:
                summary_parts.append(line.strip())
        
        # 작업 제목들 추출
        tasks = []
        for line in lines:
            if line.startswith("=== 작업") and ":" in line:
                task_title = line.split(":", 1)[1].strip().replace(" ===", "")
                tasks.append(task_title)
        
        if tasks:
            summary_parts.append(f"\n수행한 주요 작업들:")
            for i, task in enumerate(tasks[:5], 1):  # 최대 5개만 표시
                summary_parts.append(f"{i}. {task}")
        
        summary_parts.append(f"\n총 {len(tasks)}개의 작업을 통해 다양한 기술과 경험을 쌓고 있습니다.")
        
        return "\n".join(summary_parts)
    
    def create_integrated_summary(self, comments: List[str]) -> str:
        """모든 comment를 한 번에 통합 요약"""
        # print(f"DEBUG: create_integrated_summary 호출됨, comments 개수: {len(comments)}")
        
        if not comments:
            return "요약할 내용이 없습니다."
        
        if len(comments) == 1:
            # print(f"DEBUG: 단일 comment 처리: {comments[0]}")
            # 단일 comment인 경우에도 요약 처리
            return self.summarize_single_content(comments[0])
        
        # 모든 comment를 하나의 텍스트로 결합
        all_comments_text = "\n\n".join([f"메모 {i+1}: {comment}" for i, comment in enumerate(comments)])
        # print(f"DEBUG: 결합된 전체 텍스트 길이: {len(all_comments_text)}")
        # print(f"DEBUG: 결합된 텍스트 미리보기:")
        print(f"  {all_comments_text[:300]}...")
        
        # OpenAI로 통합 요약 생성
        print(f"DEBUG: OPENAI_AVAILABLE={OPENAI_AVAILABLE}, client={client is not None}")
        if OPENAI_AVAILABLE and client:
            try:
                print("DEBUG: OpenAI API 호출 시도")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 경험이 풍부한 조직 개발 전문가이자 멘토링 프로그램 매니저입니다. 다음과 같은 전문성을 가지고 있습니다: - 신입 직원 온보딩 프로그램 설계 및 운영 경험 10년 이상 - 멘티의 성장과 적응도를 객관적으로 평가하는 전문 지식 - 조직 내 인재 개발 및 성과 관리 전문성 - 건설적 피드백 제공 및 개선 방안 도출 능력 주어진 멘티의 온보딩 과정 중 수행한 태스크 기록들을 종합적으로 분석하여, 멘티의 현재 상태와 향후 발전 방향을 제시하는 평가 보고서를 작성해야 합니다. 평가는 공정하고 객관적이며, 멘티의 성장을 돕는 방향으로 이루어져야 합니다."
                        },
                        {
                            "role": "user",
                            "content": f"다음은 멘티가 온보딩 과정에서 작성한 여러 업무 메모들입니다. 이를 종합적으로 분석하여 10~12줄의 통합 평가 보고서를 작성해주세요:\n\n{all_comments_text}"
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
                print(f"DEBUG: OpenAI 응답 받음 (길이: {len(result)})")
                print(f"DEBUG: OpenAI 응답 내용:")
                print(result)
                return result
                
            except Exception as e:
                print(f"DEBUG: OpenAI API 호출 중 오류 발생: {e}")
                print(f"DEBUG: 오류 타입: {type(e)}")
        else:
            print("DEBUG: OpenAI 사용 불가 - 대체 요약 사용")
        
        # OpenAI 사용 불가시 간단한 결합
        fallback_result = self.create_simple_summary(comments)
        print(f"DEBUG: 대체 요약 사용: {fallback_result}")
        return fallback_result
    
    def summarize_single_content(self, comment: str) -> str:
        """단일 comment 요약"""
        if OPENAI_AVAILABLE and client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 경험이 풍부한 조직 개발 전문가입니다. 주어진 업무 메모를 분석하여 요약해주세요."
                        },
                        {
                            "role": "user",
                            "content": f"다음 업무 메모를 5-6줄로 요약해주세요:\n\n{comment}"
                        }
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                return response.choices[0].message.content.strip() if response.choices[0].message.content else comment
                
            except Exception as e:
                print(f"단일 요약 생성 오류: {e}")
        
        return comment
    
    def create_simple_summary(self, comments: List[str]) -> str:
        """OpenAI 사용 불가시 간단한 요약"""
        total_comments = len(comments)
        
        # 각 comment의 첫 문장들을 추출
        key_points = []
        for i, comment in enumerate(comments[:5]):  # 최대 5개만 처리
            sentences = comment.split('.')
            if sentences and sentences[0].strip():
                key_points.append(f"{i+1}. {sentences[0].strip()}")
        
        summary = f"총 {total_comments}개의 업무 메모를 분석한 결과:\n"
        summary += "\n".join(key_points)
        
        if total_comments > 5:
            summary += f"\n...그 외 {total_comments - 5}개의 추가 메모가 있습니다."
        
        return summary
    
    def process_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph 노드로 사용되는 메인 처리 함수"""
        try:
            # state에서 user_id 추출 (없으면 None)
            user_id = state.get('user_id')
            
            # 리포트 생성
            report = self.create_report_summary(user_id)
            
            # state 업데이트
            state['report_summary'] = report
            state['status'] = 'completed'
            state['timestamp'] = datetime.now().isoformat()
            
            return state
            
        except Exception as e:
            print(f"리포트 생성 오류: {e}")
            state['error'] = str(e)
            state['status'] = 'failed'
            return state

# LangGraph에서 사용할 노드 함수
def report_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph 노드 함수"""
    agent = ReportAgent()
    return agent.process_node(state)

# 테스트 함수
def test_report_agent():
    """리포트 에이전트 테스트"""
    # print("=== 리포트 에이전트 테스트 시작 ===")
    
    agent = ReportAgent()

    # print("\n사용자 1의 리포트 생성 테스트...")
    test_state_user = {
        'user_id': '1',
        'task': 'generate_report'
    }
    result_user = agent.process_node(test_state_user)
    print(f"사용자 1 결과: {result_user['status']}")
    if 'report_summary' in result_user and result_user['status'] == 'completed':
        report = result_user['report_summary']
        print(f"메모 수: {report['total_memos']}")
        print(f"통합 요약: {report['combined_summary']}")
        

    elif 'error' in result_user:
        print(f"오류 발생: {result_user['error']}")
    else:
        print("예상치 못한 결과:", result_user)
    
    print("\n=== 테스트 완료 ===")
    return result_user



# langGraph 테스트


# 상태 정의
class GraphState(TypedDict):
    user_input: str
    user_id: str
    messages: list
    next_action: str
    report_summary: Dict[str, Any]
    status: str
    response: str

# 라우팅 함수 - 입력에 따라 다음 노드 결정
def route_input(state: GraphState) -> Literal["report_node", "general_node"]:
    """사용자 입력에 따라 노드 선택"""
    user_input = state.get("user_input", "").lower()
    
    # 보고서 관련 키워드 체크
    report_keywords = ["보고서", "리포트", "report", "요약", "summary", "평가"]
    
    for keyword in report_keywords:
        if keyword in user_input:
            return "report_node"
    
    return "general_node"

# 노드 A: 보고서 작성 노드
def report_node(state: GraphState) -> GraphState:
    """보고서 작성 노드 - report_agent 사용"""
    # print("보고서 작성 노드 실행 중...")
    
    # report_agent_node 호출
    report_state = {
        'user_id': state.get('user_id', '1'),
        'task': 'generate_report'
    }
    
    result = report_agent_node(report_state)
    
    # 상태 업데이트
    state['report_summary'] = result.get('report_summary', {})
    state['status'] = result.get('status', 'completed')
    state['response'] = f"✅ 사용자 {state.get('user_id', '1')}의 보고서가 생성되었습니다."
    
    if 'report_summary' in result:
        report = result['report_summary']
        state['response'] += f"\n📋 총 메모 수: {report.get('total_memos', 0)}"
        state['response'] += f"\n📝 통합 요약: {report.get('combined_summary', '')}"
    
    return state

# 노드 B: 일반 응답 노드
def general_node(state: GraphState) -> GraphState:
    """일반 응답 노드"""
    print("💬 일반 응답 노드 실행 중...")
    state['response'] = "일반적인 질문에 대한 응답입니다."
    state['status'] = 'completed'
    return state

# 그래프 생성
def create_simple_graph():
    """간단한 LangGraph 그래프 생성"""
    
    # 그래프 초기화
    workflow = StateGraph(GraphState)
    
    # 노드 추가
    workflow.add_node("report_node", report_node)      # 노드 A: 보고서 작성
    workflow.add_node("general_node", general_node)    # 노드 B: 일반 응답
    
    # 시작점에서 조건부 분기
    workflow.set_conditional_entry_point(
        route_input,
        {
            "report_node": "report_node",
            "general_node": "general_node"
        }
    )
    
    # 종료점 설정
    workflow.add_edge("report_node", END)
    workflow.add_edge("general_node", END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app

# 테스트 함수
def test_langgraph(input_query):
    """LangGraph 테스트"""
    print("=== LangGraph 테스트 시작 ===")
    USER_ID = "1"  # 기본값
    
    # 그래프 생성
    app = create_simple_graph()

    if OPENAI_AVAILABLE and client:
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
                        - "user1의 보고서를 작성해줘" → "user1"
                        - "1번 사용자의 보고서를 작성해줘" → "1"
                        
                        만약 명확한 대상이 없다면 "1"이라고 응답하세요."""
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
                USER_ID = response.choices[0].message.content.strip()
                
                # 추가 검증: 만약 응답이 너무 길거나 이상하면 기본값 사용
                if len(USER_ID) > 100 or "보고서" in USER_ID:
                    USER_ID = "1"
                    
        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            USER_ID = "1"  # 기본값
    else:
        # OpenAI 사용 불가시 정규표현식으로 간단한 파싱
        import re
        
        # "XXX의 보고서" 패턴 매칭
        pattern = r'([^의\s]+)의\s*보고서'
        match = re.search(pattern, input_query)
        
        if match:
            USER_ID = match.group(1)
        else:
            USER_ID = "1"

    print(f"추출된 USER_ID: {USER_ID}")
    
    # 테스트 케이스 생성
    test_case = {
        "user_input": input_query,
        "user_id": USER_ID,
        "messages": [],
        "next_action": "",
        "report_summary": {},
        "status": "",
        "response": ""
    }
    
    print(f"입력: '{test_case['user_input']}'")
    
    # 그래프 실행
    result = app.invoke(test_case)
    
    print(f"상태: {result['status']}")
    print(f"응답: {result['response']}")
    
    if result.get('report_summary'):
        print(f"보고서 생성됨: ✅")
    else:
        print(f"보고서 생성됨: ❌")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    # 테스트 실행
    test_langgraph("3의 보고서를 작성해줘")
