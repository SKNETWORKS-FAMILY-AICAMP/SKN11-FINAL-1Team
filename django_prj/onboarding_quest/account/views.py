<<<<<<< Updated upstream
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.hashers import check_password
from core.models import User
from django.contrib.auth import authenticate
from django.urls import reverse

def user_add_modify(request):
    return render(request, 'account/user_add_modify.html')

def change_pwd(request):
    return render(request, 'account/change_pwd.html')

=======
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from core.models import (
    User, Department, Company, Mentorship, TaskAssign, 
    Curriculum, ChatSession, ChatMessage, Memo
)
from datetime import date, timedelta
from common.api_client import (
    call_fastapi_auth,
    call_fastapi_users,
    call_fastapi_user_stats,
    get_fastapi_client
)
import json
import logging
import requests

logger = logging.getLogger(__name__)

# 로그인/로그아웃 - 기본 인증만 유지
>>>>>>> Stashed changes
def login_view(request):
    """기본 Django 로그인 뷰"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                login(request, user)
                
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

<<<<<<< Updated upstream
def profile(request):
    return render(request, 'account/profile.html')

def supervisor(request):
    return render(request, 'account/supervisor.html')

# Create your views here.
=======
def logout_view(request):
    """로그아웃"""
    logout(request)
    return redirect('account:login')

# 프론트엔드 템플릿 렌더링 뷰들
@login_required
def supervisor(request):
    """관리자 대시보드 - 데이터베이스에서 실제 데이터 가져오기"""
    # 관리자만 접근 가능
    if not request.user.is_admin:
        messages.error(request, '관리자만 접근할 수 있습니다.')
        if request.user.role == 'mentee':
            return redirect('mentee:mentee')
        elif request.user.role == 'mentor':
            return redirect('mentor:mentor')
        else:
            return redirect('account:login')
    
    # 검색 및 필터 파라미터 처리
    search_query = request.GET.get('search', '')
    position_filter = request.GET.get('position', '')
    selected_department_id = request.GET.get('dept', '')
    
    # 부서 목록 가져오기
    departments = Department.objects.all().order_by('department_name')
    
    # 사용자 목록 가져오기
    users = User.objects.select_related('department').all()
    
    # 부서 필터링
    if selected_department_id:
        try:
            selected_department_id = int(selected_department_id)
            users = users.filter(department_id=selected_department_id)
        except (ValueError, TypeError):
            selected_department_id = None
    
    # 검색 필터링
    if search_query:
        users = users.filter(
            Q(employee_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # 직급 필터링
    if position_filter:
        users = users.filter(position=position_filter)
    
    # 직급 리스트 가져오기
    positions = User.objects.values_list('position', flat=True).distinct().order_by('position')
    
    # 선택된 부서 상세 정보
    dept_detail = None
    if selected_department_id:
        try:
            dept_detail = Department.objects.get(department_id=selected_department_id)
        except Department.DoesNotExist:
            dept_detail = None
    
    # 부서 폼 데이터 준비
    dept_form_data = {}
    if dept_detail:
        dept_form_data = {
            'department_name': dept_detail.department_name,
            'description': dept_detail.description or ''
        }
    
    context = {
        'user': request.user,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '관리자 대시보드',
        'departments': departments,
        'users': users,
        'dept_detail': dept_detail,
        'dept_form': dept_form_data,
        'positions': positions,
        'search_query': search_query,
        'position_filter': position_filter,
        'selected_department_id': selected_department_id,
    }
    return render(request, 'account/supervisor.html', context)

@login_required
def admin_dashboard(request, department_id=None):
    """관리자 대시보드 - 프론트엔드 렌더링만"""
    if not request.user.is_admin:
        return redirect('account:login')
    
    context = {
        'user': request.user,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'selected_department_id': department_id,
        'title': '관리자 대시보드'
    }
    return render(request, 'account/supervisor.html', context)

@login_required
def profile(request):
    """프로필 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 사용자의 멘토십 정보 가져오기
    mentorships = []
    if user.role == 'mentor':
        mentorships = Mentorship.objects.filter(
            mentor_id=user.user_id,
            is_active=True
        ).order_by('-start_date')
    elif user.role == 'mentee':
        mentorships = Mentorship.objects.filter(
            mentee_id=user.user_id,
            is_active=True
        ).order_by('-start_date')
    
    # 사용자의 과제 통계
    task_stats = {}
    if mentorships:
        mentorship_ids = [m.mentorship_id for m in mentorships]
        all_tasks = TaskAssign.objects.filter(mentorship_id__in=mentorship_ids)
        
        task_stats = {
            'total': all_tasks.count(),
            'todo': all_tasks.filter(status='진행 전').count(),
            'in_progress': all_tasks.filter(status='진행 중').count(),
            'review': all_tasks.filter(status='검토 요청').count(),
            'completed': all_tasks.filter(status='완료').count()
        }
    
    # 프로필 업데이트 처리
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        position = request.POST.get('position')
        job_part = request.POST.get('job_part')
        
        if first_name and last_name:
            try:
                user.first_name = first_name
                user.last_name = last_name
                if position:
                    user.position = position
                if job_part:
                    user.job_part = job_part
                user.save()
                messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
            except Exception as e:
                messages.error(request, f'프로필 업데이트 중 오류가 발생했습니다: {str(e)}')
        else:
            messages.error(request, '이름은 필수 입력 항목입니다.')
        
        return redirect('account:profile')
    
    context = {
        'user': request.user,
        'mentorships': mentorships,
        'task_stats': task_stats,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '프로필'
    }
    return render(request, 'account/profile.html', context)

