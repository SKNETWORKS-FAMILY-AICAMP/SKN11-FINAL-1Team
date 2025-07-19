from django.urls import path
from . import views

app_name = 'mentee'

urlpatterns = [
    path('', views.mentee, name='mentee'),
    path('task_list/', views.task_list, name='task_list'),
    path('task_detail/<int:task_assign_id>/', views.task_detail, name='task_detail'),
    path('task_update/<int:task_assign_id>/', views.task_update, name='task_update'),
    path('task_comment/<int:task_assign_id>/', views.task_comment, name='task_comment'),
    path('create_subtask/<int:parent_id>/', views.create_subtask, name='create_subtask'),
    path('update_task_status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('test-status-change/', views.change_task_status_for_test, name='change_task_status_for_test'),
    # 🔧 임시 디버깅 URL
    path('debug_memos/', views.debug_memos, name='debug_memos'),
    path('debug_mentorship/', views.debug_mentorship, name='debug_mentorship'),
    # 🔧 테스트 URL
    path('test_task_list/', views.test_task_list, name='test_task_list'),
]
