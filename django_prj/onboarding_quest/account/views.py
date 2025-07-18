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
from django.db.models import Q
from core.utils.fastapi_client import fastapi_client, APIError, AuthenticationError, NotFoundError
import json
import logging

logger = logging.getLogger(__name__)

def safe_get_user_data(session_data):
    """세션에서 사용자 데이터를 안전하게 추출하는 함수"""
    if isinstance(session_data, dict):
        return session_data
    elif isinstance(session_data, list) and len(session_data) > 0:
        # 리스트의 첫 번째 항목이 사용자 데이터인 경우
        first_item = session_data[0]
        if hasattr(first_item, 'dict'):
            return first_item.dict()
        elif hasattr(first_item, '__dict__'):
            return first_item.__dict__
        elif isinstance(first_item, dict):
            return first_item
    return {}





#region 로그인/로그아웃
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # FastAPI로 로그인 시도
            login_response = fastapi_client.login(email, password)
            logger.info(f"Login response type: {type(login_response)}")
            logger.info(f"Login response keys: {list(login_response.keys()) if isinstance(login_response, dict) else 'Not a dict'}")
            
            # JWT 토큰을 세션에 저장
            request.session['jwt_token'] = login_response['access_token']
            
            # 사용자 데이터 처리 및 로깅
            user_data = login_response['user']
            logger.info(f"User data type: {type(user_data)}")
            logger.info(f"User data keys: {list(user_data.keys()) if isinstance(user_data, dict) else 'Not a dict'}")
            
            # 사용자 데이터를 딕셔너리로 변환하여 저장
            if isinstance(user_data, dict):
                user_dict = user_data
            elif hasattr(user_data, 'dict'):
                user_dict = user_data.dict()
            elif hasattr(user_data, '__dict__'):
                user_dict = user_data.__dict__
            else:
                logger.error(f"Unknown user_data format: {type(user_data)}")
                user_dict = {}
            
            request.session['user_data'] = user_dict
            logger.info(f"Stored user_dict keys: {list(user_dict.keys())}")
            
            # FastAPI 클라이언트에 토큰 설정
            fastapi_client.set_auth_token(login_response['access_token'])
            
            # Django 세션에 사용자 정보 저장 (기존 Django 인증과의 호환성을 위해)
            try:
                # Django User 모델에서 사용자 찾기 (세션 관리용)
                django_user = User.objects.get(email=email)
                login(request, django_user)
            except User.DoesNotExist:
                # FastAPI에만 있는 사용자인 경우 세션 데이터만 저장
                pass
            
            # 역할에 따라 리다이렉트
            if user_dict.get('is_admin'):
                return redirect('account:supervisor')
            elif user_dict.get('role') == 'mentor':
                return redirect('mentor:mentor')
            elif user_dict.get('role') == 'mentee':
                return redirect('mentee:mentee')
            else:
                return redirect('/')
                
        except AuthenticationError:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        except ConnectionError:
            messages.error(request, 'FastAPI 서버에 연결할 수 없습니다. 관리자에게 문의하세요.')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            messages.error(request, f'로그인 중 오류가 발생했습니다: {str(e)}')
        
        return render(request, 'account/login.html')
    
    # GET 요청일 때 특정 에러 메시지들을 필터링
    if request.method == 'GET':
        storage = messages.get_messages(request)
        filtered_messages = []
        for message in storage:
            # "데이터를 불러오는 중 오류가 발생했습니다"로 시작하는 메시지는 제외
            if not str(message).startswith('데이터를 불러오는 중 오류가 발생했습니다'):
                filtered_messages.append(message)
        
        # 필터링된 메시지들을 다시 추가
        for msg in filtered_messages:
            messages.add_message(request, msg.level, str(msg))
    
    return render(request, 'account/login.html')