@login_required
def password_change(request):
    """비밀번호 변경 페이지 - 프론트엔드 렌더링만"""
    if request.method == 'POST':
        # FastAPI로 비밀번호 변경 요청
        try:
            with get_fastapi_client() as client:
                result = client.post('/users/change-password', {
                    'user_id': request.user.user_id,
                    'old_password': request.POST.get('old_password'),
                    'new_password': request.POST.get('new_password')
                })
                messages.success(request, '비밀번호가 성공적으로 변경되었습니다.')
                return redirect('account:profile')
        except Exception as e:
            messages.error(request, f'비밀번호 변경 실패: {str(e)}')
    
    context = {
        'user': request.user,
        'title': '비밀번호 변경'
    }
    return render(request, 'account/change_pwd.html', context)

@login_required
def manage_mentorship(request):
    """멘토쉽 관리 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 관리자와 멘토만 접근 가능, 멘티는 접근 불가
    if not (user.is_admin or user.role == 'mentor'):
        messages.error(request, '관리자 또는 멘토만 접근할 수 있습니다.')
        if user.role == 'mentee':
            return redirect('mentee:mentee')
        else:
            return redirect('account:login')
    
    # 모든 멘토십 목록 가져오기
    mentorships = Mentorship.objects.all().order_by('-start_date')
    
    # 멘토십 상세 정보 가공
    mentorship_data = []
    for mentorship in mentorships:
        try:
            mentor = User.objects.get(user_id=mentorship.mentor_id)
            mentee = User.objects.get(user_id=mentorship.mentee_id)
            
            # 과제 통계
            tasks = TaskAssign.objects.filter(mentorship_id=mentorship.mentorship_id)
            task_stats = {
                'total': tasks.count(),
                'completed': tasks.filter(status='완료').count(),
                'in_progress': tasks.filter(status='진행 중').count(),
                'review': tasks.filter(status='검토 요청').count()
            }
            
            progress = int((task_stats['completed'] / task_stats['total'] * 100)) if task_stats['total'] > 0 else 0
            
            mentorship_info = {
                'mentorship': mentorship,
                'mentor': mentor,
                'mentee': mentee,
                'task_stats': task_stats,
                'progress': progress,
                'days_remaining': calculate_days_remaining(mentorship.end_date) if mentorship.end_date else None
            }
            mentorship_data.append(mentorship_info)
            
        except User.DoesNotExist:
            continue
    
    # 통계 정보
    total_mentorships = mentorships.count()
    active_mentorships = mentorships.filter(is_active=True).count()
    completed_mentorships = mentorships.filter(is_active=False).count()
    
    # 멘토/멘티 목록 (수정 기능용)
    mentors = User.objects.filter(role='mentor', is_active=True).order_by('last_name', 'first_name')
    mentees = User.objects.filter(role='mentee', is_active=True).order_by('last_name', 'first_name')
    curriculums = Curriculum.objects.all().order_by('curriculum_title')
    
    context = {
        'user': request.user,
        'mentorship_data': mentorship_data,
        'total_mentorships': total_mentorships,
        'active_mentorships': active_mentorships,
        'completed_mentorships': completed_mentorships,
        'mentors': mentors,
        'mentees': mentees,
        'curriculums': curriculums,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '멘토쉽 관리'
    }
    return render(request, 'account/manage_mentorship.html', context)

# 기본 API 프록시 뷰들 (필요시)
@login_required
def api_proxy_view(request):
    """FastAPI 프록시 뷰"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            method = data.get('method', 'GET')
            
            with get_fastapi_client() as client:
                if method == 'GET':
                    result = client.get(endpoint)
                elif method == 'POST':
                    result = client.post(endpoint, data.get('data'))
                else:
                    return JsonResponse({'error': '지원하지 않는 메서드'}, status=405)
                
                return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST 요청만 허용'}, status=405)

