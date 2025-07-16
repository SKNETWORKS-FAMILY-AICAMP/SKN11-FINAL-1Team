from django.db import models
from django.core.validators import RegexValidator

# Create your models here.

class Company(models.Model):
    company_id = models.CharField(
        primary_key=True,
        max_length=12,
        validators=[
            RegexValidator(
                regex=r'^\d{3}-\d{2}-\d{5}$',
                message='사업자번호 000-00-00000.'
            )
        ]
    )
    company_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.company_name 

class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.department_name

class Mentorship(models.Model):
    mentorship_id = models.AutoField(primary_key=True)
    mentor_id = models.IntegerField()
    mentee_id = models.IntegerField()

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('mentee', 'Mentee'),
        ('mentor', 'Mentor'),
        ('admin', 'Admin'),
    )
    user_id = models.AutoField(primary_key=True)
    employee_number = models.IntegerField(null=True, blank=True, unique=True)
    is_admin = models.BooleanField(default=False)
    mentorship_id = models.IntegerField(null=True, blank=True)
    tag = models.CharField(max_length=255, null=True, blank=True)
    exp = models.IntegerField(default=0)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    join_date = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=50, null=True, blank=True)
    job_part = models.CharField(max_length=50, null=True, blank=True)
    company_id = models.CharField(max_length=12, null=True, blank=True)
    department_id = models.IntegerField(null=True, blank=True)
    
    # 필수 필드들
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # 기본 사용자명 필드를 email로 설정
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'core_user'

    def __str__(self):
        return self.email

class ChatSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    summary = models.CharField(max_length=255, null=True, blank=True)

class ChatMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_type = models.CharField(max_length=50, null=True, blank=True)
    message_text = models.CharField(max_length=1000, null=True, blank=True)
    create_time = models.DateField(auto_now_add=True, null=True, blank=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)

class Docs(models.Model):
    docs_id = models.AutoField(primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    file_path = models.CharField(max_length=255)
    create_time = models.DateTimeField(auto_now_add=True)
    common_doc = models.BooleanField(default=False)

class Template(models.Model):
    template_id = models.AutoField(primary_key=True)
    template_description = models.CharField(max_length=255, null=True, blank=True)
    template_title = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

class TaskManage(models.Model):
    task_mange_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    difficulty = models.CharField(max_length=50, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    exp = models.IntegerField()
    order = models.IntegerField(null=True, blank=True)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)

class TaskAssign(models.Model):
    task_assign_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.IntegerField()
    difficulty = models.CharField(max_length=50, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    exp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Subtask(models.Model):
    subtask_id = models.AutoField(primary_key=True)
    task_assign = models.ForeignKey(TaskAssign, on_delete=models.CASCADE)

class Memo(models.Model):
    memo_id = models.AutoField(primary_key=True)
    create_date = models.DateField(auto_now_add=True, null=True, blank=True)
    comment = models.CharField(max_length=1000, null=True, blank=True)
    task_assign = models.ForeignKey(TaskAssign, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)