from django.core.management.base import BaseCommand
from core.models import (
    Company, Department, User, Mentorship, Curriculum, TaskManage,
    TaskAssign, Memo, ChatSession, ChatMessage, Docs
)
from django.contrib.auth.hashers import make_password
from datetime import date, timedelta, datetime
from django.utils import timezone
from random import sample, randint
import random
from random import randint


class Command(BaseCommand):

    def handle(self, *args, **options):

        self.stdout.write('샘플 데이터 생성 시작...')

        # 1. 회사 1개 (EZFLOW)
        self.stdout.write('1. 회사 생성...')
        company, _ = Company.objects.get_or_create(
            company_id='123-45-67890',
            defaults={'company_name': 'EZFLOW'}
        )

        # 2. 부서 4개 (LLM 개발, 영업, HR, 마케팅)
        self.stdout.write('2. 부서 4개 생성...')
        departments = {}
        for dept_name in ['LLM 개발', '영업', 'HR', '마케팅']:
            dept, _ = Department.objects.get_or_create(
                department_name=dept_name,
                company=company,
                defaults={'description': f'{dept_name} 부서'}
            )
            departments[dept_name] = dept

        # 3. HR팀 관리자 1명
        self.stdout.write('3. HR팀 관리자 1명 생성...')
        import random
        tag_pool_admin = [
            '#관리자', '#HR', '#온보딩', '#리더', '#조직문화', '#소통', '#혁신', '#책임감', '#전략', '#성장', '#팀워크'
        ]
        admin_tags = ' '.join(random.sample(tag_pool_admin, 3))
        
        # 기존 HR 관리자 확인
        if not User.objects.filter(employee_number=1000).exists():
            admin_user = User.objects.create_user(
                email='hr_admin@ezflow.com',  # HR 구분
                password='123',  # 비밀번호 통일
                first_name='정호',
                last_name='이',  # 실제 한국 이름으로 변경
                employee_number=1000,
                is_admin=True,
                is_staff=True,
                company=company,
                department=departments['HR'],
                role='mentor',
                position='HR팀장',
                job_part='HR',
                tag=admin_tags,
            )
            self.stdout.write('   ✅ HR 관리자 생성 완료')
        else:
            admin_user = User.objects.get(employee_number=1000)
            self.stdout.write('   ℹ️ HR 관리자가 이미 존재합니다')

        # 4. 부서별 멘티 2명, 멘토 8명
        self.stdout.write('4. 부서별 멘티 2명, 멘토 8명 생성...')
        users_by_dept = {k: {'mentors': [], 'mentees': []} for k in departments}
        emp_num = 1001
        
        # 실제 한국 이름 목록
        korean_names = [
            ('김', '민수'), ('이', '영지'), ('박', '근호'), ('최', '지현'), ('정', '현우'),
            ('강', '수진'), ('조', '동훈'), ('윤', '소영'), ('장', '준호'), ('임', '혜진'),
            ('오', '태윤'), ('한', '미영'), ('신', '재현'), ('서', '은혜'), ('권', '성민'),
            ('노', '다영'), ('송', '우진'), ('안', '시우'), ('홍', '예린'), ('문', '건우'),
            ('양', '나영'), ('백', '도현'), ('허', '수아'), ('남', '민재'), ('심', '유진'),
            ('고', '지우'), ('유', '하준'), ('전', '서현'), ('류', '민호'), ('구', '아름'),
            ('변', '준영'), ('엄', '지수'), ('원', '태현'), ('이', '소민'), ('차', '동현'),
            ('주', '예지'), ('명', '현수'), ('배', '서윤'), ('도', '민규'), ('진', '하영'),
            ('마', '준석'), ('석', '예은'), ('선', '민찬'), ('설', '지민'), ('길', '서준'),
            ('연', '채원'), ('방', '시현'), ('표', '도윤'), ('범', '하은'), ('변', '준우')
        ]
        
        tag_pool_mentee = [
            '#성장', '#도전', '#학습', '#열정', '#협업', '#창의', '#긍정', '#노력', '#초보', '#신입', '#온보딩', '#멘티', '#호기심', '#목표', '#발전'
        ]
        tag_pool_mentor = [
            '#리더십', '#경험', '#전문가', '#멘토', '#가이드', '#피드백', '#지원', '#성장', '#책임', '#동기부여', '#온보딩', '#코칭', '#모범', '#팀워크', '#비전'
        ]
        for dept_idx, (dept_name, dept) in enumerate(departments.items()):
            self.stdout.write(f'  - {dept_name}팀 멘티/멘토 생성')
            # 부서별 prefix
            if dept_name == 'LLM 개발':
                email_prefix = 'dev'
            elif dept_name == '영업':
                email_prefix = 'sale'
            elif dept_name == '마케팅':
                email_prefix = 'mkt'
            else:
                email_prefix = 'hr'
            # 멘티 2명
            for i in range(2):
                mentee_email = f'{email_prefix}_mentee{i+1}@ezflow.com'
                # 이메일 중복 체크
                if not User.objects.filter(email=mentee_email).exists():
                    # 실제 한국 이름 사용
                    last_name, first_name = korean_names[(dept_idx*2 + i) % len(korean_names)]
                    mentee_tags = [f'#{dept_name}', '#멘티'] + random.sample(tag_pool_mentee, 2)
                    mentee = User.objects.create_user(
                        email=mentee_email,
                        password='123',
                        first_name=first_name,
                        last_name=last_name,
                        employee_number=emp_num,
                        is_admin=False,
                        is_staff=False,
                        company=company,
                        department=dept,
                        role='mentee',
                        position=f'{dept_name}사원',
                        job_part=dept_name,
                        tag=' '.join(mentee_tags),
                    )
                    users_by_dept[dept_name]['mentees'].append(mentee)
                else:
                    # 이미 존재하는 멘티 가져오기
                    mentee = User.objects.get(email=mentee_email)
                    users_by_dept[dept_name]['mentees'].append(mentee)
                emp_num += 1
            # 멘토 8명
            for i in range(8):
                mentor_email = f'{email_prefix}_mentor{i+1}@ezflow.com'
                # 이메일 중복 체크
                if not User.objects.filter(email=mentor_email).exists():
                    # 실제 한국 이름 사용
                    last_name, first_name = korean_names[(dept_idx*8 + i + 8) % len(korean_names)]  # +8로 멘티와 다른 이름 사용
                    mentor_tags = [f'#{dept_name}', '#멘토'] + random.sample(tag_pool_mentor, 2)
                    mentor = User.objects.create_user(
                        email=mentor_email,
                        password='123',
                        first_name=first_name,
                        last_name=last_name,
                        employee_number=emp_num,
                        is_admin=False,
                        is_staff=False,
                        company=company,
                        department=dept,
                        role='mentor',
                        position=f'{dept_name}선임',
                        job_part=dept_name,
                        tag=' '.join(mentor_tags),
                    )
                    users_by_dept[dept_name]['mentors'].append(mentor)
                else:
                    # 이미 존재하는 멘토 가져오기
                    mentor = User.objects.get(email=mentor_email)
                    users_by_dept[dept_name]['mentors'].append(mentor)
                emp_num += 1

        # 7. Docs (공통, LLM 개발, 영업, 마케팅)
        self.stdout.write('7. 부서별 문서(Docs) 생성...')
        Docs.objects.get_or_create(
            department=departments['HR'],
            title='사내규정',
            defaults={
                'description': '회사 공통 사내규정',
                'file_path': '/docs/common.pdf',
                'common_doc': True
            }
        )
        Docs.objects.get_or_create(
            department=departments['LLM 개발'],
            title='LLM 개발 가이드',
            defaults={
                'description': 'LLM 개발팀용 AI 모델 개발 가이드',
                'file_path': '/docs/llm_dev_guide.pdf',
                'common_doc': False
            }
        )
        Docs.objects.get_or_create(
            department=departments['영업'],
            title='고객사 관리 문서',
            defaults={
                'description': '영업팀 고객사 관리 문서',
                'file_path': '/docs/sales_client.pdf',
                'common_doc': False
            }
        )
        Docs.objects.get_or_create(
            department=departments['마케팅'],
            title='마케팅 캠페인 가이드',
            defaults={
                'description': '마케팅팀 캠페인 기획 및 실행 가이드',
                'file_path': '/docs/marketing_guide.pdf',
                'common_doc': False
            }
        )


        # 8. 멘토쉽의 멘티 직무에 맞는 Curriculum 및 TaskManage 샘플 생성
        self.stdout.write('8. 공용/부서별 온보딩 커리큘럼(Curriculum) 및 세부 Task(TaskManage) 생성...')
        curriculum_data = [
            {
                'title': '조직문화 적응하기',
                'desc': '신입사원을 위한 회사 조직문화 및 기본 소양 온보딩',
                'common': True,
                'department': None,
                'week_schedule': '1주차: 회사 소개 및 조직 구조 이해\n2주차: 사내 규정 및 동료 소개\n3주차: 커뮤니케이션 채널 가입 및 사내 이벤트\n4주차: 복지제도 및 FAQ 안내\n5주차: 사내 시설 투어 및 보안교육\n6주차: 시스템 계정 발급 및 입사서류 제출\n7주차: 멘토/멘티 매칭 및 온보딩 피드백 제출',
                'tasks': [
                    (1, '사내 조직도 열람', '회사 조직구성 파악'),
                    (1, '오리엔테이션 시청', '회사 소개 영상 시청'),
                    (2, '사내 규정 숙지', '근태, 복장, 보안 등 규정 확인'),
                    (2, '동료 소개받기', '부서 동료 및 타부서 주요 인물 소개'),
                    (3, '사내 커뮤니케이션 채널 가입', '메신저, 그룹웨어 등 가입'),
                    (4, '사내 이벤트 참여', '사내 행사, 동호회 등 참여'),
                    (5, '사내 복지제도 안내', '복지제도 및 지원제도 확인'),
                    (6, '사내 FAQ 확인', '자주 묻는 질문 확인'),
                    (7, '사내 시설 투어', '사무실, 회의실, 휴게공간 등 투어'),
                    (8, '보안교육 이수', '정보보안, 개인정보보호 교육'),
                    (9, '사내 시스템 계정 발급', '메일, 인트라넷 등 계정 발급'),
                    (10, '입사서류 제출', '입사 관련 서류 제출'),
                    (11, '멘토/멘티 매칭', '멘토링 프로그램 안내 및 매칭'),
                    (12, '온보딩 피드백 제출', '온보딩 과정 소감 및 개선의견 제출'),
                ]
            },
            {
                'title': 'LLM 개발부서 온보딩',
                'desc': 'LLM 개발팀 신입사원을 위한 AI 모델 개발 온보딩',
                'common': False,
                'department': 'LLM 개발',
                'week_schedule': '1주차: Python/PyTorch 환경 세팅 및 LLM 기초 이론\n2주차: 데이터셋 처리 및 전처리 실습\n3주차: 모델 훈련 및 파인튜닝 실습\n4주차: 모델 평가 및 벤치마크 테스트\n5주차: 모델 배포 및 API 서빙 실습\n6주차: MLOps 파이프라인 구축 및 성장계획 수립',
                'tasks': [
                    (1, 'Python/PyTorch 환경 세팅', 'CUDA, PyTorch, Transformers 라이브러리 설치'),
                    (1, 'LLM 기초 이론 학습', 'Transformer, GPT, BERT 아키텍처 이해'),
                    (2, '데이터셋 전처리', '텍스트 데이터 토크나이징 및 전처리 실습'),
                    (2, '데이터 로더 구현', 'DataLoader 및 배치 처리 실습'),
                    (3, '모델 파인튜닝 실습', 'Pre-trained 모델 파인튜닝 실습'),
                    (3, '하이퍼파라미터 튜닝', '학습률, 배치사이즈 등 최적화'),
                    (4, '모델 평가 지표 학습', 'BLEU, ROUGE, Perplexity 등 평가'),
                    (4, '벤치마크 테스트', '표준 데이터셋으로 성능 평가'),
                    (5, '모델 배포 실습', 'FastAPI로 모델 서빙 구현'),
                    (5, 'API 최적화', '추론 속도 및 메모리 최적화'),
                    (6, 'MLOps 파이프라인 구축', 'MLflow, DVC 등 도구 활용'),
                    (6, 'LLM 개발자 성장계획 수립', '멘토와 AI 전문가 성장목표 설정'),
                ]
            },
            {
                'title': '영업팀 온보딩',
                'desc': '영업팀 신입사원을 위한 실무 온보딩',
                'common': False,
                'department': '영업',
                'week_schedule': '1주차: 고객사 DB 열람 및 영업 스크립트 학습\n2주차: 계약 프로세스 실습 및 고객 미팅 동행\n3주차: 경쟁사 분석 및 실적 보고 작성\n4주차: 프로모션 정책 이해 및 회의 참석\n5주차: 신규 고객사 발굴 및 불만 처리\n6주차: 계약서 작성 및 영업 목표 설정',
                'tasks': [
                    (1, '고객사 DB 열람', 'CRM 시스템 사용법 익히기'),
                    (1, '영업 스크립트 학습', '기본/상황별 스크립트 숙지'),
                    (2, '계약 프로세스 실습', '견적, 계약, 청구 흐름 실습'),
                    (2, '고객 미팅 동행', '선임과 미팅 동행 실습'),
                    (3, '경쟁사 분석', '경쟁사 자료 조사 및 발표'),
                    (3, '실적 보고 작성', '주간/월간 실적 보고서 작성'),
                    (4, '프로모션 정책 이해', '프로모션/이벤트 정책 숙지'),
                    (4, '영업팀 회의 참석', '정기 회의 참여 및 발표'),
                    (5, '신규 고객사 발굴', '리스트업 및 콜드콜 실습'),
                    (5, '고객 불만 처리', 'CS 프로세스 실습'),
                    (6, '계약서 양식 작성', '표준 계약서 작성 실습'),
                    (6, '영업 목표 설정', '멘토와 목표 설정 및 피드백'),
                ]
            },
            {
                'title': '인사팀 온보딩',
                'desc': 'HR팀 신입사원을 위한 실무 온보딩',
                'common': False,
                'department': 'HR',
                'week_schedule': '1주차: 인사관리 시스템 실습 및 규정 관리\n2주차: 복리후생 안내 및 평가/보상 프로세스 이해\n3주차: 교육 프로그램 운영 및 채용 프로세스 실습\n4주차: 인사발령 공지 및 회의 참석\n5주차: 사내 이벤트 기획 및 근태 기록 관리\n6주차: 퇴직 절차 안내 및 성장계획 수립',
                'tasks': [
                    (1, '인사관리 시스템 실습', '입/퇴사, 휴가, 근태 관리 실습'),
                    (1, '사내 규정 관리', '규정 개정/공지 실습'),
                    (2, '복리후생 안내', '복지제도 안내 및 질의응답'),
                    (2, '평가/보상 프로세스 이해', '평가, 연봉, 보상 흐름 숙지'),
                    (3, '교육 프로그램 운영', '사내/외 교육 기획 및 운영'),
                    (3, '채용 프로세스 실습', '공고, 서류, 면접, 입사 실습'),
                    (4, '인사발령 공지', '발령 공지 및 시스템 반영'),
                    (4, 'HR팀 회의 참석', '정기 회의 참여 및 발표'),
                    (5, '사내 이벤트 기획', '행사, 워크샵 등 기획 실습'),
                    (5, '근태 기록 관리', '근태 시스템 실습'),
                    (6, '퇴직 절차 안내', '퇴직 프로세스 실습'),
                    (6, 'HR 성장계획 수립', '멘토와 성장목표 설정'),
                ]
            },
            {
                'title': '마케팅팀 온보딩',
                'desc': '마케팅팀 신입사원을 위한 실무 온보딩',
                'common': False,
                'department': '마케팅',
                'week_schedule': '1주차: 마케팅 전략 이해 및 브랜드 가이드 숙지\n2주차: 캠페인 기획 실습 및 광고 플랫폼 교육\n3주차: 콘텐츠 제작 및 SNS 마케팅 실습\n4주차: 데이터 분석 도구 활용 및 성과 측정\n5주차: 고객 세분화 및 타겟팅 전략 수립\n6주차: 마케팅 예산 관리 및 ROI 분석',
                'tasks': [
                    (1, '마케팅 전략 이해', '회사 마케팅 전략 및 목표 파악'),
                    (1, '브랜드 가이드 숙지', '브랜드 아이덴티티 및 가이드라인 학습'),
                    (2, '캠페인 기획 실습', '마케팅 캠페인 기획안 작성'),
                    (2, '광고 플랫폼 교육', 'Google Ads, Facebook Ads 등 플랫폼 교육'),
                    (3, '콘텐츠 제작', '마케팅 콘텐츠 기획 및 제작'),
                    (3, 'SNS 마케팅 실습', '소셜미디어 마케팅 전략 및 실습'),
                    (4, '데이터 분석 도구 활용', 'GA, 마케팅 분석 툴 사용법'),
                    (4, '성과 측정', '마케팅 KPI 설정 및 성과 분석'),
                    (5, '고객 세분화', '타겟 고객 분석 및 페르소나 설정'),
                    (5, '타겟팅 전략 수립', '세그먼트별 마케팅 전략 수립'),
                    (6, '마케팅 예산 관리', '예산 배분 및 관리 방법 학습'),
                    (6, 'ROI 분석', '마케팅 투자 대비 효과 분석'),
                ]
            },
            {
                'title': '신입사원 기본 온보딩',
                'desc': '모든 신입사원이 공통으로 이수해야 하는 기본 온보딩',
                'common': True,
                'department': None,
                'week_schedule': '1주차: 입사 오리엔테이션 및 보안/윤리 교육\n2주차: 시스템 계정 세팅 및 시설 안내\n3주차: 멘토링 프로그램 안내 및 커뮤니티 가입\n4주차: 업무 매뉴얼 숙지 및 FAQ 확인\n5주차: 입사서류 제출 및 온보딩 피드백 제출\n6주차: 사내 이벤트 참여 및 기본 업무 실습',
                'tasks': [
                    (1, '입사 오리엔테이션', '회사 및 부서 소개'),
                    (1, '보안/윤리 교육', '정보보안, 윤리교육 이수'),
                    (2, '사내 시스템 계정 세팅', '메일, 그룹웨어 등 계정 세팅'),
                    (2, '사내 시설 안내', '사무실, 회의실, 복지시설 안내'),
                    (3, '멘토링 프로그램 안내', '멘토/멘티 제도 소개'),
                    (3, '사내 커뮤니티 가입', '동호회, 사내 커뮤니티 가입'),
                    (4, '업무 매뉴얼 숙지', '업무 프로세스, 매뉴얼 확인'),
                    (4, '사내 FAQ 확인', '자주 묻는 질문 확인'),
                    (5, '입사서류 제출', '입사 관련 서류 제출'),
                    (5, '온보딩 피드백 제출', '온보딩 과정 소감 및 개선의견 제출'),
                    (6, '사내 이벤트 참여', '사내 행사, 워크샵 등 참여'),
                    (6, '기본 업무 실습', '간단한 실무 과제 수행'),
                ]
            },
        ]
        dept_map = {d.department_name: d for d in Department.objects.all()}
        for c in curriculum_data:
            # 총 주차 수 계산
            total_weeks = max([t[0] for t in c['tasks']]) if c['tasks'] else 0
            # 공용 커리큘럼은 HR 부서로만 할당
            department_obj = None
            if c['department']:
                department_obj = dept_map.get(c['department'])
            elif c['common']:
                department_obj = dept_map.get('HR')
            curriculum, _ = Curriculum.objects.get_or_create(
                curriculum_title=c['title'],
                defaults={
                    'curriculum_description': c['desc'],
                    'common': c['common'],
                    'department': department_obj,
                    'total_weeks': total_weeks,
                    'week_schedule': c.get('week_schedule', None)
                }
            )
            # 주차별 세부 Task 생성 (주차별 온보딩 일정 참고)
            for idx, (week, t_title, t_desc) in enumerate(c['tasks'], start=1):
                # 주차별 온보딩 일정에서 해당 주차 설명 추출
                week_schedule = c.get('week_schedule', '')
                week_intro = None
                for line in week_schedule.split('\n'):
                    if line.startswith(f'{week}주차:'):
                        week_intro = line.split(':', 1)[1].strip()
                        break
                # 가이드라인
                guideline = None
                if '코드' in t_title or '실습' in t_title or '작성' in t_title:
                    guideline = '실제 예시를 참고하여 작성해보세요.'
                elif '숙지' in t_title or '확인' in t_title:
                    guideline = '관련 문서를 꼼꼼히 읽고 이해하세요.'
                elif '참여' in t_title or '회의' in t_title:
                    guideline = '팀원과 적극적으로 소통하세요.'
                elif '제출' in t_title:
                    guideline = '마감일을 준수하세요.'
                elif '이해' in t_title or '학습' in t_title:
                    guideline = '핵심 개념을 정리해보세요.'
                # 과제 기간: 일 단위(랜덤 3~7일)
                period = randint(1, 7)
                # 우선순위: 랜덤(상/중/하)
                priority = random.choice(['상', '중', '하'])
                # 세부 Task 설명에 주차별 온보딩 일정 내용 추가
                task_desc = t_desc
                if week_intro:
                    task_desc = f'[{week_intro}] {t_desc}'
                TaskManage.objects.get_or_create(
                    curriculum_id=curriculum,
                    title=t_title,
                    week=week,
                    defaults={
                        'description': task_desc,
                        'guideline': guideline,
                        'order': idx,
                        'period': period,  # 일 단위 정수
                        'priority': priority
                    }
                )

        # 9. ChatSession별 ChatMessage 샘플 생성 (직무별 3~5개, 내용 다르게)
        self.stdout.write('9. ChatSession/ChatMessage 샘플 생성...')
        job_message_samples = {
            'LLM 개발': [
                'PyTorch 설치가 안 되는데 어떻게 해야 하나요?',
                'Transformer 모델 구조가 이해가 안 가요.',
                'CUDA 메모리 부족 오류가 나는데 해결 방법이 있나요?',
                '데이터셋 전처리는 어떻게 하나요?',
                '모델 파인튜닝 시 학습률은 어떻게 설정하나요?',
                'BLEU 점수는 어떻게 계산하나요?',
                '모델 배포는 어떻게 하나요?',
                'MLOps 파이프라인은 어떻게 구축하나요?',
                'GPU 사용량을 최적화하려면 어떻게 해야 하나요?',
                'Hugging Face 모델을 어떻게 사용하나요?',
                'LLM 평가 지표에는 어떤 것들이 있나요?',
                'LoRA 파인튜닝은 어떻게 하나요?'
            ],
            '영업': [
                '고객사 DB는 어디서 관리하나요?',
                '영업 스크립트 예시가 있을까요?',
                '계약 프로세스가 궁금합니다.',
                '고객사 미팅 준비는 어떻게 하나요?',
                '영업 목표 설정 방법이 궁금해요.',
                '신규 고객사 발굴 방법이 있나요?',
                '경쟁사 분석 자료는 어디서 볼 수 있나요?',
                '실적 보고는 어떻게 하나요?',
                '영업팀 회의 일정은 어떻게 확인하나요?',
                '고객 불만 처리 프로세스가 궁금합니다.',
                '프로모션 정책 안내 부탁드립니다.',
                '계약서 양식은 어디 있나요?'
            ],
            'HR': [
                '인사관리 시스템은 어디서 접속하나요?',
                '휴가 신청 절차가 궁금합니다.',
                '사내 규정은 어디서 확인할 수 있나요?',
                '평가 기준이 어떻게 되나요?',
                '복리후생 안내 부탁드립니다.',
                '연봉 협상은 언제 진행되나요?',
                '교육 프로그램 일정은 어떻게 확인하나요?',
                '재택근무 정책이 궁금합니다.',
                '퇴직 절차 안내 부탁드립니다.',
                '사내 이벤트 일정은 어디서 확인하나요?',
                '인사 발령 공지는 어디서 확인하나요?',
                '근태 기록은 어떻게 확인하나요?'
            ],
            '마케팅': [
                '마케팅 캠페인 기획은 어떻게 하나요?',
                '브랜드 가이드라인은 어디서 확인하나요?',
                'SNS 마케팅 전략이 궁금합니다.',
                '광고 예산은 어떻게 배정되나요?',
                '타겟 고객 분석 방법을 알려주세요.',
                '콘텐츠 제작 가이드가 있나요?',
                '마케팅 성과는 어떻게 측정하나요?',
                '경쟁사 마케팅 분석 자료가 있나요?',
                '마케팅 회의 일정은 어떻게 확인하나요?',
                '고객 피드백은 어디서 확인하나요?',
                'A/B 테스트는 어떻게 진행하나요?',
                '마케팅 도구 사용법이 궁금합니다.'
            ]
        }
        job_chatbot_answers = {
            'LLM 개발': [
                'PyTorch는 CUDA 버전을 확인하여 맞는 버전을 설치해주세요. 사내 개발환경 가이드를 참고하세요.',
                'Transformer는 Attention 메커니즘 기반 모델입니다. 사내 AI 교육자료를 참고해 주세요.',
                'CUDA 메모리 부족시 배치사이즈를 줄이거나 gradient_checkpointing을 사용해보세요.',
                '데이터셋 전처리는 토크나이저를 사용하며, 팀 가이드 문서에 예제가 있습니다.',
                '모델 파인튜닝시 일반적으로 1e-5 ~ 5e-5 학습률을 사용합니다. 실험을 통해 최적값을 찾으세요.',
                'BLEU 점수는 sacrebleu 라이브러리를 사용하여 계산할 수 있습니다.',
                '모델 배포는 FastAPI나 TorchServe를 사용합니다. 배포 가이드를 참고하세요.',
                'MLOps는 MLflow와 DVC를 사용합니다. 파이프라인 구축 문서를 확인해주세요.',
                'GPU 최적화는 mixed precision과 gradient accumulation을 활용하세요.',
                'Hugging Face는 transformers 라이브러리를 통해 사용할 수 있습니다.',
                'LLM 평가에는 BLEU, ROUGE, Perplexity, BERTScore 등이 있습니다.',
                'LoRA는 PEFT 라이브러리를 사용하여 효율적인 파인튜닝이 가능합니다.'
            ],
            '영업': [
                '고객사 DB는 CRM 시스템에서 관리합니다. 접근 권한은 영업팀장에게 문의하세요.',
                '영업 스크립트 예시는 사내 자료실에서 다운로드 가능합니다.',
                '계약 프로세스는 영업 매뉴얼 3장을 참고해 주세요.',
                '고객사 미팅 준비 체크리스트는 팀 공유 폴더에 있습니다.',
                '영업 목표는 분기별로 설정하며, 팀장과 상의해 주세요.',
                '신규 고객사 발굴은 영업팀 내부 교육 자료를 참고해 주세요.',
                '경쟁사 분석 자료는 전략기획팀에서 제공합니다.',
                '실적 보고는 매주 금요일까지 시스템에 입력해 주세요.',
                '영업팀 회의 일정은 구글 캘린더에서 확인 가능합니다.',
                '고객 불만 처리는 CS팀과 협업하여 진행합니다.',
                '프로모션 정책은 마케팅팀 공지사항을 참고해 주세요.',
                '계약서 양식은 사내 문서함에 있습니다.'
            ],
            'HR': [
                '인사관리 시스템은 인트라넷에서 접속 가능합니다.',
                '휴가 신청은 인사관리 시스템에서 온라인으로 가능합니다.',
                '사내 규정은 HR팀 공유 폴더 또는 인트라넷에서 확인할 수 있습니다.',
                '평가 기준은 연 2회 공지되며, HR팀에 문의해 주세요.',
                '복리후생 안내 자료는 인트라넷 공지사항을 참고해 주세요.',
                '연봉 협상은 연초에 진행되며, 일정은 HR팀에서 공지합니다.',
                '교육 프로그램 일정은 사내 교육 포털에서 확인 가능합니다.',
                '재택근무 정책은 인트라넷 정책 게시판을 참고해 주세요.',
                '퇴직 절차는 HR팀에 문의하시면 안내해 드립니다.',
                '사내 이벤트 일정은 사내 캘린더에서 확인할 수 있습니다.',
                '인사 발령 공지는 인트라넷 공지사항에 게시됩니다.',
                '근태 기록은 인사관리 시스템에서 확인 가능합니다.'
            ],
            '마케팅': [
                '마케팅 캠페인 기획은 마케팅팀 템플릿을 참고해 주세요.',
                '브랜드 가이드라인은 마케팅팀 공유 폴더에서 확인할 수 있습니다.',
                'SNS 마케팅 전략은 마케팅 매뉴얼 4장을 참고해 주세요.',
                '광고 예산 배정은 분기별 마케팅 계획에 따라 결정됩니다.',
                '타겟 고객 분석은 마케팅 분석 도구와 고객 데이터를 활용해 주세요.',
                '콘텐츠 제작 가이드는 브랜드 가이드라인 내에 포함되어 있습니다.',
                '마케팅 성과는 KPI 대시보드에서 실시간으로 확인할 수 있습니다.',
                '경쟁사 마케팅 분석 자료는 전략기획팀에서 제공합니다.',
                '마케팅 회의 일정은 팀 캘린더에서 확인 가능합니다.',
                '고객 피드백은 CRM 시스템과 소셜미디어 모니터링 툴에서 확인하세요.',
                'A/B 테스트는 마케팅 분석 플랫폼을 활용해 진행합니다.',
                '마케팅 도구 사용법은 온보딩 교육과 사내 매뉴얼을 참고해 주세요.'
            ]
        }

        for dept_name, dept in departments.items():
            all_users = users_by_dept[dept_name]['mentors'] + users_by_dept[dept_name]['mentees']
            for user in all_users:
                num_sessions = randint(3, 5)
                for s in range(num_sessions):
                    chat_session = ChatSession.objects.create(user=user)
                    job_part = getattr(user, 'job_part', dept_name)
                    msg_pool = job_message_samples.get(job_part, job_message_samples[dept_name])
                    ans_pool = job_chatbot_answers.get(job_part, job_chatbot_answers[dept_name])
                    num_msgs = randint(5, 8)
                    idxs = sample(range(len(msg_pool)), num_msgs)
                    user_msgs = [msg_pool[i] for i in idxs]
                    bot_msgs = [ans_pool[i] for i in idxs]
                    summary_set = False
                    for i in range(num_msgs):
                        user_msg = ChatMessage.objects.create(
                            session=chat_session,
                            message_type='user',
                            message_text=user_msgs[i]
                        )
                        if not summary_set:
                            chat_session.summary = user_msgs[i]
                            chat_session.save()
                            summary_set = True
                        ChatMessage.objects.create(
                            session=chat_session,
                            message_type='chatbot',
                            message_text=bot_msgs[i]
                        )

        # 10. 멘토쉽 샘플 데이터 생성
        self.stdout.write('10. 멘토쉽 샘플 데이터 생성...')
        
        # 멘토와 멘티 사용자 조회
        mentors = list(User.objects.filter(role='mentor'))
        mentees = list(User.objects.filter(role='mentee'))
        curriculums = list(Curriculum.objects.all())
        
        if not mentors or not mentees or not curriculums:
            self.stdout.write(self.style.ERROR('멘토/멘티/커리큘럼 데이터가 부족합니다.'))
        else:
            mentorships = []
            mentee_idx = 0
            
            # 멘토 3명을 사용하여 총 9개의 멘토쉽 생성 (멘토 1명당 3명의 멘티)
            for i, mentor in enumerate(mentors[:3]):
                for j in range(3):
                    if mentee_idx >= len(mentees):
                        break
                    
                    mentee = mentees[mentee_idx]
                    
                    # 날짜 설정 - 첫 번째 멘토쉽은 종료일이 지난 비활성화
                    if i == 0 and j == 0:
                        # 2025-07-16 기준으로 종료일이 지난 비활성화 멘토쉽
                        start_date = date(2024, 6, 1)
                        end_date = date(2024, 12, 31)  # 이미 종료된 날짜
                        is_active = False
                    else:
                        # 활성화된 멘토쉽들
                        start_date = date(2025, 7, 1)
                        end_date = date(2025, 12, 31)  # 아직 종료되지 않은 날짜
                        is_active = True
                    
                    # 커리큘럼 할당 (순환 방식)
                    curriculum = curriculums[(i * 3 + j) % len(curriculums)]
                    
                    # 멘토쉽 생성
                    mentorship = Mentorship.objects.create(
                        mentor_id=mentor.user_id,
                        mentee_id=mentee.user_id,
                        start_date=start_date,
                        end_date=end_date,
                        is_active=is_active,
                        curriculum_title=curriculum.curriculum_title,
                        total_weeks=curriculum.total_weeks
                    )
                    mentorships.append(mentorship)
                    
                    # 해당 커리큘럼의 TaskManage를 기반으로 TaskAssign 생성
                    task_manages = TaskManage.objects.filter(curriculum_id=curriculum).order_by('week', 'order')
                    for task_manage in task_manages:
                        # 예정 시작일/종료일 계산 (멘토쉽 시작일 기준으로 주차별 계산)
                        week_offset = (task_manage.week - 1) * 7  # 주차별 7일 간격
                        scheduled_start = start_date + timedelta(days=week_offset)
                        scheduled_end = scheduled_start + timedelta(days=task_manage.period or 7)
                        
                        # TaskAssign 생성
                        task_assign = TaskAssign.objects.create(
                            mentorship_id=mentorship,
                            title=task_manage.title,
                            description=task_manage.description,
                            guideline=task_manage.guideline,
                            week=task_manage.week,
                            order=task_manage.order,
                            scheduled_start_date=scheduled_start,
                            scheduled_end_date=scheduled_end,
                            status='진행전',
                            priority=task_manage.priority
                        )
                        
                        # 상위 TaskAssign에 대한 하위 태스크 생성 (1~3개)
                        num_subtasks = randint(1, 3)
                        subtask_templates = {
                            'Python/PyTorch 환경 세팅': ['CUDA 드라이버 설치', 'PyTorch 설치', 'Transformers 라이브러리 설치'],
                            'LLM 기초 이론 학습': ['논문 읽기', '아키텍처 이해', '실습 예제 수행'],
                            '데이터셋 전처리': ['데이터 수집', '토크나이징', '배치 처리'],
                            '모델 파인튜닝 실습': ['모델 로드', '학습 설정', '파인튜닝 실행'],
                            '모델 평가 지표 학습': ['평가 스크립트 작성', '지표 계산', '결과 분석'],
                            '모델 배포 실습': ['API 서버 구축', '모델 로드', '추론 테스트'],
                            '고객사 DB 열람': ['CRM 접속', '고객 정보 확인', '데이터 분석'],
                            '영업 스크립트 학습': ['기본 스크립트 암기', '상황별 대응법', '롤플레잉 연습'],
                            '인사관리 시스템 실습': ['시스템 접속', '기능별 실습', '테스트 데이터 입력'],
                            '사내 조직도 열람': ['조직구조 파악', '부서별 역할', '핵심 인물 확인'],
                            '오리엔테이션 시청': ['영상 시청', '내용 정리', '질의응답'],
                            '사내 규정 숙지': ['규정집 읽기', '핵심 내용 정리', '확인 테스트'],
                            '입사 오리엔테이션': ['회사 소개 듣기', '부서 소개 듣기', '동료 인사']
                        }
                        
                        # 기본 하위 태스크 템플릿
                        default_subtasks = ['계획 수립', '실행', '완료 보고']
                        
                        # 해당 태스크에 맞는 하위 태스크 선택
                        available_subtasks = subtask_templates.get(task_manage.title, default_subtasks)
                        selected_subtasks = random.sample(available_subtasks, min(num_subtasks, len(available_subtasks)))
                        
                        for idx, subtask_title in enumerate(selected_subtasks):
                            subtask_start = scheduled_start + timedelta(days=idx)
                            subtask_end = subtask_start + timedelta(days=1)
                            
                            TaskAssign.objects.create(
                                parent=task_assign,
                                mentorship_id=mentorship,
                                title=f"{task_manage.title} - {subtask_title}",
                                description=f"{task_manage.title}의 세부 단계: {subtask_title}",
                                week=task_manage.week,
                                order=idx + 1,
                                scheduled_start_date=subtask_start,
                                scheduled_end_date=subtask_end,
                                status='진행전',
                                priority=task_manage.priority
                            )
                        
                        # TaskAssign에 대한 멘토-멘티 댓글(Memo) 생성 (2~3개)
                        num_memos = randint(2, 3)
                        
                        # 부서별 맞춤형 멘토-멘티 댓글 템플릿
                        dept_specific_templates = {
                            'LLM 개발': {
                                'mentor': [
                                    "PyTorch 환경 세팅이 잘 되셨나요? CUDA 버전 확인이 중요합니다.",
                                    "Transformer 모델 구조 이해가 어려우시면 Attention 메커니즘부터 차근차근 공부해보세요.",
                                    "데이터셋 전처리 시 토크나이징이 핵심입니다. 예제 코드를 참고해보세요.",
                                    "파인튜닝할 때 학습률을 1e-5부터 시작해보시고 점진적으로 조정해보세요.",
                                    "BLEU 점수 계산은 sacrebleu 라이브러리 사용하시면 됩니다. 궁금하면 언제든 물어보세요.",
                                    "모델 배포 시 FastAPI를 활용하면 효율적입니다. 참고 자료 공유드릴게요.",
                                    "GPU 메모리 최적화가 중요해요. gradient_checkpointing을 활용해보세요."
                                ],
                                'mentee': [
                                    "PyTorch 설치가 계속 오류가 나는데 도움을 받을 수 있을까요?",
                                    "Transformer 논문을 읽어봤는데 Multi-Head Attention 부분이 이해가 안 가요.",
                                    "데이터 전처리 과정에서 토크나이저 사용법이 궁금합니다.",
                                    "파인튜닝 실습 중 CUDA out of memory 오류가 발생했습니다.",
                                    "모델 평가 지표들의 차이점을 알고 싶어요.",
                                    "배포한 모델의 추론 속도가 너무 느린 것 같아요.",
                                    "Hugging Face 모델을 로드하는 방법을 알려주세요."
                                ]
                            },
                            '영업': {
                                'mentor': [
                                    "CRM 시스템 사용법 익히셨나요? 고객 관리의 핵심입니다.",
                                    "영업 스크립트는 상황별로 다르게 적용하시는 게 중요해요.",
                                    "미팅 준비할 때 고객사 배경 조사를 충분히 해보세요.",
                                    "실적 보고서 작성 시 수치와 함께 분석도 포함해주세요.",
                                    "경쟁사 분석은 우리 제품의 차별점을 부각시키는 방향으로 해보세요.",
                                    "신규 고객 발굴 시 타겟팅이 중요합니다. 함께 전략을 세워봐요.",
                                    "계약서 검토 시 주요 조항들을 꼼꼼히 확인해주세요."
                                ],
                                'mentee': [
                                    "CRM에서 고객 정보를 어떻게 효율적으로 관리하나요?",
                                    "첫 영업 미팅에서 어떤 점을 주의해야 할까요?",
                                    "고객 불만 처리 시 어떤 절차를 따라야 하나요?",
                                    "경쟁사 대비 우리 제품의 강점을 어떻게 어필해야 할까요?",
                                    "영업 목표 달성을 위한 전략이 궁금해요.",
                                    "계약 협상 시 유의할 점이 있나요?",
                                    "실적 보고서 양식을 확인하고 싶습니다."
                                ]
                            },
                            'HR': {
                                'mentor': [
                                    "인사관리 시스템의 각 기능들을 차근차근 익혀보세요.",
                                    "채용 프로세스는 공정성과 객관성이 가장 중요합니다.",
                                    "직원 상담 시 경청하는 자세가 중요해요.",
                                    "노무관리는 법적 근거를 정확히 파악하는 게 필요합니다.",
                                    "복리후생 제도 안내 시 직원들이 이해하기 쉽게 설명해주세요.",
                                    "평가 제도 운영 시 공정성과 투명성을 유지해야 합니다.",
                                    "교육 프로그램 기획 시 직원들의 니즈를 파악하는 게 중요해요."
                                ],
                                'mentee': [
                                    "인사시스템에서 휴가 승인 처리는 어떻게 하나요?",
                                    "면접 진행 시 질문해서는 안 되는 내용이 있나요?",
                                    "퇴직금 계산 방법을 알려주세요.",
                                    "근로기준법 관련해서 궁금한 점이 있어요.",
                                    "직원 교육 프로그램을 어떻게 기획해야 할까요?",
                                    "성과평가 기준을 어떻게 설정하나요?",
                                    "사내 이벤트 예산 관리는 어떻게 하나요?"
                                ]
                            },
                            '마케팅': {
                                'mentor': [
                                    "브랜드 가이드라인을 숙지하시고 일관성 있게 적용해보세요.",
                                    "타겟 고객 분석이 캠페인 성공의 핵심입니다.",
                                    "SNS 마케팅은 각 플랫폼별 특성을 이해하는 게 중요해요.",
                                    "콘텐츠 제작 시 브랜드 톤앤매너를 유지해주세요.",
                                    "마케팅 KPI 설정 시 측정 가능한 지표를 선택하세요.",
                                    "A/B 테스트를 통해 최적의 전략을 찾아가세요.",
                                    "경쟁사 마케팅 분석으로 인사이트를 얻어보세요."
                                ],
                                'mentee': [
                                    "브랜드 아이덴티티를 어떻게 콘텐츠에 반영하나요?",
                                    "타겟 페르소나 설정 방법이 궁금해요.",
                                    "Instagram과 Facebook 마케팅 전략의 차이점은?",
                                    "캠페인 성과 측정 도구 사용법을 알려주세요.",
                                    "광고 예산 배분을 어떻게 해야 효율적일까요?",
                                    "고객 피드백을 마케팅에 어떻게 활용하나요?",
                                    "마케팅 자동화 툴 추천해 주세요."
                                ]
                            }
                        }
                        
                        # 기본 템플릿 (부서별 템플릿이 없는 경우)
                        default_templates = {
                            'mentor': [
                                "안녕하세요! 이 과제에 대해 궁금한 점이 있으면 언제든 말씀해 주세요.",
                                "진행하시면서 어려운 부분이 있으면 바로 연락 주시기 바랍니다.",
                                "좋은 진전이 있으신 것 같네요! 계속 화이팅하세요.",
                                "이 부분은 실무에서 매우 중요한 내용이니 꼼꼼히 학습해 주세요.",
                                "혹시 참고할 만한 자료가 필요하시면 말씀해 주세요.",
                                "과제 진행 상황을 중간중간 공유해 주시면 도움이 될 것 같습니다."
                            ],
                            'mentee': [
                                "안녕하세요! 과제를 시작했는데 이 부분이 잘 이해가 안 가네요.",
                                "진행 중인데 예상보다 시간이 많이 걸리고 있습니다.",
                                "과제 완료했습니다! 검토 부탁드립니다.",
                                "이 부분에 대해 추가 설명을 들을 수 있을까요?",
                                "관련 자료를 더 찾아볼 필요가 있을 것 같습니다.",
                                "다음 단계로 진행해도 될까요?"
                            ]
                        }
                        
                        # 멘토와 멘티의 부서 확인
                        mentor_dept = mentor.department.department_name if mentor.department else None
                        mentee_dept = mentee.department.department_name if mentee.department else None
                        
                        # 부서별 템플릿 선택 (멘토 부서 우선, 없으면 멘티 부서, 둘 다 없으면 기본 템플릿)
                        dept_name = mentor_dept or mentee_dept
                        memo_templates = dept_specific_templates.get(dept_name, default_templates)
                        
                        for memo_idx in range(num_memos):
                            # 멘토/멘티 교대로 댓글 작성
                            if memo_idx % 2 == 0:
                                # 멘토가 먼저 댓글
                                user = mentor
                                comment = random.choice(memo_templates['mentor'])
                            else:
                                # 멘티가 응답
                                user = mentee
                                comment = random.choice(memo_templates['mentee'])
                            
                            # 댓글 생성일을 과제 시작일 이후로 설정 (초단위까지, timezone-aware)
                            naive_date = scheduled_start + timedelta(days=memo_idx)
                            rand_hour = randint(8, 20)  # 근무시간대 랜덤
                            rand_minute = randint(0, 59)
                            rand_second = randint(0, 59)
                            dt = datetime.combine(naive_date, datetime.min.time()).replace(hour=rand_hour, minute=rand_minute, second=rand_second)
                            aware_datetime = timezone.make_aware(dt)
                            memo = Memo.objects.create(
                                task_assign=task_assign,
                                user=user,
                                comment=comment
                            )
                            # 생성일을 수동으로 설정 (auto_now_add 때문에 직접 수정)
                            memo.create_date = aware_datetime
                            memo.save()
                    
                    mentee_idx += 1
            
            self.stdout.write(f'멘토쉽 샘플 {len(mentorships)}개 생성 완료!')
            
            # TaskAssign 및 하위 태스크, 댓글 총 개수 확인
            total_task_assigns = TaskAssign.objects.count()
            total_parent_tasks = TaskAssign.objects.filter(parent__isnull=True).count()
            total_subtasks = TaskAssign.objects.filter(parent__isnull=False).count()
            total_memos = Memo.objects.count()
            
            self.stdout.write(f'TaskAssign 총 {total_task_assigns}개 생성 완료!')
            self.stdout.write(f'  - 상위 태스크: {total_parent_tasks}개')
            self.stdout.write(f'  - 하위 태스크: {total_subtasks}개')
            self.stdout.write(f'Memo(댓글) 총 {total_memos}개 생성 완료!')

        self.stdout.write(self.style.SUCCESS('샘플 데이터 생성 완료!'))

        # 11. User별 Alarm 샘플 생성
        from core.models import Alarm
        self.stdout.write('11. User별 Alarm 샘플 생성...')
        all_users = User.objects.all()
        alarm_messages = [
            '새로운 과제가 할당되었습니다.',
            '멘토가 피드백을 남겼습니다.',
            '과제 마감일이 다가옵니다.',
            '멘토쉽이 곧 종료됩니다.',
            '새로운 공지사항이 있습니다.'
        ]
        for idx, user in enumerate(all_users):
            for i in range(3):
                msg = random.choice(alarm_messages)
                alarm = Alarm.objects.create(
                    user=user,
                    message=msg,
                    is_active=True
                )
                # 생성일을 다르게(최신순) 설정 (초단위까지, timezone-aware)
                naive_date = date.today() - timedelta(days=(idx + i))
                rand_hour = randint(8, 20)
                rand_minute = randint(0, 59)
                rand_second = randint(0, 59)
                dt = datetime.combine(naive_date, datetime.min.time()).replace(hour=rand_hour, minute=rand_minute, second=rand_second)
                aware_datetime = timezone.make_aware(dt)
                alarm.created_at = aware_datetime
                alarm.save()
        self.stdout.write(f'Alarm 샘플 {Alarm.objects.count()}개 생성 완료!')

        # 12. 멘토쉽별 종합 리포트 샘플 생성
        self.stdout.write('12. 멘토쉽별 종합 리포트 샘플 생성...')
        
        # 부서별 맞춤형 리포트 템플릿
        dept_specific_reports = {
            'LLM 개발': [
                '멘티는 PyTorch 환경 세팅과 LLM 기초 이론 학습에서 높은 이해도를 보였습니다. 데이터 전처리와 모델 파인튜닝 실습을 성실히 수행하였으며, 특히 GPU 메모리 최적화와 관련된 기술적 문제 해결 능력이 돋보입니다. AI/ML 분야의 전문가로 성장할 잠재력이 충분합니다.',
                'Transformer 아키텍처 이해와 모델 평가 지표 학습에서 우수한 성과를 보였습니다. MLOps 파이프라인 구축과 모델 배포 실습을 통해 실무 역량을 키웠으며, 자기주도적 학습 태도가 인상적입니다. 향후 LLM 개발 전문가로서 큰 성장이 기대됩니다.',
                'CUDA와 PyTorch 환경에 빠르게 적응하였으며, 파인튜닝과 모델 최적화 과제를 성실히 완료했습니다. 기술적 호기심이 높고 새로운 AI 기술 습득에 적극적입니다. 다만, 코드 최적화 부분에서 조금 더 경험을 쌓으면 좋겠습니다.',
                'LLM 개발 전반에 걸쳐 뛰어난 학습 능력을 보였습니다. 특히 BLEU, ROUGE 등 평가 지표 활용과 FastAPI를 통한 모델 서빙에서 실무적 역량을 입증했습니다. 팀 내에서의 기술 공유와 협업 태도도 우수하여 향후 AI 팀의 핵심 인재로 성장할 것으로 예상됩니다.'
            ],
            '영업': [
                '멘티는 CRM 시스템 활용과 고객사 관리에서 빠른 적응력을 보였습니다. 영업 스크립트 학습과 고객 미팅 동행을 통해 실무 감각을 키웠으며, 특히 신규 고객 발굴 과제에서 창의적인 아이디어를 제시했습니다. 영업 전문가로서의 잠재력이 높습니다.',
                '계약 프로세스 이해와 실적 보고서 작성에서 체계적인 업무 처리 능력을 보였습니다. 고객 불만 처리와 경쟁사 분석 과제를 성실히 수행하였으며, 고객 중심적 사고와 분석적 접근 방식이 돋보입니다. 영업팀의 핵심 인재로 성장할 것으로 기대됩니다.',
                '영업 목표 설정과 계약서 작성 실습에서 꼼꼼함과 정확성을 보였습니다. 고객과의 소통 능력이 우수하고 프로모션 정책 이해도 빠릅니다. 다만, 적극적인 영업 마인드를 더 키워나가면 좋겠습니다.',
                '영업 전반에 걸친 이해도가 높고 실무 적응력이 뛰어납니다. CRM 데이터 분석과 영업 전략 수립에서 논리적 사고력을 보여주었으며, 팀워크와 고객 서비스 마인드가 우수합니다. 향후 영업팀 리더로 성장할 가능성이 높습니다.'
            ],
            'HR': [
                '멘티는 인사관리 시스템 활용과 채용 프로세스 이해에서 높은 숙련도를 보였습니다. 복리후생 제도 안내와 직원 상담 과제를 통해 인사 업무의 전반적 흐름을 파악했으며, 특히 법규 준수와 공정성 확보에 대한 의식이 뛰어납니다.',
                '평가 및 보상 시스템 이해와 교육 프로그램 기획에서 창의적 아이디어를 제시했습니다. 근태 관리와 인사 발령 업무를 성실히 수행하였으며, 직원들과의 소통 능력과 문제 해결 능력이 우수합니다. HR 전문가로서 큰 성장이 기대됩니다.',
                '사내 규정 관리와 퇴직 절차 안내 업무에서 정확성과 체계성을 보였습니다. 사내 이벤트 기획 과제를 통해 조직 활성화에 대한 관심과 아이디어를 보여주었습니다. 다만, 노무 관련 법규 지식을 더 쌓아나가면 좋겠습니다.',
                'HR 업무 전반에 대한 이해도가 높고 직원 지원 마인드가 강합니다. 인사 시스템 관리와 조직문화 개선에 대한 관심이 높으며, 공정하고 투명한 인사 업무 수행 의지를 보였습니다. 향후 HR 팀의 중추적 역할을 할 것으로 예상됩니다.'
            ],
            '마케팅': [
                '멘티는 브랜드 가이드라인 숙지와 마케팅 캠페인 기획에서 창의적 사고력을 보였습니다. SNS 마케팅 실습과 콘텐츠 제작 과제를 통해 디지털 마케팅 역량을 키웠으며, 특히 타겟 고객 분석과 페르소나 설정에서 분석적 접근이 돋보입니다.',
                '마케팅 데이터 분석 도구 활용과 성과 측정에서 우수한 역량을 보였습니다. A/B 테스트 설계와 ROI 분석 과제를 성실히 수행하였으며, 데이터 기반 의사결정 능력이 뛰어납니다. 퍼포먼스 마케팅 전문가로 성장할 잠재력이 높습니다.',
                '광고 플랫폼 교육과 마케팅 예산 관리에서 체계적인 접근을 보였습니다. 고객 세분화와 타겟팅 전략 수립 과제에서 논리적 사고력을 발휘했으며, 브랜드 일관성 유지에 대한 이해도가 높습니다. 다만, 크리에이티브한 아이디어 발상을 더 키워나가면 좋겠습니다.',
                '마케팅 전략 수립부터 실행까지 전반적인 프로세스를 잘 이해하고 있습니다. 경쟁사 분석과 트렌드 파악 능력이 우수하며, 고객 피드백을 마케팅에 반영하는 역량도 뛰어납니다. 종합적인 마케팅 전문가로 성장할 것으로 기대됩니다.'
            ]
        }
        
        # 기본 리포트 템플릿 (부서가 명확하지 않은 경우)
        default_reports = [
            '멘티는 온보딩 기간 동안 적극적으로 참여하였으며, 과제 수행 능력이 우수합니다. 협업과 소통 능력이 뛰어나 향후 성장 가능성이 높습니다.',
            '과제 제출 및 피드백 반영이 성실하며, 자기주도적으로 업무를 수행하였습니다. 추가적인 실무 경험이 쌓이면 더욱 발전할 것으로 기대됩니다.',
            '업무 이해도가 높고, 새로운 환경에 빠르게 적응하였습니다. 다만, 일정 관리에 조금 더 신경 쓸 필요가 있습니다.',
            '팀원과의 협업에서 긍정적인 태도를 보였으며, 주어진 과제를 성실히 수행하였습니다. 앞으로의 성장도 기대됩니다.'
        ]
        
        mentorships = Mentorship.objects.all()
        for idx, mentorship in enumerate(mentorships):
            # 멘토 또는 멘티의 부서 정보 가져오기
            mentor = User.objects.get(user_id=mentorship.mentor_id)
            mentee = User.objects.get(user_id=mentorship.mentee_id)
            
            # 부서명 확인 (멘토 부서 우선, 없으면 멘티 부서)
            mentor_dept = mentor.department.department_name if mentor.department else None
            mentee_dept = mentee.department.department_name if mentee.department else None
            dept_name = mentor_dept or mentee_dept
            
            # 부서별 맞춤 리포트 선택
            if dept_name in dept_specific_reports:
                report_pool = dept_specific_reports[dept_name]
            else:
                report_pool = default_reports
            
            # 랜덤하게 리포트 선택
            mentorship.report = random.choice(report_pool)
            mentorship.save()
            
        self.stdout.write(f'Mentorship 리포트 샘플 {mentorships.count()}개 생성 완료!')