# 부서 CRUD 함수들
@login_required
def department_create(request):
    """부서 생성 - FastAPI로 프록시"""
    if request.method == 'POST':
        department_name = request.POST.get('department_name')
        description = request.POST.get('description')
        
        if department_name:
            try:
                import requests
                
                # FastAPI로 요청 전송
                response = requests.post(
                    f'{settings.FASTAPI_BASE_URL}/api/v1/account/department/create',
                    json={
                        'department_name': department_name,
                        'description': description
                    },
                    headers={
                        'Authorization': f'Bearer {request.user.email}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    messages.success(request, result.get('message', '부서가 성공적으로 생성되었습니다.'))
                else:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
                    messages.error(request, error_data.get('detail', '부서 생성 중 오류가 발생했습니다.'))
            except Exception as e:
                logger.error(f"부서 생성 API 에러: {e}")
                messages.error(request, f'부서 생성 중 오류가 발생했습니다: {str(e)}')
        else:
            messages.error(request, '부서명을 입력해주세요.')
    
    return redirect('account:supervisor')

@login_required
def department_update(request, department_id):
    """부서 수정"""
    if request.method == 'POST':
        try:
            department = Department.objects.get(department_id=department_id)
            department_name = request.POST.get('department_name')
            description = request.POST.get('description')
            
            if department_name:
                department.department_name = department_name
                department.description = description or ''
                department.save()
                messages.success(request, f'부서 "{department_name}"이(가) 성공적으로 수정되었습니다.')
            else:
                messages.error(request, '부서명을 입력해주세요.')
        except Department.DoesNotExist:
            messages.error(request, '부서를 찾을 수 없습니다.')
        except Exception as e:
            messages.error(request, f'부서 수정 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('account:supervisor')

@login_required
def department_delete(request, department_id):
    """부서 삭제"""
    try:
        department = Department.objects.get(department_id=department_id)
        department_name = department.department_name
        
        # 부서에 소속된 사용자가 있는지 확인
        user_count = User.objects.filter(department=department).count()
        if user_count > 0:
            messages.error(request, f'부서 "{department_name}"에 소속된 사용자가 {user_count}명 있어서 삭제할 수 없습니다.')
        else:
            department.delete()
            messages.success(request, f'부서 "{department_name}"이(가) 성공적으로 삭제되었습니다.')
    except Department.DoesNotExist:
        messages.error(request, '부서를 찾을 수 없습니다.')
    except Exception as e:
        messages.error(request, f'부서 삭제 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('account:supervisor')

@login_required
def department_detail(request, department_id):
    """부서 상세"""
    return redirect('account:supervisor', department_id=department_id)

# 사용자 CRUD 함수들
@login_required
def user_create(request):
    """사용자 생성"""
    if request.method == 'POST':
        # 사용자 생성 폼 페이지로 리다이렉트하거나 여기서 직접 처리
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        employee_number = request.POST.get('employee_number')
        department_id = request.POST.get('department_id')
        position = request.POST.get('position')
        job_part = request.POST.get('job_part')
        role = request.POST.get('role')
        password = request.POST.get('password', '123')  # 기본 비밀번호
        
        if email and first_name and last_name and employee_number:
            try:
                import requests
                
                # FastAPI로 요청 전송
                response = requests.post(
                    f'{settings.FASTAPI_BASE_URL}/api/v1/account/user/create',
                    json={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'employee_number': employee_number,
                        'department_id': int(department_id) if department_id else None,
                        'position': position or '신입',
                        'job_part': job_part or '일반',
                        'role': role or 'mentee',
                        'password': password
                    },
                    headers={
                        'Authorization': f'Bearer {request.user.email}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    messages.success(request, result.get('message', '사용자가 성공적으로 생성되었습니다.'))
                else:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
                    messages.error(request, error_data.get('detail', '사용자 생성 중 오류가 발생했습니다.'))
            except Exception as e:
                logger.error(f"사용자 생성 API 에러: {e}")
                messages.error(request, f'사용자 생성 중 오류가 발생했습니다: {str(e)}')
        else:
            messages.error(request, '필수 정보를 모두 입력해주세요.')
    
    return redirect('account:supervisor')

@login_required
def user_edit(request, user_id):
    """사용자 수정"""
    return redirect('account:supervisor')

@login_required
def user_update_view(request, pk):
    """사용자 업데이트 - FastAPI로 프록시"""
    if request.method == 'POST':
        try:
            import requests
            
            # 요청 데이터 준비
            update_data = {}
            if request.POST.get('first_name'):
                update_data['first_name'] = request.POST.get('first_name')
            if request.POST.get('last_name'):
                update_data['last_name'] = request.POST.get('last_name')
            if request.POST.get('position'):
                update_data['position'] = request.POST.get('position')
            if request.POST.get('job_part'):
                update_data['job_part'] = request.POST.get('job_part')
            if request.POST.get('department_id'):
                update_data['department_id'] = int(request.POST.get('department_id'))
            if request.POST.get('role'):
                update_data['role'] = request.POST.get('role')
            
            # FastAPI로 요청 전송
            response = requests.put(
                f'{settings.FASTAPI_BASE_URL}/api/v1/account/user/{pk}/update',
                json=update_data,
                headers={
                    'Authorization': f'Bearer {request.user.email}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                messages.success(request, result.get('message', '사용자가 성공적으로 수정되었습니다.'))
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
                messages.error(request, error_data.get('detail', '사용자 수정 중 오류가 발생했습니다.'))
                
        except Exception as e:
            logger.error(f"사용자 수정 API 에러: {e}")
            messages.error(request, f'사용자 수정 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('account:supervisor')

@login_required
def user_delete(request, user_id):
    """사용자 삭제"""
    try:
        user = User.objects.get(user_id=user_id)
        user_name = user.get_full_name()
        
        # 관련 데이터 확인
        mentorship_count = (
            Mentorship.objects.filter(mentor_id=user_id).count() +
            Mentorship.objects.filter(mentee_id=user_id).count()
        )
        
        if mentorship_count > 0:
            messages.error(request, f'사용자 "{user_name}"은(는) 멘토십 관계가 있어서 삭제할 수 없습니다.')
        else:
            user.delete()
            messages.success(request, f'사용자 "{user_name}"이(가) 성공적으로 삭제되었습니다.')
    except User.DoesNotExist:
        messages.error(request, '사용자를 찾을 수 없습니다.')
    except Exception as e:
        messages.error(request, f'사용자 삭제 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('account:supervisor')

@login_required
def user_delete_view(request, pk):
    """사용자 삭제 (pk 버전)"""
    return user_delete(request, pk)

@login_required
def password_reset(request, user_id):
    """비밀번호 재설정 - FastAPI로 프록시"""
    if request.method == 'POST':
        try:
            import requests
            
            # FastAPI로 요청 전송
            response = requests.post(
                f'{settings.FASTAPI_BASE_URL}/api/v1/account/password_reset/{user_id}',
                headers={
                    'Authorization': f'Bearer {request.user.email}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                return JsonResponse(response.json())
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'message': response.text}
                return JsonResponse({
                    'success': False,
                    'message': error_data.get('detail', '비밀번호 재설정 중 오류가 발생했습니다.')
                })
        except Exception as e:
            logger.error(f"비밀번호 재설정 API 에러: {e}")
            return JsonResponse({
                'success': False,
                'message': f'비밀번호 재설정 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})

@csrf_exempt
def mentorship_edit(request, mentorship_id):
    """멘토쉽 수정 - Django ORM 사용"""
    # 권한 확인
    if not (request.user.is_admin or request.user.role == 'mentor'):
        return JsonResponse({
            'success': False,
            'error': '관리자 또는 멘토만 접근할 수 있습니다.'
        })
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
            
            # 데이터 업데이트
            if 'mentor_id' in data:
                mentorship.mentor_id = data['mentor_id']
            if 'mentee_id' in data:
                mentorship.mentee_id = data['mentee_id']
            if 'start_date' in data:
                mentorship.start_date = data['start_date']
            if 'end_date' in data:
                mentorship.end_date = data['end_date']
            if 'curriculum_title' in data:
                mentorship.curriculum_title = data['curriculum_title']
            if 'is_active' in data:
                mentorship.is_active = data['is_active'] == 'true' or data['is_active'] == True
            
            mentorship.save()
            
            return JsonResponse({
                'success': True,
                'message': '멘토쉽이 성공적으로 수정되었습니다.'
            })
        except Exception as e:
            logger.error(f"멘토쉽 수정 에러: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})

def mentorship_delete(request, mentorship_id):
    """멘토쉽 삭제"""
    # 권한 확인
    if not (request.user.is_admin or request.user.role == 'mentor'):
        return JsonResponse({
            'success': False,
            'error': '관리자 또는 멘토만 접근할 수 있습니다.'
        })
    
    if request.method == 'POST':
        try:
            mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
            
            # 관련된 TaskAssign 레코드들도 삭제
            TaskAssign.objects.filter(mentorship_id=mentorship_id).delete()
            
            mentorship.delete()
            
            return JsonResponse({
                'success': True,
                'message': '멘토쉽이 성공적으로 삭제되었습니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})

@login_required
def mentorship_detail(request, mentorship_id):
    try:
        # FastAPI 서버 URL 설정
        fastapi_url = f"http://localhost:8003/api/v1/mentorships/{mentorship_id}"
        
        # FastAPI 서버로 요청 보내기
        response = requests.get(fastapi_url)
        
        if response.status_code == 200:
            mentorship_data = response.json()
            return JsonResponse(mentorship_data, safe=False)
        else:
            return JsonResponse({'error': 'FastAPI 서버에서 데이터 조회 실패'}, status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'FastAPI 서버 연결 오류: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'예기치 못한 오류: {str(e)}'}, status=500)

# 헬퍼 함수들
def calculate_days_remaining(end_date):
    """남은 일수 계산"""
    if not end_date:
        return None
    
    today = date.today()
    delta = end_date - today
    return delta.days
>>>>>>> Stashed changes