def logout_view(request):
    """로그아웃 처리 - 안전한 방식으로 개선"""
    logger.info("Logout process started")
    
    # FastAPI 로그아웃 시도 (선택적, 실패해도 Django 로그아웃은 진행)
    if 'jwt_token' in request.session:
        try:
            fastapi_client.set_auth_token(request.session['jwt_token'])
            logout_result = fastapi_client.logout()
            logger.info(f"FastAPI logout: {logout_result.get('message', 'Success')}")
        except Exception as e:
            logger.warning(f"FastAPI logout failed: {str(e)} - continuing with Django logout")
    
    # Django 세션 정리 (항상 수행)
    try:
        logout(request)
        logger.info("Django logout completed successfully")
    except Exception as e:
        logger.error(f"Django logout error: {str(e)}")
    
    # 세션 데이터 정리
    session_keys_to_remove = ['jwt_token', 'user_data']
    for key in session_keys_to_remove:
        try:
            if key in request.session:
                del request.session[key]
        except Exception as e:
            logger.warning(f"Session key {key} removal failed: {str(e)}")
    
    # 모든 기존 메시지 정리 (에러 메시지 포함)
    storage = messages.get_messages(request)
    for message in storage:
        pass  # 메시지 소비하여 제거
    
    # 새로운 요청 객체로 리다이렉트하여 메시지 시스템 초기화
    logger.info("Logout process completed - redirecting to login")
    
    # 로그아웃 성공 메시지는 쿼리 파라미터로 전달
    return redirect('account:login')
#endregion 로그인/로그아웃 





#region 관리자

@login_required
def supervisor(request):
    try:
        # 사용자 인증 상태 확인
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated user accessing supervisor")
            return redirect('account:login')
        
        # 세션 데이터 확인
        if 'user_data' not in request.session:
            logger.warning("No user_data in session for supervisor access")
            messages.error(request, '세션이 만료되었습니다. 다시 로그인해주세요.')
            return redirect('account:login')
        
        # JWT 토큰 설정
        if 'jwt_token' in request.session:
            fastapi_client.set_auth_token(request.session['jwt_token'])
        else:
            logger.warning("No JWT token in session")
            messages.error(request, '인증 토큰이 없습니다. 다시 로그인해주세요.')
            return redirect('account:login')
        
        # 현재 사용자 정보 가져오기 - 안전한 방식으로 처리
        user_data_raw = request.session.get('user_data', {})
        user_data = safe_get_user_data(user_data_raw)
        logger.info(f"Supervisor view - user_data type: {type(user_data_raw)}")
        logger.info(f"Supervisor view - processed user_data keys: {list(user_data.keys())}")
        
        company_id = user_data.get('company_id')
        logger.info(f"Company ID: {company_id}")
        
        if not company_id:
            messages.error(request, '회사 정보를 찾을 수 없습니다.')
            return redirect('account:login')
        
        # FastAPI에서 부서 목록 가져오기
        logger.info("Fetching departments...")
        departments_response = fastapi_client.get_departments(company_id=company_id)
        logger.info(f"Departments response type: {type(departments_response)}")
        logger.info(f"Departments response: {departments_response}")
        
        departments = departments_response.get('departments', [])
        logger.info(f"Departments type: {type(departments)}")
        
        # 검색 및 필터링 파라미터
        search_query = request.GET.get('search', '')
        selected_department_id = request.GET.get('dept')
        position_filter = request.GET.get('position', '')
        
        # FastAPI에서 사용자 목록 가져오기
        logger.info("Fetching users...")
        users_params = {
            'company_id': company_id,
            'search': search_query if search_query else None,
            'department_id': int(selected_department_id) if selected_department_id else None
        }
        logger.info(f"Users params: {users_params}")
        
        users_response = fastapi_client.get_users(**{k: v for k, v in users_params.items() if v is not None})
        logger.info(f"Users response type: {type(users_response)}")
        logger.info(f"Users response: {users_response}")
        
        users = users_response.get('users', [])
        logger.info(f"Users type: {type(users)}")
        
        # 선택된 부서 정보
        dept_detail = None
        if selected_department_id:
            try:
                logger.info(f"Fetching department detail for ID: {selected_department_id}")
                dept_detail = fastapi_client.get_department(int(selected_department_id))
                logger.info(f"Department detail type: {type(dept_detail)}")
            except Exception as e:
                logger.error(f"Error fetching department detail: {e}")
                pass
        
        # 부서 폼 (나중에 FastAPI로 변환 예정)
        dept_form = DepartmentForm()
        
        return render(request, 'account/supervisor.html', {
            'departments': departments,
            'users': users,
            'dept_form': dept_form,
            'selected_department_id': int(selected_department_id) if selected_department_id else None,
            'dept_detail': dept_detail,
            'search_query': search_query,
        })
        
    except AuthenticationError:
        messages.error(request, '인증이 만료되었습니다. 다시 로그인해주세요.')
        return redirect('account:login')
    except ConnectionError:
        messages.error(request, 'FastAPI 서버에 연결할 수 없습니다.')
        # Fallback to Django models (optional)
        return redirect('account:login')
    except Exception as e:
        logger.error(f"Supervisor view error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        messages.error(request, f'데이터를 불러오는 중 오류가 발생했습니다: {str(e)}')
        return redirect('account:login')

@login_required
def admin_dashboard(request, department_id=None):
    if not request.user.is_admin:
        return render(request, 'account/login.html')

    try:
        # 현재 사용자 정보 - 안전한 방식으로 처리
        user_data_raw = request.session.get('user_data', {})
        user_data = safe_get_user_data(user_data_raw)
        company_id = user_data.get('company_id')
        
        # 전체 부서 가져오기
        departments_result = fastapi_client.get_departments(company_id=company_id)
        departments = departments_result.get('departments', [])

        # 부서가 선택된 경우 해당 부서의 유저만
        if department_id:
            users_result = fastapi_client.get_users(company_id=company_id, department_id=int(department_id))
            selected_department_id = int(department_id)
        else:
            users_result = fastapi_client.get_users(company_id=company_id)
            selected_department_id = None
        
        users = users_result.get('users', [])

        return render(request, 'account/supervisor.html', {
            'departments': departments,
            'users': users,
            'selected_department_id': selected_department_id,
        })
        
    except (AuthenticationError, APIError) as e:
        messages.error(request, f'데이터 조회 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'account/supervisor.html', {
            'departments': [],
            'users': [],
            'selected_department_id': None,
        })

