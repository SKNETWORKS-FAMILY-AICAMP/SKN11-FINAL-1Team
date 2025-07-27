from django.contrib import admin

from .models import Company, Department, Mentorship, User, ChatSession, ChatMessage, Docs, Curriculum, TaskManage, TaskAssign, Memo
from django.contrib.auth.hashers import make_password
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

admin.site.register(Company)
admin.site.register(Department)
admin.site.register(Mentorship)

# UserAdmin 커스텀: 비밀번호 해시 저장
class UserAdmin(BaseUserAdmin):
    model = User
    # 기본 필드 표시 (원하는 대로 조정 가능)
    list_display = ('email', 'first_name', 'last_name', 'is_admin', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('개인정보', {'fields': ('first_name', 'last_name', 'employee_number', 'company', 'department', 'tag', 'role', 'join_date', 'position', 'job_part', 'profile_image')}),
        ('권한', {'fields': ('is_admin', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'employee_number', 'password1', 'password2', 'company', 'department', 'tag', 'role', 'join_date', 'position', 'job_part', 'profile_image', 'is_admin', 'is_staff', 'is_active'),
        }),
    )

    def save_model(self, request, obj, form, change):
        # 비밀번호가 평문이면 해시로 변환
        password = obj.password
        if password and not password.startswith('pbkdf2_') and not password.startswith('argon2$') and not password.startswith('bcrypt$'):
            obj.password = make_password(password)
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(Docs)
admin.site.register(Curriculum)
admin.site.register(TaskManage)
admin.site.register(TaskAssign)
admin.site.register(Memo)
