from django.urls import path
from .views import login_view, logout_view, home_view, password_change, user_edit_view
from . import views

urlpatterns = [
    #로그인/로그아웃/비밀번호 변경
    path('', login_view),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-change/', password_change, name='password_change'),
    path('profile/edit/', user_edit_view, name='profile_edit'),
    path('home/', home_view, name='home'),

]