@login_required
def admin_dashboard_view(request):
    if not request.user.is_admin:
        return HttpResponseForbidden("접근 권한이 없습니다.")

    try:
        # 현재 사용자 정보 - 안전한 방식으로 처리
        user_data_raw = request.session.get('user_data', {})
        user_data = safe_get_user_data(user_data_raw)
        company_id = user_data.get('company_id')
        
        # FastAPI에서 데이터 조회
        users_result = fastapi_client.get_users(is_active=True, company_id=company_id)
        departments_result = fastapi_client.get_departments(company_id=company_id)
        
        users = users_result.get('users', [])
        departments = departments_result.get('departments', [])

        return render(request, 'account/supervisor.html', {
            'user': request.user, 
            'users': users, 
            'departments': departments,
        })
        
    except (AuthenticationError, APIError) as e:
        messages.error(request, f'데이터 조회 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'account/supervisor.html', {
            'user': request.user,
            'users': [],
            'departments': [],
        })



#region > 부서 생성/조회/수정/삭제
@login_required
def department_create(request):
    if request.method == 'POST':
        try:
            department_name = request.POST.get('department_name')
            description = request.POST.get('description', '')
            
            # 현재 사용자 정보에서 회사 ID 가져오기 - 안전한 방식으로 처리
            user_data_raw = request.session.get('user_data', {})
            user_data = safe_get_user_data(user_data_raw)
            company_id = user_data.get('company_id')
            
            if not company_id:
                messages.error(request, '회사 정보를 찾을 수 없습니다.')
                return redirect('account:supervisor')
            
            # FastAPI로 부서 생성
            dept_data = {
                'department_name': department_name,
                'description': description,
                'company_id': company_id
            }
            
            result = fastapi_client.create_department(dept_data)
            messages.success(request, f"부서 '{department_name}'가 성공적으로 생성되었습니다.")
            
        except AuthenticationError:
            messages.error(request, '인증이 만료되었습니다. 다시 로그인해주세요.')
            return redirect('account:login')
        except APIError as e:
            messages.error(request, f'부서 생성 중 오류가 발생했습니다: {str(e)}')
        except Exception as e:
            messages.error(request, f'부서 생성 중 예상치 못한 오류가 발생했습니다: {str(e)}')
        
        return redirect('account:supervisor')

