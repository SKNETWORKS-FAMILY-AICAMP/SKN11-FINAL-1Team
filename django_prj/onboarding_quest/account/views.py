from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import User

def login_view(request):
    """기본 Django 로그인 뷰"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                login(request, user)
                
                # 역할에 따른 리다이렉트
                if user.role == 'admin':
                    return redirect('account:supervisor')
                elif user.role == 'mentor':
                    return redirect('mentor:mentor')
                elif user.role == 'mentee':
                    return redirect('mentee:mentee')
                else:
                    return redirect('common:dashboard')
            else:
                messages.error(request, '비밀번호가 올바르지 않습니다.')
        except User.DoesNotExist:
            messages.error(request, '존재하지 않는 사용자입니다.')
    
    return render(request, 'account/login.html')

@login_required
def user_add_modify(request):
    return render(request, 'account/user_add_modify.html')

@login_required
def change_pwd(request):
    return render(request, 'account/change_pwd.html')

@login_required
def profile(request):
    return render(request, 'account/profile.html')

@login_required
def supervisor(request):
    return render(request, 'account/supervisor.html')

