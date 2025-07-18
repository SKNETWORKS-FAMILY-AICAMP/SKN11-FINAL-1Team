from django.views.decorators.http import require_GET
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponseForbidden
from core.models import User, Department, Mentorship, Curriculum
from account.forms import UserForm, CustomPasswordChangeForm, UserEditForm, DepartmentForm
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Value as V
from django.db.models.functions import Concat
import json





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
                if user.is_admin:
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
    # return redirect('login')
    return redirect('account:login')
#endregion 로그인/로그아웃 





#region 관리자

@login_required
def supervisor(request):
    company = request.user.company
    departments = Department.objects.filter(company=company)
    dept_form = DepartmentForm()
    
    # 검색 및 필터링
    search_query = request.GET.get('search', '')
    selected_department_id = request.GET.get('dept')
    position_filter = request.GET.get('position', '')
    
    # 기본 사용자 쿼리
    users = User.objects.filter(company=company)
    
    # 검색 조건 적용
    if search_query:
        # 전체 이름 검색을 위한 annotate 추가
        users = users.annotate(
            full_name=Concat('last_name', 'first_name')
        ).filter(
            Q(full_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_number__icontains=search_query)
        )
    
    # 부서 필터 적용
    dept_detail = None
    if selected_department_id:
        try:
            dept_detail = Department.objects.get(department_id=selected_department_id, company=company)
            users = users.filter(department=dept_detail)
        except Department.DoesNotExist:
            pass
    
    
    return render(request, 'account/supervisor.html', {
        'departments': departments,
        'users': users,
        'dept_form': dept_form,
        'selected_department_id': int(selected_department_id) if selected_department_id else None,
        'dept_detail': dept_detail,
        'search_query': search_query,

    })

@login_required
def admin_dashboard(request, department_id=None):
    if not request.user.is_admin:
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
    if not request.user.is_admin:
        return HttpResponseForbidden("접근 권한이 없습니다.")

    users = User.objects.filter(is_active=True)
    departments = Department.objects.filter(company=request.user.company)

    return render(request, 'account/supervisor.html', {'user': request.user, 'users': users, 'departments': departments,})



#region > 부서 생성/조회/수정/삭제
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
@require_GET
def department_detail(request, department_id):
    dept = get_object_or_404(Department, pk=department_id)
    departments = Department.objects.filter(company=request.user.company)
    users = User.objects.filter(is_active=True, department=dept)
    return render(request, 'account/supervisor.html', {
        'departments': departments,
        'users': users,
        'selected_department_id': dept.department_id,
        'dept_detail': dept,
        'view_mode': request.GET.get('view', None),
    })

# 부서 수정
@login_required
def department_update(request, department_id):
    dept = get_object_or_404(Department, pk=department_id)
    departments = Department.objects.filter(company=dept.company)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            # 부서 수정 후 supervisor.html로 리다이렉트 (선택 해제)
            return redirect('account:supervisor')
    else:
        form = DepartmentForm(instance=dept)
    # GET 또는 실패 시 수정 폼 렌더링
    return render(request, 'account/supervisor.html', {
        'departments': departments,
        'dept_edit': dept,
        'dept_form': form,
        'selected_department_id': dept.department_id,
        'edit_mode': True,
    })

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
        form = UserForm(request.POST, company=request.user.company)
        if form.is_valid():
            user = form.save(commit=False)
            user.company = request.user.company
            # 비밀번호를 '123'로 고정
            user.set_password('123')
            user.save()
            return redirect('account:supervisor')
    else:
        form = UserForm(company=request.user.company)
    return render(request, 'account/user_add_modify.html', {'form': form})

# 사용자 수정
@login_required
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user, company=user.company)
        if form.is_valid():
            changed = False
            for field in form.changed_data:
                changed = True
                break
            if changed:
                form.save()
                messages.success(request, '프로필 정보가 저장되었습니다.')
            else:
                messages.info(request, '변경된 내용이 없습니다.')
            return redirect('account:user_edit', user_id=user.id)
    else:
        form = UserForm(instance=user, company=user.company)
    return render(request, 'account/profile.html', {'form': form, 'user': user})

# 사용자 삭제
@login_required
def user_delete(request, user_id):
    if not request.user.is_admin:
        return JsonResponse({'success': False, 'error': '관리자 권한이 필요합니다.'}, status=403)
        
    user = get_object_or_404(User, user_id=user_id)
    
    if user == request.user:
        return JsonResponse({'success': False, 'error': '자신의 계정은 삭제할 수 없습니다.'}, status=400)
    
    try:
        user.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('account:supervisor')
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        return redirect('account:supervisor')

# 사용자 수정
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user, company=user.company)
        if form.is_valid():
            form.save()
            return redirect('account:supervisor')
    else:
        form = UserForm(instance=user, company=user.company)
    return render(request, 'account/user_add_modify.html', {'form': form, 'edit_mode': True})

# 사용자 삭제
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('account:supervisor')
    return render(request, 'account/user_confirm_delete.html', {'user': user})