@login_required
@require_GET
def department_detail(request, department_id):
    try:
        # FastAPI에서 부서 상세 정보 조회
        dept_result = fastapi_client.get_department(department_id)
        dept = dept_result
        
        # 현재 사용자 정보 - 안전한 방식으로 처리
        user_data_raw = request.session.get('user_data', {})
        user_data = safe_get_user_data(user_data_raw)
        company_id = user_data.get('company_id')
        
        # 부서 목록과 해당 부서의 사용자 목록 조회
        departments_result = fastapi_client.get_departments(company_id=company_id)
        users_result = fastapi_client.get_users(department_id=department_id, is_active=True)
        
        departments = departments_result.get('departments', [])
        users = users_result.get('users', [])
        
        return render(request, 'account/supervisor.html', {
            'departments': departments,
            'users': users,
            'selected_department_id': dept.get('department_id'),
            'dept_detail': dept,
            'view_mode': request.GET.get('view', None),
        })
        
    except (AuthenticationError, APIError) as e:
        messages.error(request, f'부서 정보 조회 중 오류가 발생했습니다: {str(e)}')
        return redirect('account:supervisor')

# 부서 수정
@login_required
def department_update(request, department_id):
    if request.method == 'POST':
        try:
            # 부서 정보 수정
            dept_data = {
                'department_name': request.POST.get('department_name'),
                'description': request.POST.get('description', ''),
            }
            
            result = fastapi_client.update_department(department_id, dept_data)
            messages.success(request, '부서 정보가 성공적으로 수정되었습니다.')
            
        except (AuthenticationError, APIError) as e:
            messages.error(request, f'부서 수정 중 오류가 발생했습니다: {str(e)}')
        
        return redirect('account:supervisor')
    
    # GET 요청시 부서 정보 조회
    try:
        dept_result = fastapi_client.get_department(department_id)
        
        # 현재 사용자 정보 - 안전한 방식으로 처리
        user_data_raw = request.session.get('user_data', {})
        user_data = safe_get_user_data(user_data_raw)
        company_id = user_data.get('company_id')
        departments_result = fastapi_client.get_departments(company_id=company_id)
        
        return render(request, 'account/supervisor.html', {
            'departments': departments_result.get('departments', []),
            'dept_detail': dept_result,
            'edit_mode': True,
        })
        
    except (AuthenticationError, APIError) as e:
        messages.error(request, f'부서 정보 조회 중 오류가 발생했습니다: {str(e)}')
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
        try:
            # 폼 데이터 수집
            user_data = {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email'),
                'password': '123',  # 기본 비밀번호
                'job_part': request.POST.get('job_part'),
                'position': request.POST.get('position'),
                'join_date': request.POST.get('join_date'),
                'tag': request.POST.get('tag', ''),
                'role': request.POST.get('role'),
                'employee_number': int(request.POST.get('employee_number')) if request.POST.get('employee_number') else None,
                'is_admin': request.POST.get('is_admin') == 'on',
                'department_id': int(request.POST.get('department_id')) if request.POST.get('department_id') else None,
            }
            
            # 현재 사용자의 회사 ID 추가
            user_data_session = request.session.get('user_data', {})
            company_id = user_data_session.get('company_id')
            if company_id:
                user_data['company_id'] = company_id
            
            # FastAPI로 사용자 생성
            result = fastapi_client.create_user(user_data)
            messages.success(request, f"사용자 '{user_data['first_name']} {user_data['last_name']}'가 성공적으로 생성되었습니다.")
            return redirect('account:supervisor')
            
        except AuthenticationError:
            messages.error(request, '인증이 만료되었습니다. 다시 로그인해주세요.')
            return redirect('account:login')
        except APIError as e:
            messages.error(request, f'사용자 생성 중 오류가 발생했습니다: {str(e)}')
        except Exception as e:
            messages.error(request, f'사용자 생성 중 예상치 못한 오류가 발생했습니다: {str(e)}')
    
    # GET 요청이거나 에러 발생 시 폼 렌더링
    form = UserForm(company=request.user.company if hasattr(request.user, 'company') else None)
    return render(request, 'account/user_add_modify.html', {'form': form})

