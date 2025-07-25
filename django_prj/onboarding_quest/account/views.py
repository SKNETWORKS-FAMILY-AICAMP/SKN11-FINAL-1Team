from django.views.decorators.http import require_GET
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponseForbidden
from core.models import User, Department, Mentorship, Curriculum
from account.forms import UserForm, CustomPasswordChangeForm, UserEditForm, DepartmentForm
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from core.utils.fastapi_client import fastapi_client, APIError, AuthenticationError, NotFoundError
import json
import logging
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
                # 🔧 멘티의 경우 활성 멘토십과 함께 리다이렉트
                user_id = user_dict.get('user_id')
                mentorship_id = None
                
                print(f"🔍 LOGIN - 멘티 로그인: user_id={user_id}")
                
                # Django ORM으로 활성 멘토십 조회
                try:
                    from core.models import Mentorship
                    active_mentorship = Mentorship.objects.filter(
                        mentee_id=user_id, 
                        is_active=True
                    ).first()
                    
                    if active_mentorship:
                        mentorship_id = active_mentorship.mentorship_id
                        print(f"🔍 LOGIN - 활성 멘토십 발견: mentorship_id={mentorship_id}")
                        return redirect(f"/mentee/?mentorship_id={mentorship_id}")
                    else:
                        print(f"🔍 LOGIN - 활성 멘토십이 없음. 기본 리다이렉트")
                        return redirect('mentee:mentee')
                except Exception as e:
                    print(f"🔍 LOGIN - 멘토십 조회 실패: {e}")
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
        employee_number_filter = request.GET.get('employee_number', '')
        join_date_filter = request.GET.get('join_date', '')
        
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
        
        # 사번 및 입사일 동시 필터링 적용
        if employee_number_filter or join_date_filter:
            users = [user for user in users if (
                (not employee_number_filter or user.get('employee_number') == int(employee_number_filter)) and
                (not join_date_filter or user.get('join_date') == join_date_filter)
            )]
        
        # 사번 내림차순 및 입사일 오름차순 정렬 적용
        users.sort(key=lambda user: (
            -user.get('employee_number', 0),  # 사번 내림차순
            user.get('join_date', '')        # 입사일 오름차순
        ))
        
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
        # AJAX/JSON 요청 처리
        if request.content_type == 'application/json':
            import json
            try:
                json_data = json.loads(request.body)
                user_data = {
                    'first_name': json_data.get('first_name'),
                    'last_name': json_data.get('last_name'),
                    'email': json_data.get('email'),
                    'password': json_data.get('password', '123'),
                    'job_part': json_data.get('job_part'),
                    'position': json_data.get('position'),
                    'join_date': json_data.get('join_date'),
                    'tag': json_data.get('tag', ''),
                    'role': json_data.get('role'),
                    'employee_number': int(json_data.get('employee_number')) if json_data.get('employee_number') else None,
                    'is_admin': json_data.get('is_admin') == True,
                    'department_id': int(json_data.get('department_id')) if json_data.get('department_id') else None,
                    'is_active': json_data.get('is_active', False),
                }
                user_data_session = request.session.get('user_data', {})
                company_id = user_data_session.get('company_id')
                if company_id:
                    try:
                        user_data['company_id'] = int(company_id)
                    except Exception:
                        pass  # company_id가 int가 아니면 전달하지 않음
                result = fastapi_client.create_user(user_data)
                return JsonResponse({
                    'success': True,
                    'user_id': result.get('user_id'),
                    'message': f"사용자 '{user_data['first_name']} {user_data['last_name']}'가 성공적으로 생성되었습니다."
                })
            except AuthenticationError:
                return JsonResponse({'success': False, 'error': '인증이 만료되었습니다. 다시 로그인해주세요.'}, status=401)
            except APIError as e:
                return JsonResponse({'success': False, 'error': f'사용자 생성 중 오류가 발생했습니다: {str(e)}'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'사용자 생성 중 예상치 못한 오류가 발생했습니다: {str(e)}'}, status=500)
        # 기존 폼 처리
        try:
            user_data = {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email'),
                'password': '123',
                'job_part': request.POST.get('job_part'),
                'position': request.POST.get('position'),
                'join_date': request.POST.get('join_date'),
                'tag': request.POST.get('tag', ''),
                'role': request.POST.get('role'),
                'employee_number': int(request.POST.get('employee_number')) if request.POST.get('employee_number') else None,
                'is_admin': request.POST.get('is_admin') == 'on',
                'department_id': int(request.POST.get('department_id')) if request.POST.get('department_id') else None,
                'is_active': request.POST.get('is_active') == 'on',
            }
            user_data_session = request.session.get('user_data', {})
            company_id = user_data_session.get('company_id')
            if company_id:
                try:
                    user_data['company_id'] = int(company_id)
                except Exception:
                    pass
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
            # is_active 처리 (체크 안하면 False, None도 False로)
            is_active_val = request.POST.get('is_active')
            user_data['is_active'] = True if is_active_val == 'on' or is_active_val is True else False

            # company_id 추가 (user_create와 동일하게)
            user_data_session = request.session.get('user_data', {})
            company_id = user_data_session.get('company_id')
            if company_id:
                try:
                    user_data['company_id'] = int(company_id)
                except Exception:
                    pass
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
from django.http import JsonResponse

