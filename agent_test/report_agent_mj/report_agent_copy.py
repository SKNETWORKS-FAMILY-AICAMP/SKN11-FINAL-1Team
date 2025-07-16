import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# LLM 초기화
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o",
    openai_api_key=openai_api_key
)

@dataclass
class TaskInfo:
    """과제 정보를 담는 데이터 클래스"""
    task_id: int
    title: str
    guide: str
    date: str
    content: str
    mentor_name: str
    subtasks: List[Dict]
    task_memos: List[Dict]
    task_reviews: List[Dict]

@dataclass
class ComprehensiveReportData:
    """전체 리포트 생성을 위한 데이터 클래스"""
    user_name: str
    user_role: str
    all_tasks: List[TaskInfo]
    overall_stats: Dict

class ReportAgent:
    """종합 리포트 생성 에이전트"""
    
    def __init__(self, db_path: str = "report_agent_test.db"):
        self.db_path = db_path
        self.llm = llm
    
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 생성"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    def get_user_tasks(self, user_id: int) -> List[Tuple[int, str]]:
        """사용자의 과제 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT t.task_id, t.title
                FROM task t
                JOIN task_assign ta ON t.task_id = ta.task_id
                WHERE ta.mentee_id = ? OR ta.mentor_id = ?
                ORDER BY t.task_id
            """, (user_id, user_id))
            
            return [(row['task_id'], row['title']) for row in cursor.fetchall()]
    
    def fetch_single_task_data(self, task_id: int) -> Optional[TaskInfo]:
        """단일 과제 데이터 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 기본 과제 정보 조회
            cursor.execute("""
                SELECT t.*, u_mentee.name as mentee_name, u_mentor.name as mentor_name
                FROM task t
                JOIN task_assign ta ON t.task_id = ta.task_id
                JOIN user u_mentee ON ta.mentee_id = u_mentee.user_id
                JOIN user u_mentor ON ta.mentor_id = u_mentor.user_id
                WHERE t.task_id = ?
            """, (task_id,))
            
            task_row = cursor.fetchone()
            if not task_row:
                return None
            
            # 하위 과제 정보 조회
            cursor.execute("""
                SELECT s.*, 
                       GROUP_CONCAT(DISTINCT m.content) as memo_contents,
                       GROUP_CONCAT(DISTINCT r.content) as review_contents,
                       AVG(r.score) as avg_score
                FROM subtask s
                LEFT JOIN memo m ON s.subtask_id = m.subtask_id
                LEFT JOIN review r ON s.subtask_id = r.subtask_id
                WHERE s.task_id = ?
                GROUP BY s.subtask_id
                ORDER BY s.subtask_id
            """, (task_id,))
            
            subtasks = []
            for row in cursor.fetchall():
                # memo_contents와 review_contents가 None일 수 있으므로 안전하게 처리
                memo_contents = row['memo_contents'] if row['memo_contents'] else ""
                review_contents = row['review_contents'] if row['review_contents'] else ""
                
                subtask = {
                    'subtask_id': row['subtask_id'],
                    'title': row['title'],
                    'guide': row['guide'],
                    'date': row['date'],
                    'content': row['content'] if row['content'] else "",
                    'memos': memo_contents.split(',') if memo_contents else [],
                    'reviews': review_contents.split(',') if review_contents else [],
                    'score': row['avg_score'] if row['avg_score'] else 0
                }
                subtasks.append(subtask)
            
            # 상위 과제 메모 조회
            cursor.execute("""
                SELECT content, create_date
                FROM memo
                WHERE task_id = ? AND subtask_id IS NULL
                ORDER BY create_date
            """, (task_id,))
            
            task_memos = [{'content': row['content'], 'date': row['create_date']} 
                         for row in cursor.fetchall()]
            
            # 상위 과제 리뷰 조회
            cursor.execute("""
                SELECT content, score, summary, generated_by, create_date
                FROM review
                WHERE task_id = ? AND subtask_id IS NULL
                ORDER BY create_date
            """, (task_id,))
            
            task_reviews = [{'content': row['content'], 'score': row['score'], 
                           'summary': row['summary'], 'generated_by': row['generated_by'],
                           'date': row['create_date']} for row in cursor.fetchall()]
            
            return TaskInfo(
                task_id=task_row['task_id'],
                title=task_row['title'],
                guide=task_row['guide'] if task_row['guide'] else "",
                date=task_row['date'],
                content=task_row['content'] if task_row['content'] else "",
                mentor_name=task_row['mentor_name'],
                subtasks=subtasks,
                task_memos=task_memos,
                task_reviews=task_reviews
            )
    
    def fetch_comprehensive_data(self, user_id: int) -> Optional[ComprehensiveReportData]:
        """사용자의 전체 과제 데이터 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 사용자 정보 조회
            cursor.execute("SELECT name, role FROM user WHERE user_id = ?", (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return None
            
            # 사용자의 모든 과제 조회
            task_list = self.get_user_tasks(user_id)
            all_tasks = []
            
            total_tasks = len(task_list)
            total_subtasks = 0
            completed_subtasks = 0
            total_scores = []
            subtask_scores = []
            
            for task_id, _ in task_list:
                task_info = self.fetch_single_task_data(task_id)
                if task_info:
                    all_tasks.append(task_info)
                    
                    # 통계 계산
                    total_subtasks += len(task_info.subtasks)
                    completed_subtasks += len([s for s in task_info.subtasks if s['content'].strip()])
                    
                    # 상위 과제 점수 수집
                    for review in task_info.task_reviews:
                        if review['score'] is not None:
                            total_scores.append(review['score'])
                    
                    # 하위 과제 점수 수집
                    for subtask in task_info.subtasks:
                        if subtask['score'] and subtask['score'] > 0:
                            subtask_scores.append(subtask['score'])
            
            # 전체 통계 계산
            all_scores = total_scores + subtask_scores
            overall_stats = {
                'total_tasks': total_tasks,
                'total_subtasks': total_subtasks,
                'completed_subtasks': completed_subtasks,
                'completion_rate': (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0,
                'average_score': sum(all_scores) / len(all_scores) if all_scores else 0,
                'task_scores': total_scores,
                'subtask_scores': subtask_scores,
                'total_evaluations': len(all_scores)
            }
            
            return ComprehensiveReportData(
                user_name=user_row['name'],
                user_role=user_row['role'],
                all_tasks=all_tasks,
                overall_stats=overall_stats
            )
    
    def generate_comprehensive_report_prompt(self, report_data: ComprehensiveReportData) -> str:
        """전체 종합 리포트 생성을 위한 프롬프트 생성 (과제 개수 많을 경우)"""
        prompt = f"""
다음은 "{report_data.user_name}" 학습자의 전체 학습 기록에 대한 데이터입니다.
이 정보를 바탕으로 전반적인 패턴과 대표 사례를 중심으로 종합 리포트를 작성해주세요.

=== 학습자 기본 정보 ===
- 이름: {report_data.user_name} ({report_data.user_role})
- 총 상위 과제 수: {report_data.overall_stats['total_tasks']}개
- 총 하위 과제 수: {report_data.overall_stats['total_subtasks']}개
- 완료된 하위 과제 수: {report_data.overall_stats['completed_subtasks']}개
- 하위 과제 완료율: {report_data.overall_stats['completion_rate']:.1f}%
- 전체 평균 점수: {report_data.overall_stats['average_score']:.1f}점 ({report_data.overall_stats['total_evaluations']}개 평가 기준)

=== 점수 분포 ===
- 상위 과제 점수 목록: {report_data.overall_stats['task_scores']}
- 하위 과제 점수 목록: {report_data.overall_stats['subtask_scores']}

=== 참고 데이터: 일부 대표 과제 ===
"""
        # 대표 과제 3개만 요약
        for i, task in enumerate(report_data.all_tasks[:3], 1):
            task_score = next((review['score'] for review in task.task_reviews if review['score'] is not None), "N/A")
            guide_summary = task.guide[:100] + '...' if len(task.guide) > 100 else task.guide
            
            prompt += f"""
[과제 {i}] {task.title} - 점수: {task_score}
- 멘토: {task.mentor_name}
- 날짜: {task.date}
- 가이드 요약: {guide_summary}
- 주요 메모 개수: {len(task.task_memos)}, 리뷰 개수: {len(task.task_reviews)}
"""

        prompt += """

=== 리포트 작성 요청 ===
다음과 같은 구조의 종합 리포트를 작성해주세요:

1. **전체 학습 여정 종합 분석**
   - 다양한 과제를 통해 습득한 주요 기술/지식
   - 학습 흐름 속에서 나타나는 성숙도 및 역량 향상 패턴
   - 초기 대비 변화된 학습 태도와 실력

2. **우수 성취 및 강점 요약**
   - 일관되게 강점으로 나타난 부분
   - 대표 과제나 제출물에서 확인 가능한 탁월한 역량
   - 긍정적인 변화나 성과를 보여준 사례

3. **개선이 필요한 영역**
   - 반복적으로 관찰되는 약점이나 어려움
   - 낮은 점수나 미완료율에서 유추되는 학습 이슈
   - 보완이 필요한 학습 접근 방식이나 습관

4. **종합 평가 및 제안**
   - 학습자의 전반적인 학습 성향 및 발전 가능성
   - 현재 수준에서의 평가 요약
   - 향후 추천 학습 전략 및 커리어 방향 제안

※ 주의사항:
- 모든 과제를 하나하나 평가하기보다, **공통된 패턴**과 **대표적인 사례**를 중심으로 분석해주세요.
- 피드백은 학습자의 노력을 인정하고 **격려하는 어조**로 작성하며, **구체적인 근거와 함께 건설적인 제안**을 포함해주세요.
"""
        return prompt
    
    def generate_comprehensive_report(self, user_id: int) -> Optional[str]:
        """전체 종합 리포트 생성 메인 함수"""
        print(f"사용자 {user_id}의 전체 학습 데이터 조회 중...")
        
        # 전체 데이터 조회
        report_data = self.fetch_comprehensive_data(user_id)
        if not report_data:
            print("사용자 데이터를 찾을 수 없습니다.")
            return None
        
        print(f"총 {len(report_data.all_tasks)}개 과제 데이터 로드 완료")
        print(f"전체 완료율: {report_data.overall_stats['completion_rate']:.1f}%")
        print(f"평균 점수: {report_data.overall_stats['average_score']:.1f}점")
        
        # 프롬프트 생성
        prompt = self.generate_comprehensive_report_prompt(report_data)
        
        print("AI 종합 리포트 생성 중...")
        
        # LLM을 통한 종합 리포트 생성
        messages = [
            SystemMessage(content="""당신은 학습자의 전체 학습 과정을 분석하고 종합적인 피드백을 제공하는 교육 전문가입니다. 
            모든 상위 과제와 하위 과제의 내용을 면밀히 분석하여 학습자의 성장 과정을 정확히 파악하고, 
            구체적이고 실용적인 피드백을 제공해주세요."""),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"리포트 생성 중 오류 발생: {e}")
            return None
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """사용자 통계 정보 조회"""
        report_data = self.fetch_comprehensive_data(user_id)
        if not report_data:
            return None
        
        return {
            'user_name': report_data.user_name,
            'user_role': report_data.user_role,
            'stats': report_data.overall_stats,
            'task_count': len(report_data.all_tasks)
        }

# 사용 예시
def main():
    """메인 실행 함수"""
    try:
        agent = ReportAgent()
        
        # 사용자 ID 입력
        user_id = 1
        
        print(f"=== 사용자 {user_id} 학습 현황 종합 리포트 생성 ===\n")
        
        # 사용자 통계 먼저 확인
        stats = agent.get_user_stats(user_id)
        if stats:
            print(f"학습자: {stats['user_name']} ({stats['user_role']})")
            print(f"총 과제 수: {stats['task_count']}개")
            print(f"완료율: {stats['stats']['completion_rate']:.1f}%")
            print(f"평균 점수: {stats['stats']['average_score']:.1f}점")
            print(f"총 평가 수: {stats['stats']['total_evaluations']}개\n")
        else:
            print("사용자 통계를 조회할 수 없습니다.")
            return
        
        # 종합 리포트 생성
        comprehensive_report = agent.generate_comprehensive_report(user_id)
        
        if comprehensive_report:
            print("=== 종합 학습 리포트 ===\n")
            print(comprehensive_report)
            
            # 리포트를 파일로 저장 (선택사항)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{user_id}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"=== {stats['user_name']} 학습자 종합 리포트 ===\n")
                    f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(comprehensive_report)
                print(f"\n리포트가 '{filename}' 파일로 저장되었습니다.")
            except Exception as e:
                print(f"파일 저장 중 오류 발생: {e}")
        else:
            print("종합 리포트 생성에 실패했습니다.")
            
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()