# 사용자 수정
@login_required
def user_edit(request, user_id):
    try:
        if request.method == 'POST':
            # 수정할 데이터 수집
            user_data = {}
            for field in ['first_name', 'last_name', 'email', 'job_part', 'position', 'join_date', 'tag', 'role']:
                value = request.POST.get(field)
                if value:
                    user_data[field] = value
            
            # 숫자 필드 처리
            if request.POST.get('employee_number'):
                user_data['employee_number'] = int(request.POST.get('employee_number'))
            if request.POST.get('department_id'):
                user_data['department_id'] = int(request.POST.get('department_id'))
            
            user_data['is_admin'] = request.POST.get('is_admin') == 'on'
            
            # FastAPI로 사용자 수정
            result = fastapi_client.update_user(user_id, user_data)
            messages.success(request, '프로필 정보가 저장되었습니다.')
            return redirect('account:user_edit', user_id=user_id)
        else:
            # 사용자 정보 조회
            user_info = fastapi_client.get_user(user_id)
            form = UserForm(instance=None, company=None)  # FastAPI 데이터로 렌더링
            return render(request, 'account/profile.html', {'form': form, 'user': user_info})
            
    except AuthenticationError:
        messages.error(request, '인증이 만료되었습니다. 다시 로그인해주세요.')
        return redirect('account:login')
    except APIError as e:
        messages.error(request, f'사용자 정보 처리 중 오류가 발생했습니다: {str(e)}')
        return redirect('account:supervisor')
    except Exception as e:
        messages.error(request, f'예상치 못한 오류가 발생했습니다: {str(e)}')
        return redirect('account:supervisor')