@login_required
def user_delete(request, user_id):
    try:
        current_user_data_raw = request.session.get('user_data', {})
        current_user_data = safe_get_user_data(current_user_data_raw)

        # 관리자 권한 확인
        if not current_user_data.get('is_admin'):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': '관리자만 사용자를 삭제할 수 있습니다.'})
            messages.error(request, '관리자만 사용자를 삭제할 수 있습니다.')
            return redirect('account:supervisor')
        
        # 자기 자신 삭제 방지
        if current_user_data.get('user_id') == user_id:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': '자기 자신은 삭제할 수 없습니다.'})
            messages.error(request, '자기 자신은 삭제할 수 없습니다.')
            return redirect('account:supervisor')
        
        # FastAPI 호출
        result = fastapi_client.delete_user(user_id)

        # AJAX 요청이면 JSON 응답
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        # 기본 리다이렉트 (단일 삭제 버튼)
        messages.success(request, '사용자가 성공적으로 삭제되었습니다.')
        return redirect('account:supervisor')

    except AuthenticationError:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': '인증이 만료되었습니다. 다시 로그인해주세요.'})
        messages.error(request, '인증이 만료되었습니다. 다시 로그인해주세요.')
        return redirect('account:login')

    except APIError as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f'사용자 삭제 중 오류가 발생했습니다: {str(e)}')
        return redirect('account:supervisor')

    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f'예상치 못한 오류가 발생했습니다: {str(e)}')
        return redirect('account:supervisor')

