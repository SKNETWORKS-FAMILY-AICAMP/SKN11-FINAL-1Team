from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('user/add/', views.user_add_modify, name='user_add_modify'),
    path('change_pwd/', views.change_pwd, name='change_pwd'),
    path('login/', views.login_view, name='account_login'),
    path('profile/', views.profile, name='profile'),
    path('supervisor/', views.supervisor, name='supervisor'),
]