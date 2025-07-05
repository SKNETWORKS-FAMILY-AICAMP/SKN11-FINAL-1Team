from django.core.management.base import BaseCommand
from core.models import User, Department, Company
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = '샘플 사용자 데이터를 데이터베이스에 채웁니다.'

    def handle(self, *args, **options):
        self.stdout.write('샘플 사용자 데이터를 채우는 중...')

        # 더미 회사와 부서가 없으면 생성합니다.
        company, created = Company.objects.get_or_create(
            company_id='123-45-67890',
            defaults={'company_name': '샘플 회사'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('샘플 회사 생성 완료'))

        department, created = Department.objects.get_or_create(
            department_name='샘플 부서',
            defaults={'company': company, 'description': '샘플 사용자를 위한 부서'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('샘플 부서 생성 완료'))

        # 모든 사용자의 비밀번호는 '123'으로 통일합니다.
        common_password = '123'

        # Mentee 사용자 5명 생성
        for i in range(1, 6):
            username = f'mentee{i}'
            email = f'mentee{i}@example.com'
            user_data = {
                'email': email,
                'password': common_password,
                'job_part': '개발',
                'position': 1,
                'role': 'mentee',
                'department': department,
                'mentorship': None, # mentorship는 빈 값으로 설정
            }
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'password': make_password(user_data.pop('password')),
                    **user_data
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'사용자 생성 완료: {username}'))
            else:
                self.stdout.write(self.style.WARNING(f'사용자가 이미 존재합니다: {username}'))

        # Mentor 사용자 5명 생성
        for i in range(1, 6):
            username = f'mentor{i}'
            email = f'mentor{i}@example.com'
            user_data = {
                'email': email,
                'password': common_password,
                'job_part': '관리',
                'position': 2,
                'role': 'mentor',
                'department': department,
                'mentorship': None, # mentorship는 빈 값으로 설정
            }
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'password': make_password(user_data.pop('password')),
                    **user_data
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'사용자 생성 완료: {username}'))
            else:
                self.stdout.write(self.style.WARNING(f'사용자가 이미 존재합니다: {username}'))

        # 관리자 사용자 1명 생성
        admin_username = 'adminuser'
        admin_email = 'admin@example.com'
        admin_user_data = {
            'email': admin_email,
            'password': common_password,
            'is_staff': False,
            'is_superuser': False,
            'job_part': '관리자',
            'position': 0,
            'role': 'admin', # 관리자도 역할은 지정
            'department': department,
            'mentorship': None, # mentorship는 빈 값으로 설정
        }
        admin_user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'password': make_password(admin_user_data.pop('password')),
                **admin_user_data
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'관리자 사용자 생성 완료: {admin_username}'))
        else:
            self.stdout.write(self.style.WARNING(f'관리자 사용자가 이미 존재합니다: {admin_username}'))

        self.stdout.write(self.style.SUCCESS('샘플 사용자 데이터 채우기 완료.'))