@login_required
def user_update_view(request, pk):
    if request.method == 'POST':
        # AJAX/JSON 요청 처리
        if request.content_type == 'application/json':
            try:
                json_data = json.loads(request.body)
                logger.info(f"Received JSON data: {json_data}")
                
                user_data = {}
                for field in ['first_name', 'last_name', 'email', 'job_part', 'position', 'join_date', 'tag', 'role']:
                    value = json_data.get(field)
                    if value is not None and str(value).strip():
                        user_data[field] = str(value).strip()
                
                # is_active 처리 (체크 안하면 False)
                user_data['is_active'] = bool(json_data.get('is_active', False))
                logger.info(f"is_active set to: {user_data['is_active']}")
                
                # 숫자 필드 처리 (빈 문자열, None, 0 등을 안전하게 처리)
                employee_number = json_data.get('employee_number')
                if employee_number is not None and str(employee_number).strip():
                    try:
                        user_data['employee_number'] = int(employee_number)
                        logger.info(f"employee_number set to: {user_data['employee_number']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to convert employee_number '{employee_number}': {e}")
                
                department_id = json_data.get('department_id')
                if department_id is not None and str(department_id).strip():
                    try:
                        user_data['department_id'] = int(department_id)
                        logger.info(f"department_id set to: {user_data['department_id']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to convert department_id '{department_id}': {e}")
                
                if 'is_admin' in json_data:
                    user_data['is_admin'] = bool(json_data.get('is_admin'))
                
                # company_id 추가 (user_create와 동일하게)
                user_data_session = request.session.get('user_data', {})
                company_id = user_data_session.get('company_id')
                if company_id:
                    try:
                        user_data['company_id'] = int(company_id)
                        logger.info(f"company_id set to: {user_data['company_id']}")
                    except Exception as e:
                        logger.warning(f"Failed to convert company_id '{company_id}': {e}")
                
                # FastAPI로 사용자 수정, 예외가 없으면 성공으로 간주
                logger.info(f"Updating user {pk} with data: {user_data}")
                try:
                    fastapi_client.update_user(pk, user_data)
                    logger.info(f"User {pk} updated successfully")
                    return JsonResponse({
                        'success': True,
                        'user_id': pk,
                        'message': '사용자 정보가 성공적으로 수정되었습니다.'
                    })
                except Exception as update_error:
                    logger.error(f"FastAPI update_user failed: {str(update_error)}")
                    logger.error(f"Update error type: {type(update_error)}")
                    raise
            except AuthenticationError:
                logger.error("Authentication error in user_update_view")
                return JsonResponse({'success': False, 'error': '인증이 만료되었습니다. 다시 로그인해주세요.'}, status=401)
            except APIError as e:
                logger.error(f"API error in user_update_view: {str(e)}")
                return JsonResponse({'success': False, 'error': f'사용자 수정 중 오류가 발생했습니다: {str(e)}'}, status=400)
            except Exception as e:
                logger.error(f"Unexpected error in user_update_view: {str(e)}")
                logger.error(f"Exception type: {type(e)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                return JsonResponse({'success': False, 'error': f'사용자 수정 중 예상치 못한 오류가 발생했습니다: {str(e)}'}, status=500)
        # 기존 폼 처리
        form = UserForm(request.POST, company=request.user.company if hasattr(request.user, 'company') else None)
        if form.is_valid():
            user_data = form.cleaned_data
            dept = user_data.pop('department', None)
            user_data['department_id'] = dept.department_id if dept else None
            user_data['tag'] = form.cleaned_data.get('tag')
            # is_active 처리 (체크 안하면 False)
            user_data['is_active'] = request.POST.get('is_active') == 'on'
            result = fastapi_client.update_user(pk, user_data)
            if result.get('success'):
                messages.success(request, '사용자 정보가 수정되었습니다.')
            else:
                messages.error(request, '수정 실패: ' + result.get('error', '알 수 없는 오류'))
            return redirect('account:supervisor')
    else:
        user_info = fastapi_client.get_user(pk)
        initial_data = {
            'employee_number': user_info.get('employee_number'),
            'first_name': user_info.get('first_name'),
            'last_name': user_info.get('last_name'),
            'email': user_info.get('email'),
            'department': user_info.get('department_id'),
            'position': user_info.get('position'),
            'job_part': user_info.get('job_part'),
            'role': user_info.get('role'),
            'tag': user_info.get('tag'),
            'is_admin': user_info.get('is_admin'),
            'is_active': user_info.get('is_active'),
        }
        form = UserForm(initial=initial_data, company=request.user.company if hasattr(request.user, 'company') else None)
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
def user_password_reset(request, user_id):
    if request.method == 'POST':
        try:
            current_user_data = safe_get_user_data(request.session.get('user_data', {}))
            if not current_user_data.get('is_admin'):
                return JsonResponse({'success': False, 'message': '관리자 권한이 필요합니다.'}, status=403)

            result = fastapi_client.reset_password(user_id)
            if result.get('success'):
                return JsonResponse({'success': True, 'message': '비밀번호가 초기화되었습니다. (초기 비밀번호: 123)'})
            else:
                return JsonResponse({'success': False, 'message': result.get('error', '비밀번호 초기화 실패')}, status=400)

        except AuthenticationError:
            return JsonResponse({'success': False, 'message': '인증이 만료되었습니다.'}, status=401)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'}, status=405)
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
    """비밀번호 변경 처리"""
    from .forms import CustomPasswordChangeForm
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        logger.info(f"비밀번호 변경 시도 - 사용자: {request.user.email}")
        logger.info(f"현재 사용자 비밀번호 해시 길이: {len(request.user.password)}")
        logger.info(f"현재 사용자 비밀번호 해시 시작: {request.user.password[:30]}...")
        
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            logger.info("폼 검증 성공")
            new_password = form.cleaned_data['new_password']
            
            # Django 표준 방식으로 비밀번호 설정
            request.user.set_password(new_password)
            request.user.save()
            
            logger.info(f"비밀번호 변경 완료 - 새 해시 길이: {len(request.user.password)}")
            logger.info(f"새 비밀번호 해시 시작: {request.user.password[:30]}...")
            
            # 세션 무효화하고 로그아웃
            logout(request)
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': '/account/login/'})
            else:
                messages.success(request, '비밀번호가 성공적으로 변경되었습니다. 다시 로그인해 주세요.')
                return redirect('account:login')
        else:
            logger.warning(f"폼 검증 실패: {form.errors}")
            error_msgs = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_msgs.append(f"{field}: {error}")
                    logger.warning(f"폼 오류 - {field}: {error}")
            
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
        
        # 디버깅: 멘토쉽 데이터 구조 확인
        if mentorships:
            logger.info(f"First mentorship keys: {list(mentorships[0].keys())}")
            logger.info(f"First mentorship data: {mentorships[0]}")
        
        # 현재 사용자 정보 - 안전한 방식으로 처리
        user_data_raw = request.session.get('user_data', {})
        user_data = safe_get_user_data(user_data_raw)
        company_id = user_data.get('company_id')
        
        # 사용자 목록 조회
        users_result = fastapi_client.get_users(company_id=company_id)
        all_users = {user['user_id']: user for user in users_result.get('users', [])}
        
        # 디버깅: 사용자 데이터 확인
        logger.info(f"Total users retrieved: {len(all_users)}")
        for user_id, user_data in list(all_users.items())[:3]:  # 처음 3명만 로그
            logger.info(f"User {user_id}: is_active={user_data.get('is_active')}, role={user_data.get('role')}, name={user_data.get('last_name')}{user_data.get('first_name')}")
        
        # 디버깅: 활성 vs 비활성 사용자 수 확인
        active_users = [u for u in all_users.values() if u.get('is_active', False)]
        inactive_users = [u for u in all_users.values() if not u.get('is_active', False)]
        logger.info(f"Active users: {len(active_users)}, Inactive users: {len(inactive_users)}")
        
        # 디버깅: 멘토와 멘티 역할별 활성 사용자 수
        active_mentors = [u for u in active_users if u.get('role') == 'mentor']
        active_mentees = [u for u in active_users if u.get('role') == 'mentee']
        logger.info(f"Active mentors: {len(active_mentors)}, Active mentees: {len(active_mentees)}")
        
        # 디버깅: 멘토쉽 데이터 구조 상세 확인
        logger.info(f"Total mentorships: {len(mentorships)}")
        if mentorships:
            logger.info(f"Sample mentorship keys: {list(mentorships[0].keys())}")
            for i, m in enumerate(mentorships[:2]):  # 처음 2개 멘토쉽만 로그
                logger.info(f"Mentorship {i+1}: id={m.get('id')}, mentorship_id={m.get('mentorship_id')}, is_active={m.get('is_active')}, mentor_id={m.get('mentor_id')}, mentee_id={m.get('mentee_id')}")
        
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
        
        # 멘토쉽에 사용자 정보 추가 및 활성화 상태 계산
        for mentorship in mentorships:
            mentor = all_users.get(mentorship.get('mentor_id'))
            mentee = all_users.get(mentorship.get('mentee_id'))
            
            mentorship['mentor'] = mentor
            mentorship['mentee'] = mentee
            
            # 멘토쉽 ID 키가 없는 경우 id 키로 대체
            if 'mentorship_id' not in mentorship and 'id' in mentorship:
                mentorship['mentorship_id'] = mentorship['id']
            
            # 멘토쉽 활성화 상태: 멘토와 멘티 모두 is_active=True이고 멘토쉽 자체도 is_active=True인 경우에만 활성화
            mentor_active = mentor and mentor.get('is_active', False) if mentor else False
            mentee_active = mentee and mentee.get('is_active', False) if mentee else False
            # is_active 값이 없으면 기본값 True 사용 (DB 기본값과 동일)
            mentorship_active = mentorship.get('is_active', True)
            
            # 디버깅: 멘토쉽 데이터 키 확인
            mentorship_id_display = mentorship.get('mentorship_id', mentorship.get('id'))
            logger.info(f"=== Mentorship {mentorship_id_display} Analysis ===")
            logger.info(f"Mentorship keys: {list(mentorship.keys())}")
            logger.info(f"Raw mentorship.is_active: {mentorship.get('is_active')} (type: {type(mentorship.get('is_active'))})")
            logger.info(f"Processed mentorship_active: {mentorship_active}")
            
            if mentor:
                logger.info(f"Mentor {mentor.get('user_id')} ({mentor.get('last_name')}{mentor.get('first_name')}): is_active={mentor.get('is_active')} → mentor_active={mentor_active}")
            else:
                logger.info(f"Mentor: None → mentor_active={mentor_active}")
                
            if mentee:
                logger.info(f"Mentee {mentee.get('user_id')} ({mentee.get('last_name')}{mentee.get('first_name')}): is_active={mentee.get('is_active')} → mentee_active={mentee_active}")
            else:
                logger.info(f"Mentee: None → mentee_active={mentee_active}")
            
            # 실제 활성화 상태 계산
            mentorship['effective_is_active'] = mentor_active and mentee_active and mentorship_active
            
            logger.info(f"Final calculation: {mentor_active} AND {mentee_active} AND {mentorship_active} = {mentorship['effective_is_active']}")
            logger.info(f"=== End Analysis ===\n")

        # 상태 필터 적용 (effective_is_active 기준)
        if status_filter == 'active':
            mentorships = [m for m in mentorships if m.get('effective_is_active', False)]
        elif status_filter == 'inactive':
            mentorships = [m for m in mentorships if not m.get('effective_is_active', False)]
        
        # 부서 필터 적용
        if department_filter:
            filtered_mentorships = []
            for mentorship in mentorships:
                if (mentorship.get('mentor') and mentorship['mentor'].get('department_id') == int(department_filter)) or \
                   (mentorship.get('mentee') and mentorship['mentee'].get('department_id') == int(department_filter)):
                    filtered_mentorships.append(mentorship)
            mentorships = filtered_mentorships
        
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
        # Django ORM에서 멘토쉽 상세 정보 조회
        from core.models import Mentorship
        mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
        
        # 커리큘럼 ID 조회 (curriculum_title로부터 curriculum_id를 찾기)
        curriculum_id = None
        if mentorship.curriculum_title:
            try:
                curriculums_result = fastapi_client.get_curriculums()
                for curriculum in curriculums_result.get('curriculums', []):
                    if curriculum.get('curriculum_title') == mentorship.curriculum_title:
                        curriculum_id = curriculum.get('curriculum_id')
                        break
            except Exception as e:
                logger.warning(f"Failed to find curriculum_id: {e}")
        
        data = {
            'mentor_id': mentorship.mentor_id,
            'mentee_id': mentorship.mentee_id,
            'curriculum_id': curriculum_id,
            'start_date': mentorship.start_date.isoformat() if mentorship.start_date else None,
            'end_date': mentorship.end_date.isoformat() if mentorship.end_date else None,
            'is_active': mentorship.is_active,
            'curriculum_title': mentorship.curriculum_title,
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Mentorship detail error: {str(e)}")
        return JsonResponse({'error': f'멘토쉽 정보 조회 실패: {str(e)}'}, status=400)
    
@login_required
def mentorship_report(request):
    """
    멘토쉽 평가(report) 조회 API
    Retrieves report text from core.models.Mentorship based on mentorship_id, mentor_id, mentee_id
    """
    mentorship_id = request.GET.get('mentorship_id')
    mentor_id = request.GET.get('mentor_id')
    mentee_id = request.GET.get('mentee_id')
    try:
        from core.models import Mentorship
        mentorship = Mentorship.objects.filter(
            mentorship_id=mentorship_id,
            mentor_id=mentor_id,
            mentee_id=mentee_id
        ).first()
        report_text = mentorship.report if mentorship and mentorship.report else ''
        return JsonResponse({'report': report_text})
    except Exception as e:
        logger.error(f"멘토쉽 리포트 조회 실패: {e}")
        return JsonResponse({'report': ''}, status=500)

@login_required
def mentorship_edit(request, mentorship_id):
    """멘토쉽 수정 (AJAX)"""
    logger.info(f"mentorship_edit called with ID: {mentorship_id}, method: {request.method}")
    
    if not request.user.is_admin:
        logger.warning(f"Non-admin user {request.user} attempted to edit mentorship")
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Mentorship edit data received: {data}")
            
            # Django ORM을 사용해서 멘토쉽 수정
            from core.models import Mentorship
            mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
            logger.info(f"Found mentorship: {mentorship}")
            
            # 데이터 업데이트 및 활성 상태 검증
            if data.get('mentor_id'):
                mentor_id = int(data.get('mentor_id'))
                try:
                    # FastAPI를 통해 멘토 정보 확인
                    mentor = fastapi_client.get_user(mentor_id)
                    if not mentor.get('is_active'):
                        return JsonResponse({'success': False, 'error': '비활성화된 멘토로는 멘토쉽을 수정할 수 없습니다.'})
                    if mentor.get('role') != 'mentor':
                        return JsonResponse({'success': False, 'error': '지정된 사용자가 멘토가 아닙니다.'})
                    mentorship.mentor_id = mentor_id
                    logger.info(f"Updated mentor_id to: {mentorship.mentor_id}")
                except Exception as e:
                    logger.warning(f"Failed to validate mentor: {e}")
                    return JsonResponse({'success': False, 'error': '멘토 정보를 확인할 수 없습니다.'})
            
            if data.get('mentee_id'):
                mentee_id = int(data.get('mentee_id'))
                try:
                    # FastAPI를 통해 멘티 정보 확인
                    mentee = fastapi_client.get_user(mentee_id)
                    if not mentee.get('is_active'):
                        return JsonResponse({'success': False, 'error': '비활성화된 멘티로는 멘토쉽을 수정할 수 없습니다.'})
                    if mentee.get('role') != 'mentee':
                        return JsonResponse({'success': False, 'error': '지정된 사용자가 멘티가 아닙니다.'})
                    mentorship.mentee_id = mentee_id
                    logger.info(f"Updated mentee_id to: {mentorship.mentee_id}")
                except Exception as e:
                    logger.warning(f"Failed to validate mentee: {e}")
                    return JsonResponse({'success': False, 'error': '멘티 정보를 확인할 수 없습니다.'})
            
            if data.get('start_date'):
                mentorship.start_date = data.get('start_date')
                logger.info(f"Updated start_date to: {mentorship.start_date}")
            if data.get('end_date'):
                mentorship.end_date = data.get('end_date') if data.get('end_date') else None
                logger.info(f"Updated end_date to: {mentorship.end_date}")
            
            # curriculum_id로 curriculum_title 조회 및 설정
            if data.get('curriculum_id'):
                try:
                    curriculum_result = fastapi_client.get_curriculum(int(data.get('curriculum_id')))
                    mentorship.curriculum_title = curriculum_result.get('curriculum_title', '')
                    mentorship.total_weeks = curriculum_result.get('total_weeks', 0)
                    logger.info(f"Updated curriculum_title to: {mentorship.curriculum_title}")
                except Exception as e:
                    logger.warning(f"Failed to fetch curriculum info: {e}")
            
            # is_active 상태 업데이트
            mentorship.is_active = data.get('is_active') == True or data.get('is_active') == 'true'
            logger.info(f"Updated is_active to: {mentorship.is_active}")
            
            # 저장
            mentorship.save()
            
            logger.info(f"Mentorship {mentorship_id} updated successfully")
            
            return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Mentorship edit error: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'멘토쉽 수정 실패: {str(e)}'})
    
    logger.warning(f"Invalid request method: {request.method}")
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

@login_required
def mentorship_delete(request, mentorship_id):
    """멘토쉽 삭제 (AJAX)"""
    if not request.user.is_admin:
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
    
    if request.method == 'POST':
        try:
            # Django ORM을 사용해서 멘토쉽 삭제
            from core.models import Mentorship
            mentorship = get_object_or_404(Mentorship, mentorship_id=mentorship_id)
            mentorship.delete()
            
            logger.info(f"Mentorship {mentorship_id} deleted successfully")
            return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Mentorship delete error: {str(e)}")
            return JsonResponse({'success': False, 'error': f'멘토쉽 삭제 실패: {str(e)}'})
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

#endregion 멘토쉽 관리

@login_required
def reset_user_password(request, user_id):
    """사용자 비밀번호 초기화 (AJAX)"""
    if not request.user.is_admin:
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, user_id=user_id)
            # 비밀번호를 "123"으로 초기화
            user.set_password('123')
            user.save()
            
            # 사용자 이름 생성
            # user_name = user.get_full_name() or f"사용자(ID: {user_id})"
            user_name = f"{user.last_name}{user.first_name}"
            
            return JsonResponse({
                'success': True,
                'message': f'{user_name}님의 비밀번호가 "123"으로 초기화되었습니다.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

