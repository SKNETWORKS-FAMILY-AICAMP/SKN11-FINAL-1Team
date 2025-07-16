from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # 기존 URL들
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('doc/', views.doc, name='doc'),
    path('task_add/', views.task_add, name='task_add'),
]
