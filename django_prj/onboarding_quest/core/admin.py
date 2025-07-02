from django.contrib import admin
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
