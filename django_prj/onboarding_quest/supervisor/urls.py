from django.urls import path
from .views import admin_dashboard, user_create, user_edit, user_delete
from . import views


urlpatterns = [
    # 관리자 페이지
   path('', views.admin_dashboard, name='admin_dashboard'), 
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),#기본
    path('dashboard/department/<int:department_id>/', views.admin_dashboard, name='admin_dashboard_filtered'),
    path('<int:department_id>/', views.admin_dashboard, 
    name='admin_dashboard'),  # 부서 필터용
    path('department/add/', views.department_create, name='department_create'),
    path('department/<int:department_id>/delete/', views.department_delete, name='department_delete'),

    #사원 생성, 삭제, 수정
    path('user/add/', user_create, name='user_create'),
    path('user/<int:user_id>/edit/', user_edit, name='user_edit'),
    path('user/<int:user_id>/delete/', user_delete, name='user_delete'),
    path('user/<int:pk>/update/', views.user_update_view, name='user_update'),
    path('user/<int:pk>/delete/', views.user_delete_view, name='user_delete'),


]
