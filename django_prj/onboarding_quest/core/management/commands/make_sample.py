from django.core.management.base import BaseCommand
from core.models import (
    Company, Department, User, Mentorship, Template, TaskManage,
    TaskAssign, Subtask, Memo, ChatSession, ChatMessage, Docs
)
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = '샘플 사용자 데이터를 데이터베이스에 채웁니다.'

    def handle(self, *args, **options):


        from datetime import date, timedelta

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

        self.stdout.write(self.style.SUCCESS('요구사항에 맞는 샘플 데이터 생성 완료!'))
