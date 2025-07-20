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

        # 2. 부서 3개 (개발, 영업, HR)
        self.stdout.write('2. 부서 3개 생성...')
        departments = {}
        for dept_name in ['개발', '영업', 'HR']:
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
        admin_user = User.objects.create_user(
            email='hr_admin@ezflow.com',  # HR 구분
            password='123',  # 비밀번호 통일
            first_name='관리자',
            last_name='이',  # 성만 다르게
            employee_number=1000,
            is_admin=True,
            is_staff=True,
            is_superuser=True,
            company=company,
            department=departments['HR'],
            role='mentor',
            position='HR팀장',
            job_part='HR',
            tag=admin_tags,
        )

        # 4. 부서별 멘티 2명, 멘토 10명
        self.stdout.write('4. 부서별 멘티 2명, 멘토 10명 생성...')
        users_by_dept = {k: {'mentors': [], 'mentees': []} for k in departments}
        emp_num = 1001
        last_names = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권']
        tag_pool_mentee = [
            '#성장', '#도전', '#학습', '#열정', '#협업', '#창의', '#긍정', '#노력', '#초보', '#신입', '#온보딩', '#멘티', '#호기심', '#목표', '#발전'
        ]
        tag_pool_mentor = [
            '#리더십', '#경험', '#전문가', '#멘토', '#가이드', '#피드백', '#지원', '#성장', '#책임', '#동기부여', '#온보딩', '#코칭', '#모범', '#팀워크', '#비전'
        ]
        for dept_idx, (dept_name, dept) in enumerate(departments.items()):
            self.stdout.write(f'  - {dept_name}팀 멘티/멘토 생성')
            # 부서별 prefix
            if dept_name == '개발':
                email_prefix = 'dev'
            elif dept_name == '영업':
                email_prefix = 'sale'
            else:
                email_prefix = 'hr'
            # 멘티 2명
            for i in range(2):
                last_name = last_names[(dept_idx*2 + i) % len(last_names)]
                mentee_tags = [f'#{dept_name}', '#멘티'] + random.sample(tag_pool_mentee, 2)
                mentee = User.objects.create_user(
                    email=f'{email_prefix}_mentee{i+1}@ezflow.com',
                    password='123',
                    first_name='멘티',
                    last_name=last_name,
                    employee_number=emp_num,
                    is_admin=False,
                    is_staff=False,
                    is_superuser=False,
                    company=company,
                    department=dept,
                    role='mentee',
                    position=f'{dept_name}사원',
                    job_part=dept_name,
                    tag=' '.join(mentee_tags),
                )
                users_by_dept[dept_name]['mentees'].append(mentee)
                emp_num += 1
            # 멘토 10명
            for i in range(10):
                last_name = last_names[(dept_idx*10 + i) % len(last_names)]
                mentor_tags = [f'#{dept_name}', '#멘토'] + random.sample(tag_pool_mentor, 2)
                mentor = User.objects.create_user(
                    email=f'{email_prefix}_mentor{i+1}@ezflow.com',
                    password='123',
                    first_name='멘토',
                    last_name=last_name,
                    employee_number=emp_num,
                    is_admin=False,
                    is_staff=False,
                    is_superuser=False,
                    company=company,
                    department=dept,
                    role='mentor',
                    position=f'{dept_name}선임',
                    job_part=dept_name,
                    tag=' '.join(mentor_tags),
                )
                users_by_dept[dept_name]['mentors'].append(mentor)
                emp_num += 1

        # 7. Docs (공통, 개발, 영업)
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
            department=departments['개발'],
            title='프로그램 메뉴얼',
            defaults={
                'description': '개발팀용 프로그램 메뉴얼',
                'file_path': '/docs/dev_manual.pdf',
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
                'title': '개발부서 온보딩',
                'desc': '개발팀 신입사원을 위한 실무 온보딩',
                'common': False,
                'department': '개발',
                'week_schedule': '1주차: 개발환경 세팅 및 코드리뷰 참여\n2주차: 개발가이드 숙지 및 빌드/배포 실습\n3주차: API 문서 활용 및 테스트 코드 작성\n4주차: 이슈트래커 사용법 및 개발팀 회의 참석\n5주차: 신규 기능 구현 및 배포 프로세스 이해\n6주차: 기술부채 관리 및 성장계획 수립',
                'tasks': [
                    (1, '개발환경 세팅', 'IDE, Git, 패키지 설치'),
                    (1, '코드리뷰 참여하기', '팀 코드리뷰 프로세스 체험'),
                    (2, '사내 개발가이드 숙지', '코딩 컨벤션, 브랜치 전략 등'),
                    (2, '프로젝트 빌드/배포 실습', '로컬 빌드, 테스트, 배포'),
                    (3, 'API 문서 활용', 'Swagger 등 API 문서 확인'),
                    (3, '테스트 코드 작성', '단위테스트, 통합테스트 실습'),
                    (4, '이슈트래커 사용법', 'Jira, GitHub Issues 등 실습'),
                    (4, '개발팀 회의 참석', '정기/비정기 회의 참여'),
                    (5, '프로젝트 신규 기능 구현', '작은 기능 직접 구현'),
                    (5, '배포 프로세스 이해', 'CI/CD 파이프라인 체험'),
                    (6, '기술부채 관리', '리팩토링, 문서화 실습'),
                    (6, '개발자 성장계획 수립', '멘토와 성장목표 설정'),
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
            '개발': [
                '프로그램 매뉴얼을 어디서 볼 수 있나요?',
                'Git 사용법이 잘 이해가 안돼요.',
                'Django에서 모델을 추가하려면 어떻게 해야 하나요?',
                '코드 리뷰는 어떤 방식으로 진행되나요?',
                '개발 환경 세팅이 궁금합니다.',
                '테스트 코드는 어떻게 작성하나요?',
                '배포 프로세스가 궁금합니다.',
                'API 문서는 어디에 있나요?',
                '코드 컨벤션은 어떻게 되나요?',
                '신규 프로젝트 세팅 방법이 궁금해요.',
                '에러 로그는 어디서 확인하나요?',
                'CI/CD 파이프라인 설명 부탁드립니다.'
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
            ]
        }
        job_chatbot_answers = {
            '개발': [
                '프로그램 매뉴얼은 사내 위키 또는 개발팀 공유 폴더에서 확인하실 수 있습니다.',
                'Git 사용법 관련 자료는 온보딩 문서와 사내 교육 영상을 참고해 주세요.',
                'Django 모델 추가는 models.py에 클래스 정의 후 makemigrations, migrate 하시면 됩니다.',
                '코드 리뷰는 GitHub PR을 통해 진행하며, 팀원들이 코멘트를 남깁니다.',
                '개발 환경 세팅 가이드는 사내 위키에 상세히 안내되어 있습니다.',
                '테스트 코드는 pytest 예제와 사내 가이드 문서를 참고해 주세요.',
                '배포 프로세스는 Jenkins를 통해 자동화되어 있습니다.',
                'API 문서는 Swagger에서 확인 가능합니다.',
                '코드 컨벤션은 사내 개발 가이드 문서를 참고해 주세요.',
                '신규 프로젝트 세팅은 템플릿 저장소를 복제해 시작합니다.',
                '에러 로그는 Sentry와 서버 로그에서 확인할 수 있습니다.',
                'CI/CD 파이프라인은 개발팀 위키에 상세히 설명되어 있습니다.'
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
                            '개발환경 세팅': ['IDE 설치', '깃허브 연동', '패키지 설치'],
                            '코드리뷰 참여하기': ['PR 생성', '코드 수정', '리뷰 반영'],
                            '사내 개발가이드 숙지': ['가이드 문서 읽기', '예시 코드 실습', '질문 정리'],
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
                        memo_templates = {
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
        report_samples = [
            '멘티는 온보딩 기간 동안 적극적으로 참여하였으며, 과제 수행 능력이 우수합니다. 협업과 소통 능력이 뛰어나 향후 성장 가능성이 높습니다.',
            '과제 제출 및 피드백 반영이 성실하며, 자기주도적으로 업무를 수행하였습니다. 추가적인 실무 경험이 쌓이면 더욱 발전할 것으로 기대됩니다.',
            '업무 이해도가 높고, 새로운 환경에 빠르게 적응하였습니다. 다만, 일정 관리에 조금 더 신경 쓸 필요가 있습니다.',
            '팀원과의 협업에서 긍정적인 태도를 보였으며, 주어진 과제를 성실히 수행하였습니다. 앞으로의 성장도 기대됩니다.'
        ]
        mentorships = Mentorship.objects.all()
        for idx, mentorship in enumerate(mentorships):
            mentorship.report = random.choice(report_samples)
            mentorship.save()
        self.stdout.write(f'Mentorship 리포트 샘플 {mentorships.count()}개 생성 완료!')