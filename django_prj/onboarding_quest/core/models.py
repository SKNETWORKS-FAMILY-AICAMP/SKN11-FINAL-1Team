from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from datetime import date
from django.conf import settings



# 유저를 만들면 → 우리가 만든 User 모델 구조에 맞게 DB에 저장
# 우리가 만든 User 모델에서 유저를 만들 때 쓰는 도우미
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # 비밀번호 해시
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Company(models.Model):
    company_id = models.CharField(
        primary_key=True,
        max_length=12,
        validators=[
            RegexValidator(
                regex=r'^\d{3}-\d{2}-\d{5}$',
                message='사업자번호 000-00-00000.'
            )
        ],
        help_text='회사 고유 사업자번호(Primary Key)'
    )
    company_name = models.CharField(max_length=255, help_text='회사명')

    def __str__(self):
        return self.company_name 

class Department(models.Model):
    department_id = models.AutoField(primary_key=True, help_text='부서 고유 ID')
    department_name = models.CharField(max_length=50, help_text='부서명')
    description = models.CharField(max_length=255, null=True, blank=True, help_text='부서 설명')
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="departments",
        help_text='소속 회사'
    )
    is_active = models.BooleanField(default=True, help_text='부서 활성화 여부')

    class Meta:
        unique_together = ('department_name', 'company') 

    def __str__(self):
        return self.department_name
    
class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True, help_text='유저 고유 ID')
    employee_number = models.IntegerField(unique=True, null=True, blank=True, help_text='사번')
    is_admin = models.BooleanField(default=False, help_text='관리자 여부')
    mentorship_id = models.IntegerField(null=True, blank=True, help_text='멘토쉽 ID(옵션)')
    company = models.ForeignKey(  
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text='소속 회사'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        help_text='소속 부서'
    )
    tag = models.CharField(max_length=255, null=True, blank=True, help_text='유저 태그')
    ROLE_CHOICES = (
        ('mentee', 'Mentee'),
        ('mentor', 'Mentor')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text='역할(멘티/멘토)')
    join_date = models.DateField(auto_now_add=True, null=True, blank=True, help_text='입사일')
    position = models.CharField(max_length=50, help_text='직위')
    job_part = models.CharField(max_length=50, help_text='직무')
    email = models.EmailField(unique=True, help_text='이메일(로그인 ID)')
    password = models.CharField(max_length=128, help_text='비밀번호')

    last_name = models.CharField(max_length=50, help_text='성')
    first_name = models.CharField(max_length=50, help_text='이름')
    last_login = models.DateTimeField(auto_now=True, null=True, blank=True, help_text='마지막 로그인 시각')

    is_active = models.BooleanField(default=True, help_text='활성화 여부')
    is_staff = models.BooleanField(default=False, help_text='스태프 여부')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'employee_number']

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class ChatSession(models.Model):
    session_id = models.AutoField(primary_key=True, help_text='채팅 세션 고유 ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='사용자')
    summary = models.CharField(max_length=255, null=True, blank=True, help_text='세션 요약')

class ChatMessage(models.Model):
    message_id = models.AutoField(primary_key=True, help_text='메시지 고유 ID')
    MESSAGE_TYPE_CHOICES = [
        ('user', 'User'),
        ('chatbot', 'Chatbot')
    ]
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        null=False,
        blank=False,
        help_text='메시지 타입(user/chatbot)'
    )
    message_text = models.CharField(max_length=1000, null=True, blank=True, help_text='메시지 내용')
    create_time = models.DateField(auto_now_add=True, null=True, blank=True, help_text='메시지 생성일')
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, help_text='채팅 세션')

class Docs(models.Model):
    docs_id = models.AutoField(primary_key=True, help_text='문서 고유 ID')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, help_text='소속 부서')
    title = models.CharField(max_length=255, help_text='문서 제목')
    description = models.CharField(max_length=255, null=True, blank=True, help_text='문서 설명')
    file_path = models.CharField(max_length=255, help_text='파일 경로')
    create_time = models.DateTimeField(auto_now_add=True, help_text='생성일')
    common_doc = models.BooleanField(default=False, help_text='공용 문서 여부')

