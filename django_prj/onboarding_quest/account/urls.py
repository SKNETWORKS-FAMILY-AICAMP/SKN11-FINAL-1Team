from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    # 관리자 페이지
    path('', views.admin_dashboard, name='admin_dashboard'), 
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),#기본
    path('dashboard/department/<int:department_id>/', views.admin_dashboard, name='admin_dashboard_filtered'),
    path('<int:department_id>/', views.admin_dashboard, name='admin_dashboard'),  # 부서 필터용
    path('department/add/', views.department_create, name='department_create'),
    path('department/<int:department_id>/delete/', views.department_delete, name='department_delete'),
    path('department/<int:department_id>/update/', views.department_update, name='department_update'),
    path('department/<int:department_id>/detail/', views.department_detail, name='department_detail'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # path('user_add_modify/', views.user_add_modify, name='user_add_modify_direct'),
    # path('change_pwd/', views.change_pwd, name='change_pwd'),
    path('profile/', views.profile, name='profile'),
    path('password_change/', views.password_change, name='password_change'),
    path('supervisor/', views.supervisor, name='supervisor'),

    #사원 생성, 삭제, 수정
    path('user/add/', views.user_create, name='user_create'),
    path('user/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('user/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('user/<int:user_id>/password_reset/', views.user_password_reset, name='password_reset'),
    path('user/<int:pk>/update/', views.user_update_view, name='user_update'),
    path('user/<int:user_id>/password_reset/', views.user_password_reset, name='password_reset'),

    # 멘토쉽 관리
    path('manage_mentorship/', views.manage_mentorship, name='manage_mentorship'),
    path('mentorship/<int:mentorship_id>/edit/', views.mentorship_edit, name='mentorship_edit'),
    path('mentorship/<int:mentorship_id>/delete/', views.mentorship_delete, name='mentorship_delete'),
    path('mentorship/<int:mentorship_id>/detail/', views.mentorship_detail, name='mentorship_detail'),
]