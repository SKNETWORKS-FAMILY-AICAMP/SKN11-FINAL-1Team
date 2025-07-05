from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.hashers import check_password
from core.models import User
from django.contrib.auth import authenticate

def user_add_modify(request):
    return render(request, 'account/user_add_modify.html')

def change_pwd(request):
    return render(request, 'account/change_pwd.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                login(request, user)  # Django 세션 기반 인증 적용
                # 역할에 따라 리다이렉트
                if user.role == 'admin':
                    return redirect('account:supervisor')
                elif user.role == 'mentor':
                    return redirect('/common/mentor/')
                elif user.role == 'mentee':
                    return redirect('/common/mentee/')
                else:
                    return redirect('/')
            else:
                messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        except User.DoesNotExist:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        return render(request, 'account/login.html')
    return render(request, 'account/login.html')

def profile(request):
    return render(request, 'account/profile.html')

def supervisor(request):
    return render(request, 'account/supervisor.html')

# Create your views here.
