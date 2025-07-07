from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .models import User
from .forms import UserForm, CustomPasswordChangeForm, UserEditForm

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            # ✅ 관리자 여부에 따라 분기
            if user.admin:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')

    return render(request, 'users/login.html')


# 로그아웃하면 홈화면으로 옮겨지게끔 수정해야하나?
def logout_view(request):
    logout(request)
    return redirect('login')

# 임시 홈 구현 -> 여기 있는 main으로 옮겨놔야하나?
@login_required
def home_view(request):
    return render(request, 'users/main.html', {'user': request.user})

@login_required
def password_change(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']

            # db에 암호화 저장하는 것
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # 로그인 유지
            messages.success(request, '비밀번호가 성공적으로 변경되었습니다.')
            return redirect('profile_edit')  # 또는 너의 메인 페이지
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'users/password_change.html', {'form': form})


@login_required
def user_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_profile')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'users/profile_edit.html', {'form': form})

