from django.urls import path
from . import views

app_name = 'mentor'

urlpatterns = [
    path('', views.mentor, name='mentor'),
    path('add_template/', views.add_template, name='mentor_add_template'),
    path('manage_mentee/', views.manage_mentee, name='manage_mentee'),
    path('manage_template/', views.manage_template, name='manage_template'),
    path('clone_template/<int:curriculum_id>/', views.clone_template, name='clone_template'),
    path('delete_template/<int:curriculum_id>/', views.delete_template, name='delete_template'),
    path('edit_template/<int:curriculum_id>/', views.edit_template, name='edit_template'),
    path('api/save_curriculum/', views.save_curriculum, name='save_curriculum'),
    # AJAX 멘티 목록
    path('mentees/', views.mentees_api, name='mentees_api'),
    # 멘티 상세정보 (view 함수 기반)
    path('mentee/<int:user_id>/', views.mentee_detail, name='mentee_detail'),
    # 멘토링 생성
    path('create_mentorship/', views.create_mentorship, name='create_mentorship'),
]
