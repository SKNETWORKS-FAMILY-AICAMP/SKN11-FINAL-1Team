from django.contrib.auth.hashers import check_password
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponseForbidden
from core.models import User, Department
from account.forms import UserForm, CustomPasswordChangeForm, UserEditForm
import json
from django.core.serializers.json import DjangoJSONEncoder

def profile(request):
    return render(request, 'account/profile.html')

@login_required
def department_detail(request, department_id):
    dept = get_object_or_404(Department, pk=department_id)
    departments = Department.objects.all()
    users = User.objects.filter(is_active=True, department=dept)
    return render(request, 'account/supervisor.html', {
        'departments': departments,
        'users': users,
        'selected_department_id': dept.department_id,
        'dept_detail': dept,
        'view_mode': request.GET.get('view', None),
    })

@login_required
def supervisor(request):
    departments = Department.objects.all()
    dept_id = request.GET.get('dept')
    if dept_id:
        users = User.objects.filter(is_active=True, department__department_id=dept_id)
        selected_department_id = int(dept_id)
    else:
        users = User.objects.filter(is_active=True)
        selected_department_id = None

    # departments를 list of dict로 변환
    departments_json = json.dumps([
        {
            'department_id': d.department_id,
            'department_name': d.department_name,
            'description': d.description,
            'company': {'company_name': d.company.company_name if d.company else None} if hasattr(d, 'company') else None,
            'is_active': d.is_active,
        }
        for d in departments
    ], cls=DjangoJSONEncoder)

    return render(request, 'account/supervisor.html', {
        'users': users,
        'departments': departments,
        'departments_json': departments_json,
        'selected_department_id': selected_department_id,
    })



#region 로그인/로그아웃
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
                    return redirect('mentor:mentor')
                elif user.role == 'mentee':
                    return redirect('mentee:mentee')
                else:
                    return redirect('/')
            else:
                messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        except User.DoesNotExist:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        return render(request, 'account/login.html')
    return render(request, 'account/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
#endregion 로그인/로그아웃



#region 관리자

@login_required
def admin_dashboard(request, department_id=None):
    if not request.user.admin:
        return render(request, 'account/login.html')

    # 전체 부서 가져오기
    departments = Department.objects.filter(company=request.user.company)

    # 부서가 선택된 경우 해당 부서의 유저만
    if department_id:
        users = User.objects.filter(company=request.user.company, department__department_id=department_id)
        selected_department_id = int(department_id)
    else:
        users = User.objects.filter(company=request.user.company)
        selected_department_id = None

    return render(request, 'account/supervisor.html', {
        'departments': departments,
        'users': users,
        'selected_department_id': selected_department_id,
    })

@login_required
def admin_dashboard_view(request):
    if not request.user.admin:
        return HttpResponseForbidden("접근 권한이 없습니다.")

    users = User.objects.filter(is_active=True)
    departments = Department.objects.filter(company=request.user.company)

    return render(request, 'account/supervisor.html', {'user': request.user, 'users': users, 'departments': departments,})



#region > 부서 생성/삭제
@login_required
def department_create(request):
    if request.method == 'POST':
        department_name = request.POST.get('department_name')
        description = request.POST.get('description', '')
        company = request.user.company

        if department_name:
            # 🔁 1. 비활성화된 부서가 있으면 되살림
            inactive = Department.objects.filter(
                department_name=department_name,
                company=company,
                is_active=False
            ).first()

            if inactive:
                inactive.is_active = True
                inactive.description = description
                inactive.save()
                return redirect('admin_dashboard_filtered', department_id=inactive.department_id)

            # ✅ 2. 이미 존재하는 활성 부서인지 확인
            if Department.objects.filter(
                department_name=department_name,
                company=company,
                is_active=True
            ).exists():
                error = '이미 존재하는 부서명입니다.'
            else:
                # ✅ 3. 새로운 부서 생성
                department = Department.objects.create(
                    department_name=department_name,
                    description=description,
                    company=company,
                    is_active=True  # 중요
                )
                return redirect('account:supervisor')
        else:
            error = '부서명을 입력해주세요.'

        # 실패 시 다시 대시보드 렌더링
        departments = Department.objects.filter(company=company)
        users = User.objects.filter(company=company)
        selected_department_id = None

        return render(request, 'account/supervisor.html', {
            'departments': departments,
            'users': users,
            'selected_department_id': selected_department_id,
            'error': error
        })

    return redirect('admin_dashboard')

@login_required
def department_delete(request, department_id):
    department = get_object_or_404(Department, pk=department_id, company=request.user.company)
    department.delete()
    return redirect('account:supervisor')
#endregion > 부서



#region > 직원 추가/수정/삭제
# 사용자 추가
@login_required
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.company = request.user.company
            # 🔐 비밀번호 암호화
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('account:supervisor')
    else:
        form = UserForm(company=request.user.company)
    return render(request, 'account/user_add_modify.html', {'form': form})

# 사용자 수정
@login_required
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    form = UserForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect('account:supervisor')
    return render(request, 'account/profile.html', {'form': form})

# 사용자 삭제
@login_required
def user_delete(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    if request.user.admin and user != request.user:
        user.delete()
    return redirect('account:supervisor')

# 사용자 수정
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('account:supervisor')
    else:
        form = UserForm(instance=user)
    return render(request, 'account/user_add_modify.html', {'form': form})

# 사용자 삭제
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('account:supervisor')
    return render(request, 'account/user_confirm_delete.html', {'user': user})
#endregion > 직원 추가/수정/삭제

#endregion 관리자



#region 사용자
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
            return redirect('account:profile')  # 또는 너의 메인 페이지
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'account/change_pwd.html', {'form': form})
#endregion 사용자





@login_required
def user_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('account:profile')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'account/profile_edit.html', {'form': form})

@login_required
def department_update(request, department_id):
    dept = get_object_or_404(Department, pk=department_id)
    departments = Department.objects.all()
    if request.method == 'POST':
        new_name = request.POST.get('department_name')
        new_desc = request.POST.get('description', '')
        if new_name:
            dept.department_name = new_name
            dept.description = new_desc
            dept.save()
            return redirect('account:department_detail', department_id=dept.department_id)
    # GET: 수정 폼 렌더링
    return render(request, 'account/supervisor.html', {
        'departments': departments,
        'dept_edit': dept,
        'selected_department_id': dept.department_id,
        'edit_mode': True,
    })