class Curriculum(models.Model):
    curriculum_id = models.AutoField(primary_key=True, help_text='커리큘럼 고유 ID')
    curriculum_description = models.CharField(max_length=255, null=True, blank=True, help_text='커리큘럼 설명')
    curriculum_title = models.CharField(max_length=255, help_text='커리큘럼 제목')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, help_text='소속 부서')
    common = models.BooleanField(default=False, help_text='공용 커리큘럼 여부')
    total_weeks = models.IntegerField(default=0, help_text='총 주차 수')
    week_schedule = models.TextField(null=True, blank=True, help_text='주차별 온보딩 일정(1주차: ~\n2주차: ~\n3주차: ~ 형식)')

    def __str__(self):
        return self.curriculum_title


class TaskManage(models.Model):
    task_manage_id = models.AutoField(primary_key=True, help_text='과제 관리 고유 ID')
    curriculum_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='tasks', help_text='소속 커리큘럼')
    title = models.CharField(max_length=255, help_text='과제 제목')
    description = models.CharField(max_length=255, null=True, blank=True, help_text='과제 설명')
    guideline = models.CharField(max_length=255, null=True, blank=True, help_text='과제 가이드라인')
    week = models.IntegerField(help_text='몇 주차 과제인지')
    order = models.IntegerField(null=True, blank=True, help_text='과제 순서')
    period = models.IntegerField(null=True, blank=True, help_text='과제 기간')
    PRIORITY_CHOICES = [
        ('상', '상'),
        ('중', '중'),
        ('하', '하'),
    ]
    priority = models.CharField(
        max_length=2,
        choices=PRIORITY_CHOICES,
        null=True,
        blank=True,
        help_text='과제 우선순위(상/중/하)'
    )

    def __str__(self):
        return f"{self.curriculum.curriculum_title} - {self.title} (Week {self.week})"

class Mentorship(models.Model):
    mentorship_id = models.AutoField(primary_key=True, help_text='멘토쉽 고유 ID')
    mentor_id = models.IntegerField(help_text='멘토 User ID')
    mentee_id = models.IntegerField(help_text='멘티 User ID')
    start_date = models.DateField(null=True, blank=True, help_text='시작일')
    end_date = models.DateField(null=True, blank=True, help_text='종료일')
    is_active = models.BooleanField(default=True, help_text='멘토쉽 활성화 여부')
    curriculum_title = models.CharField(max_length=255, help_text='커리큘럼 제목')
    total_weeks = models.IntegerField(default=0, help_text='총 주차 수')

class TaskAssign(models.Model):
    task_assign_id = models.AutoField(primary_key=True, help_text='과제 할당 고유 ID')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subtasks', help_text='상위 과제(TaskAssign)')
    mentorship_id = models.ForeignKey(Mentorship, on_delete=models.CASCADE, help_text='멘토쉽')
    title = models.CharField(max_length=255, null=True, blank=True, help_text='과제 할당 제목')
    description = models.CharField(max_length=255, null=True, blank=True, help_text='설명')
    guideline = models.CharField(max_length=255, null=True, blank=True, help_text='과제 가이드라인')
    week = models.IntegerField(help_text='몇 주차 과제인지')
    order = models.IntegerField(null=True, blank=True, help_text='과제 순서')
    scheduled_start_date = models.DateField(null=True, blank=True, help_text='예정 시작일')
    scheduled_end_date = models.DateField(null=True, blank=True, help_text='예정 종료일')
    real_start_date = models.DateField(null=True, blank=True, help_text='실제 시작일')
    real_end_date = models.DateField(null=True, blank=True, help_text='실제 종료일')
    STATUS_CHOICES = [
        ('진행 전', '진행 전'),
        ('진행 중', '진행 중'),
        ('검토 요청', '검토 요청'),
        ('완료', '완료'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        null=True,
        blank=True,
        help_text='과제 상태(진행 전/진행 중/검토요청/완료)'
    )
    PRIORITY_CHOICES = [
        ('상', '상'),
        ('중', '중'),
        ('하', '하'),
    ]
    priority = models.CharField(
        max_length=2,
        choices=PRIORITY_CHOICES,
        null=True,
        blank=True,
        help_text='과제 우선순위(상/중/하)'
    )
    order = models.IntegerField(null=True, blank=True, help_text='순서')

class Memo(models.Model):
    memo_id = models.AutoField(primary_key=True, help_text='메모 고유 ID')
    create_date = models.DateField(auto_now_add=True, null=True, blank=True, help_text='생성일')
    comment = models.CharField(max_length=1000, null=True, blank=True, help_text='메모 내용')
    task_assign = models.ForeignKey(TaskAssign, on_delete=models.CASCADE, help_text='과제 할당')
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='유저')