# 사용자 비밀번호 초기화
@login_required
def password_reset(request, user_id):
    """관리자가 사용자 비밀번호를 초기화하는 기능"""
    if not request.user.is_admin:
        return HttpResponseForbidden("접근 권한이 없습니다.")
    
    user = get_object_or_404(User, user_id=user_id)
    
    if request.method == 'POST':
        # 비밀번호를 '123'으로 초기화
        user.set_password('123')
        user.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'{user.get_full_name()}의 비밀번호가 초기화되었습니다.'})
        else:
            messages.success(request, f'{user.get_full_name()}의 비밀번호가 초기화되었습니다.')
            return redirect('account:supervisor')
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

#endregion > 직원 추가/수정/삭제

#endregion 관리자





#region 사용자

# 사용자 프로필 뷰 (누락된 함수 추가)
@login_required
def profile(request):
    return render(request, 'account/profile.html', {'user': request.user})

# 비밀번호 변경
@login_required
def password_change(request):
    from .forms import CustomPasswordChangeForm
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            logout(request)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': '/account/login/'})
            else:
                messages.success(request, '비밀번호가 성공적으로 변경되었습니다. 다시 로그인해 주세요.')
                return redirect('account:login')
        else:
            error_msgs = [str(e) for errs in form.errors.values() for e in errs]
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': error_msgs})
            else:
                for error in error_msgs:
                    messages.error(request, error)
                return redirect('account:profile')
    else:
        return redirect('account:profile')
# 비밀번호 변경

#endregion 사용자

#region 멘토쉽 관리

@login_required
def manage_mentorship(request):
    """멘토쉽 관리 페이지"""
    if not request.user.is_admin:
        return HttpResponseForbidden("접근 권한이 없습니다.")
    
    # 검색 및 필터링
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')
    
    # 기본 멘토쉽 쿼리
    mentorships = Mentorship.objects.all()
    
    # 모든 사용자 정보를 미리 가져오기 (성능 최적화)
    all_users = {user.user_id: user for user in User.objects.select_related('department').all()}
    
    # 검색 조건 적용
    if search_query:
        # 먼저 검색 조건에 맞는 사용자들의 ID를 찾기
        matching_users = User.objects.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        ).values_list('user_id', flat=True)
        
        mentorships = mentorships.filter(
            Q(mentor_id__in=matching_users) |
            Q(mentee_id__in=matching_users)
        )
    
    # 상태 필터 적용
    if status_filter == 'active':
        mentorships = mentorships.filter(is_active=True)
    elif status_filter == 'inactive':
        mentorships = mentorships.filter(is_active=False)
    
    # 부서 필터 적용
    if department_filter:
        # 해당 부서의 사용자들을 찾기
        dept_users = User.objects.filter(department__department_id=department_filter).values_list('user_id', flat=True)
        mentorships = mentorships.filter(
            Q(mentor_id__in=dept_users) |
            Q(mentee_id__in=dept_users)
        )
    
    # 페이지네이션
    paginator = Paginator(mentorships, 10)
    page_number = request.GET.get('page')
    mentorships = paginator.get_page(page_number)
    
    # 멘토쉽에 사용자 정보 추가
    for mentorship in mentorships:
        mentorship.mentor = all_users.get(mentorship.mentor_id)
        mentorship.mentee = all_users.get(mentorship.mentee_id)
    
    # 멘토와 멘티 목록 (모달용)
    mentors = User.objects.filter(role='mentor', is_active=True).select_related('department')
    mentees = User.objects.filter(role='mentee', is_active=True).select_related('department')
    departments = Department.objects.filter(company=request.user.company, is_active=True)
    
    # 커리큘럼 목록 가져오기
    curriculums = Curriculum.objects.all()
    
    return render(request, 'account/manage_mentorship.html', {
        'mentorships': mentorships,
        'mentors': mentors,
        'mentees': mentees,
        'departments': departments,
        'curriculums': curriculums,
        'search_query': search_query,
        'status_filter': status_filter,
        'department_filter': department_filter,
    })

@login_required
def mentorship_detail(request, mentorship_id):
    """멘토쉽 상세 정보 (AJAX)"""
    if not request.user.is_admin:
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
    
    mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
    
    data = {
        'mentor_id': mentorship.mentor_id,
        'mentee_id': mentorship.mentee_id,
        'start_date': mentorship.start_date.strftime('%Y-%m-%d') if mentorship.start_date else '',
        'end_date': mentorship.end_date.strftime('%Y-%m-%d') if mentorship.end_date else '',
        'curriculum_title': mentorship.curriculum_title,
        'is_active': mentorship.is_active,
    }
    
    return JsonResponse(data)

@login_required
def mentorship_edit(request, mentorship_id):
    """멘토쉽 수정 (AJAX)"""
    if not request.user.is_admin:
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
    
    if request.method == 'POST':
        mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
        
        try:
            data = json.loads(request.body)
            
            mentorship.mentor_id = data.get('mentor_id')
            mentorship.mentee_id = data.get('mentee_id')
            mentorship.start_date = data.get('start_date')
            mentorship.end_date = data.get('end_date')
            mentorship.curriculum_title = data.get('curriculum_title')
            mentorship.is_active = data.get('is_active') == 'true'
            
            mentorship.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

@login_required
def mentorship_delete(request, mentorship_id):
    """멘토쉽 삭제 (AJAX)"""
    if not request.user.is_admin:
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
    
    if request.method == 'POST':
        mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
        
        try:
            mentorship.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

#endregion 멘토쉽 관리


