from django.contrib import admin
<<<<<<< Updated upstream
from .models import Company, Department, Mentorship, User, ChatSession, ChatMessage, Docs, Template, TaskManage, TaskAssign, Subtask, Memo

admin.site.register(Company)
admin.site.register(Department)
admin.site.register(Mentorship)
admin.site.register(User)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(Docs)
admin.site.register(Template)
admin.site.register(TaskManage)
admin.site.register(TaskAssign)
admin.site.register(Subtask)
admin.site.register(Memo)
=======
from .models import User, Company, Department

# 기본 사용자 관리만 유지
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('last_login',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_id', 'company_name')
    search_fields = ('company_name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'company', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('department_name',)

# 나머지 모델들은 FastAPI에서 관리하므로 Django 관리자에서 제외
>>>>>>> Stashed changes
