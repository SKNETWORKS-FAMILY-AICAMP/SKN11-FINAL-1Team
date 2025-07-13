from django.core.management.base import BaseCommand
from core.models import (
    Company, Department, User, Mentorship, Template, TaskManage,
    TaskAssign, Subtask, Memo, ChatSession, ChatMessage, Docs
)
from django.contrib.auth.hashers import make_password
from datetime import date, timedelta
from random import sample, randint


class Command(BaseCommand):
    help = '샘플 사용자 데이터를 데이터베이스에 채웁니다.'

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

        # 5. 부서별 멘토쉽(멘토-멘티 1:1, 부서별 1개)
        self.stdout.write('5. 부서별 멘토쉽 생성...')
        mentorships = {}
        for dept_name, dept in departments.items():
            mentor = users_by_dept[dept_name]['mentors'][0]
            mentee = users_by_dept[dept_name]['mentees'][0]
            mentorship, _ = Mentorship.objects.get_or_create(
                mentor_id=mentor.user_id,
                mentee_id=mentee.user_id
            )
            mentorships[dept_name] = mentorship

        # 6. 템플릿 2개 (개발자 온보딩, 영업 온보딩)
        self.stdout.write('6. 템플릿(커리큘럼) 생성...')
        template_dev, _ = Template.objects.get_or_create(
            template_title='개발자 온보딩',
            department=departments['개발'],
            defaults={'template_description': '개발자 온보딩 커리큘럼'}
        )
        template_sales, _ = Template.objects.get_or_create(
            template_title='영업 온보딩',
            department=departments['영업'],
            defaults={'template_description': '영업 온보딩 커리큘럼'}
        )

        # 6-1. 템플릿별 TaskManage(커리큘럼 단계) 샘플 생성
        self.stdout.write('6-1. 템플릿별 TaskManage(커리큘럼 단계) 생성...')
        from datetime import date, timedelta
        taskmanages = {}
        taskmanages['개발'] = []
        for i, title in enumerate(['Git 사용법', 'Python 기초', 'Django 실습'], 1):
            tm, _ = TaskManage.objects.get_or_create(
                title=title,
                template=template_dev,
                defaults={
                    'start_date': date.today() + timedelta(days=i-1),
                    'end_date': date.today() + timedelta(days=i),
                    'difficulty': '중',
                    'description': f'{title} 학습',
                    'exp': 100 * i,
                    'order': i
                }
            )
            taskmanages['개발'].append(tm)
        taskmanages['영업'] = []
        for i, title in enumerate(['고객사 DB관리', '영업 스크립트 작성', '계약 프로세스'], 1):
            tm, _ = TaskManage.objects.get_or_create(
                title=title,
                template=template_sales,
                defaults={
                    'start_date': date.today() + timedelta(days=i-1),
                    'end_date': date.today() + timedelta(days=i),
                    'difficulty': '중',
                    'description': f'{title} 실습',
                    'exp': 100 * i,
                    'order': i
                }
            )
            taskmanages['영업'].append(tm)

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

        # 8. 멘토쉽의 멘티 직무에 맞는 TaskAssign 샘플 생성 (멘토-멘티 1쌍씩)
        self.stdout.write('8. 멘토쉽-멘티별 TaskAssign(실습과제) 생성...')
        for dept_name, mentorship in mentorships.items():
            mentee = users_by_dept[dept_name]['mentees'][0]
            mentor = users_by_dept[dept_name]['mentors'][0]
            # 해당 부서 템플릿의 TaskManage 목록
            tms = taskmanages.get(dept_name, [])
            for tm in tms:
                TaskAssign.objects.get_or_create(
                    title=f"{tm.title} 실습과제",
                    mentorship=mentorship,
                    user=mentee,
                    defaults={
                        'start_date': tm.start_date,
                        'end_date': tm.end_date,
                        'status': 1,
                        'difficulty': tm.difficulty,
                        'description': tm.description,
                        'exp': tm.exp,
                        'order': tm.order
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

        self.stdout.write(self.style.SUCCESS('샘플 데이터 생성 완료!'))