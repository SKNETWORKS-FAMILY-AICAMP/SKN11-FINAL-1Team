from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    #로그인/로그아웃/비밀번호 변경
    path('password-change/', views.password_change, name='password_change'),
    path('profile/edit/', views.user_edit_view, name='profile_edit'),

    # 관리자 페이지
    path('', views.admin_dashboard, name='admin_dashboard'), 
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),#기본
    path('dashboard/department/<int:department_id>/', views.admin_dashboard, name='admin_dashboard_filtered'),
    path('<int:department_id>/', views.admin_dashboard, name='admin_dashboard'),  # 부서 필터용
    path('department/add/', views.department_create, name='department_create'),
    path('department/<int:department_id>/delete/', views.department_delete, name='department_delete'),






    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # path('user_add_modify/', views.user_add_modify, name='user_add_modify_direct'),
    # path('change_pwd/', views.change_pwd, name='change_pwd'),
    path('profile/', views.profile, name='profile'),
    path('supervisor/', views.supervisor, name='supervisor'),

    #사원 생성, 삭제, 수정
    path('user/add/', views.user_create, name='user_create'),
    path('user/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('user/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('user/<int:pk>/update/', views.user_update_view, name='user_update'),
    path('user/<int:pk>/delete/', views.user_delete_view, name='user_delete_view'),
]