# 사용자 삭제
@login_required
def user_delete(request, user_id):
    try:
        # 현재 사용자가 관리자인지 확인 - 안전한 방식으로 처리
        current_user_data_raw = request.session.get('user_data', {})
        current_user_data = safe_get_user_data(current_user_data_raw)
        if not current_user_data.get('is_admin'):
            messages.error(request, '관리자만 사용자를 삭제할 수 있습니다.')
            return redirect('account:supervisor')
        
        # 자기 자신은 삭제할 수 없음
        if current_user_data.get('user_id') == user_id:
            messages.error(request, '자기 자신은 삭제할 수 없습니다.')
            return redirect('account:supervisor')
        
        # FastAPI로 사용자 삭제
        result = fastapi_client.delete_user(user_id)
        messages.success(request, '사용자가 성공적으로 삭제되었습니다.')
        
    except AuthenticationError:
        messages.error(request, '인증이 만료되었습니다. 다시 로그인해주세요.')
        return redirect('account:login')
    except APIError as e:
        messages.error(request, f'사용자 삭제 중 오류가 발생했습니다: {str(e)}')
    except Exception as e:
        messages.error(request, f'예상치 못한 오류가 발생했습니다: {str(e)}')
    
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
    if request.method == 'POST':
        # 태그 업데이트 처리
        tags = request.POST.get('tags', '').strip()
        if tags:
            # 쉼표로 구분된 태그를 정리
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            # 다시 쉼표로 구분된 문자열로 저장
            request.user.tag = ', '.join(tag_list)
        else:
            request.user.tag = ''
        
        request.user.save()
        messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
        return redirect('account:profile')
    
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
    
    try:
        # 검색 및 필터링 파라미터
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        department_filter = request.GET.get('department', '')
        
        # FastAPI에서 멘토쉽 목록 조회
        mentorships_result = fastapi_client.get_mentorships()
        mentorships = mentorships_result.get('mentorships', [])
        
        # 현재 사용자 정보 - 안전한 방식으로 처리
        user_data_raw = request.session.get('user_data', {})
        user_data = safe_get_user_data(user_data_raw)
        company_id = user_data.get('company_id')
        
        # 사용자 목록 조회
        users_result = fastapi_client.get_users(company_id=company_id)
        all_users = {user['user_id']: user for user in users_result.get('users', [])}
        
        # 검색 조건 적용 (프론트엔드에서 필터링)
        if search_query:
            filtered_mentorships = []
            for mentorship in mentorships:
                mentor = all_users.get(mentorship.get('mentor_id'))
                mentee = all_users.get(mentorship.get('mentee_id'))
                
                if mentor and (search_query.lower() in f"{mentor.get('first_name', '')}{mentor.get('last_name', '')}".lower()):
                    filtered_mentorships.append(mentorship)
                elif mentee and (search_query.lower() in f"{mentee.get('first_name', '')}{mentee.get('last_name', '')}".lower()):
                    filtered_mentorships.append(mentorship)
            mentorships = filtered_mentorships
        
        # 상태 필터 적용
        if status_filter == 'active':
            mentorships = [m for m in mentorships if m.get('is_active', True)]
        elif status_filter == 'inactive':
            mentorships = [m for m in mentorships if not m.get('is_active', True)]
        
        # 부서 필터 적용
        if department_filter:
            filtered_mentorships = []
            for mentorship in mentorships:
                mentor = all_users.get(mentorship.get('mentor_id'))
                mentee = all_users.get(mentorship.get('mentee_id'))
                
                if (mentor and mentor.get('department_id') == int(department_filter)) or \
                   (mentee and mentee.get('department_id') == int(department_filter)):
                    filtered_mentorships.append(mentorship)
        
        # 부서 목록 조회 (모달용)
        departments_result = fastapi_client.get_departments(company_id=company_id)
        departments = departments_result.get('departments', [])
        
        # 멘토와 멘티 목록 (모달용)
        mentors_result = fastapi_client.get_users(role='mentor', is_active=True, company_id=company_id)
        mentees_result = fastapi_client.get_users(role='mentee', is_active=True, company_id=company_id)
        mentors = mentors_result.get('users', [])
        mentees = mentees_result.get('users', [])
        
        # 커리큘럼 목록 가져오기
        curriculums_result = fastapi_client.get_curriculums()
        curriculums = curriculums_result.get('curriculums', [])
        
        # 멘토쉽에 사용자 정보 추가
        for mentorship in mentorships:
            mentorship['mentor'] = all_users.get(mentorship.get('mentor_id'))
            mentorship['mentee'] = all_users.get(mentorship.get('mentee_id'))
        
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
        
    except (AuthenticationError, APIError) as e:
        messages.error(request, f'멘토쉽 정보 조회 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'account/manage_mentorship.html', {
            'mentorships': [],
            'mentors': [],
            'mentees': [],
            'departments': [],
            'curriculums': [],
            'search_query': search_query,
            'status_filter': status_filter,
            'department_filter': department_filter,
        })

@login_required
def mentorship_detail(request, mentorship_id):
    """멘토쉽 상세 정보 (AJAX)"""
    if not request.user.is_admin:
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
    
    try:
        # FastAPI에서 멘토쉽 상세 정보 조회
        mentorship = fastapi_client.get_mentorship(mentorship_id)
        
        data = {
            'mentor_id': mentorship.get('mentor_id'),
            'mentee_id': mentorship.get('mentee_id'),
            'curriculum_id': mentorship.get('curriculum_id'),
            'start_date': mentorship.get('start_date'),
            'end_date': mentorship.get('end_date'),
            'is_active': mentorship.get('is_active'),
            'curriculum_title': mentorship.get('curriculum_title'),
            'total_weeks': mentorship.get('total_weeks'),
        }
        return JsonResponse(data)
        
    except (AuthenticationError, APIError) as e:
        return JsonResponse({'error': f'멘토쉽 정보 조회 실패: {str(e)}'}, status=400)

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


