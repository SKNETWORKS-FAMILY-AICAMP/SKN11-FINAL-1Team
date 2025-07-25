from django.shortcuts import render
from django.db import models
from django.contrib.auth.decorators import login_required
from core.models import Curriculum, TaskManage, TaskAssign, Mentorship, Curriculum, User
import json
from django.views.decorators.http import require_POST,require_GET
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from core.models import Mentorship, User
from core.utils.fastapi_client import fastapi_client, APIError, AuthenticationError
from django.contrib import messages
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 멘토링 생성 API - FastAPI 프록시
@login_required
@require_POST
@csrf_exempt
def create_mentorship(request):
    """멘토쉽 생성 - FastAPI로 프록시"""
    try:
        data = json.loads(request.body)
        
        # 현재 사용자의 user_id를 요청 데이터에 추가
        data['mentor_id'] = request.user.user_id
        
        # Django의 프록시를 통해 FastAPI로 전달
        from django.http import HttpRequest
        
        # 새로운 HttpRequest 객체 생성하여 프록시로 전달
        proxy_request = HttpRequest()
        proxy_request.method = 'POST'
        proxy_request.META = request.META
        proxy_request._body = json.dumps(data).encode('utf-8')
        proxy_request.GET = request.GET
        
        from core.views import fastapi_proxy
        response = fastapi_proxy(proxy_request, 'mentorship/create')
        
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"[ERROR] 멘토쉽 생성 중 오류: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def mentee_detail(request, user_id):
    try:
        # FastAPI로 멘티 정보 조회
        mentee_info = fastapi_client.get_user(user_id)
        
        # 현재 사용자의 부서와 같은지 확인
        current_user_data = request.session.get('user_data', {})
        current_dept_id = current_user_data.get('department_id')
        
        if mentee_info.get('department_id') != current_dept_id or mentee_info.get('role') != 'mentee':
            return JsonResponse({'error': 'not found'}, status=404)
            
        data = {
            'id': mentee_info.get('user_id'),
            'emp': mentee_info.get('employee_number'),
            'email': mentee_info.get('email'),
            'dept': mentee_info.get('department', {}).get('department_name', '') if mentee_info.get('department') else '',
            'job': mentee_info.get('job_part'),
            'position': mentee_info.get('position'),
            'join': mentee_info.get('join_date'),
            'tag': mentee_info.get('tag'),
            'lastname': mentee_info.get('last_name'),
            'firstname': mentee_info.get('first_name'),
        }
        return JsonResponse(data)
        
    except AuthenticationError:
        return JsonResponse({'error': 'authentication required'}, status=401)
    except APIError:
        return JsonResponse({'error': 'not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def mentees_api(request):
    try:
        # 현재 사용자 정보
        user_data = request.session.get('user_data', {})
        department_id = user_data.get('department_id')
        
        if not department_id:
            return JsonResponse({'mentees': []})
        
        # FastAPI로 멘티 목록 조회
        users_response = fastapi_client.get_users(department_id=department_id)
        all_users = users_response.get('users', [])
        
        # 멘티만 필터링
        mentees = [user for user in all_users if user.get('role') == 'mentee']
        
        mentee_list = [
            {
                'id': m.get('user_id'),
                'emp': m.get('employee_number'),
                'email': m.get('email'),
                'dept': m.get('department', {}).get('department_name', '') if m.get('department') else '',
                'job': m.get('job_part'),
                'position': m.get('position'),
                'join': m.get('join_date'),
                'tag': m.get('tag'),
                'lastname': m.get('last_name'),
                'firstname': m.get('first_name'),
            }
            for m in mentees
        ]
        return JsonResponse({'mentees': mentee_list})
        
    except AuthenticationError:
        return JsonResponse({'mentees': []})
    except Exception as e:
        return JsonResponse({'mentees': [], 'error': str(e)})

# 커리큘럼+Task 저장 API
@require_POST
@login_required
@csrf_exempt
def save_curriculum(request):
    try:
        data = json.loads(request.body)
        user = request.user
        curriculum_id = data.get('curriculum_id')
        with transaction.atomic():
            if curriculum_id:
                # 기존 커리큘럼 수정
                curriculum = Curriculum.objects.get(pk=curriculum_id)
                curriculum.curriculum_title = data.get('curriculum_title')
                curriculum.curriculum_description = data.get('curriculum_description')
                curriculum.week_schedule = data.get('week_schedule')
                curriculum.common = data.get('is_common', False)
                curriculum.total_weeks = max([t['week'] for t in data.get('tasks', [])] or [0])
                curriculum.save()
                # 기존 Task 모두 삭제 후 재생성(덮어쓰기)
                TaskManage.objects.filter(curriculum_id=curriculum).delete()
            else:
                # 새 커리큘럼 생성
                curriculum = Curriculum.objects.create(
                    curriculum_title=data.get('curriculum_title'),
                    curriculum_description=data.get('curriculum_description'),
                    week_schedule=data.get('week_schedule'),
                    department=user.department,
                    common=data.get('is_common', False),
                    total_weeks=max([t['week'] for t in data.get('tasks', [])] or [0])
                )
            # Task 리스트 저장 (order 반영)
            for t in data.get('tasks', []):
                TaskManage.objects.create(
                    curriculum_id=curriculum,
                    title=t.get('title'),
                    description=t.get('description'),
                    guideline=t.get('guideline'),
                    week=t.get('week'),
                    order=t.get('order'),
                    period=t.get('period') or None,
                    priority=t.get('priority')
                )
        return JsonResponse({'success': True, 'curriculum_id': curriculum.pk})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def mentor(request):
    """멘토 대시보드 - FastAPI 전용"""
    if not request.user.is_authenticated:
        messages.error(request, '로그인이 필요합니다.')
        from django.shortcuts import redirect
        return redirect('account:login')
    
    # FastAPI를 통해서만 데이터를 가져오므로, 템플릿만 렌더링
    context = {
        'user': request.user,  # JavaScript에서 사용할 사용자 정보
        'user_id': request.user.user_id,  # 명시적으로 user_id 전달
        'FASTAPI_BASE_URL': os.getenv('FASTAPI_BASE_URL', 'http://localhost:8001')  # FastAPI URL 추가
    }
    
    return render(request, 'mentor/mentor.html', context)

@login_required
def add_template(request, curriculum_id=None):
    """커리큘럼 생성/편집 페이지"""
    context = {}
    
    # 편집 모드인 경우
    if curriculum_id:
        try:
            from core.models import Curriculum, TaskManage
            import json
            
            curriculum = Curriculum.objects.get(pk=curriculum_id)
            tasks = TaskManage.objects.filter(curriculum_id=curriculum).order_by('week', 'order')
            
            # Task 정보도 모두 넘김
            task_list = [
                {
                    'week': t.week,
                    'title': t.title,
                    'guideline': t.guideline,
                    'description': t.description,
                    'period': str(t.period) if t.period is not None else '',
                    'priority': t.priority
                }
                for t in tasks
            ]
            
            curriculum_dict = {
                'curriculum_id': curriculum.pk,
                'curriculum_title': curriculum.curriculum_title,
                'curriculum_description': curriculum.curriculum_description,
                'week_schedule': curriculum.week_schedule,
                'is_common': curriculum.common,
            }
            
            context = {
                'edit_mode': True,
                'curriculum': json.dumps(curriculum_dict, ensure_ascii=False),
                'tasks_json': json.dumps(task_list, ensure_ascii=False),
                'FASTAPI_BASE_URL': os.getenv('FASTAPI_BASE_URL', 'http://localhost:8001')
            }
        except Curriculum.DoesNotExist:
            from django.contrib import messages
            messages.error(request, '존재하지 않는 커리큘럼입니다.')
            from django.shortcuts import redirect
            return redirect('mentor:manage_template')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'커리큘럼 정보 조회 중 오류가 발생했습니다: {str(e)}')
            from django.shortcuts import redirect
            return redirect('mentor:manage_template')
    
    return render(request, 'mentor/add_template.html', context)

@login_required
def manage_mentee(request):
    try:
        user_data = request.session.get('user_data', {})
        company_id = user_data.get('company_id')
        department_id = user_data.get('department_id')
        
        # 같은 부서의 멘티 중 is_active=True인 멘티만 필터링
        mentees_result = fastapi_client.get_users(
            department_id=department_id,  # 부서 필터링
            role='mentee',                # 멘티만
            is_active=True               # 활성 사용자만
        )
        mentees = mentees_result.get('users', [])
        
        # 부서 커리큘럼 목록 (공용+부서별 커리큘럼 한 번에 조회)
        curriculums_result = fastapi_client.get_curriculums(department_id=department_id)
        curriculums = curriculums_result.get('curriculums', [])
        
        return render(request, 'mentor/manage_mentee.html', {
            'mentees': mentees,
            'curriculums': curriculums,
        })
        
    except (AuthenticationError, APIError) as e:
        messages.error(request, f'멘티 관리 정보 조회 중 오류가 발생했습니다: {str(e)}')
        
        # FastAPI 실패 시 Django ORM으로 폴백
        try:
            if department_id:
                mentees = User.objects.filter(
                    department_id=department_id,  # 멘토와 같은 부서
                    role='mentee',                # 멘티만
                    is_active=True               # 활성 사용자만
                ).select_related('company', 'department')
                
                # 폴백 시에도 커리큘럼 조회 (부서별 + 공용)
                from core.models import Curriculum
                dept_curriculums = Curriculum.objects.filter(department_id=department_id)
                common_curriculums = Curriculum.objects.filter(common=True)
                all_curriculums = list(common_curriculums) + list(dept_curriculums)
            else:
                mentees = []
                all_curriculums = []
                
            return render(request, 'mentor/manage_mentee.html', {
                'mentees': mentees,
                'curriculums': all_curriculums,
            })
        except Exception as fallback_error:
            messages.error(request, f'데이터 조회 중 오류가 발생했습니다: {str(fallback_error)}')
            return render(request, 'mentor/manage_mentee.html', {
                'mentees': [],
                'curriculums': [],
            })

@login_required
def manage_template(request):
    user = request.user
    curriculum_tasks = {}
    
    try:
        # FastAPI로 필터링된 커리큘럼 조회 (공통 커리큘럼 + 사용자 부서 커리큘럼)
        result = fastapi_client.get_filtered_curriculums(department_id=user.department.department_id if user.department else None)
        curriculums_data = result.get('curriculums', [])
        
        # 태스크 정보는 현재 사용되지 않으므로 빈 딕셔너리로 설정
        # TODO: 필요시 FastAPI에 /curriculum/{id}/tasks 엔드포인트 추가 후 활성화
        # for curriculum in curriculums_data:
        #     curriculum_id = curriculum['curriculum_id']
        #     try:
        #         tasks_result = fastapi_client.get_curriculum_tasks(curriculum_id)
        #         curriculum_tasks[curriculum_id] = tasks_result
        #     except Exception as e:
        #         print(f"커리큘럼 {curriculum_id} 태스크 조회 오류: {e}")
        #         curriculum_tasks[curriculum_id] = []
        
        # curriculums_data를 정렬 (공통 커리큘럼 우선, 그다음 제목순)
        curriculums_data.sort(key=lambda x: (not x.get('common', False), x.get('curriculum_title', '')))
        
        return render(request, 'mentor/manage_template.html', {
            'curriculums': curriculums_data,
            'curriculum_tasks_json': json.dumps(curriculum_tasks, ensure_ascii=False),
        })
        
    except Exception as e:
        print(f"FastAPI 커리큘럼 조회 오류: {e}")
        # Fallback to Django ORM
        curriculums = Curriculum.objects.filter(
            models.Q(common=True) | models.Q(department=user.department)
        ).order_by('-common', 'curriculum_title')
        
        for c in curriculums:
            tasks = TaskManage.objects.filter(curriculum_id=c).order_by('week', 'order')
            curriculum_tasks[c.pk] = [
                {
                    'week': t.week,
                    'title': t.title,
                    'guideline': t.guideline,
                    'description': t.description,
                    'period': str(t.period) if t.period is not None else '',
                    'priority': t.priority
                }
                for t in tasks
            ]
            
        return render(request, 'mentor/manage_template.html', {
            'curriculums': curriculums,
            'curriculum_tasks_json': json.dumps(curriculum_tasks, ensure_ascii=False),
        })

@require_POST
@login_required
def clone_template(request, curriculum_id):
    try:
        with transaction.atomic():
            orig = Curriculum.objects.get(pk=curriculum_id)
            # 새 커리큘럼 생성 (부서는 로그인한 user의 부서로)
            new_curriculum = Curriculum.objects.create(
                curriculum_description=orig.curriculum_description,
                curriculum_title=orig.curriculum_title + ' (복제)',
                department=request.user.department,  # 여기만 변경
                common=False,
                total_weeks=orig.total_weeks,
                week_schedule=orig.week_schedule,
            )
            # 세부 Task 모두 복제
            orig_tasks = TaskManage.objects.filter(curriculum_id=orig)
            for t in orig_tasks:
                TaskManage.objects.create(
                    curriculum_id=new_curriculum,
                    title=t.title,
                    description=t.description,
                    guideline=t.guideline,
                    week=t.week,
                    order=t.order,
                    period=t.period,
                    priority=t.priority
                )
        return JsonResponse({'success': True, 'new_id': new_curriculum.pk})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
@login_required
def delete_template(request, curriculum_id):
    try:
        with transaction.atomic():
            cur = Curriculum.objects.get(pk=curriculum_id)
            # 본인 부서/공용만 삭제 가능 (권한 체크)
            if not (cur.department == request.user.department or cur.common):
                return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
            # 관련 TaskManage도 함께 삭제됨 (on_delete=models.CASCADE)
            cur.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def edit_template(request, curriculum_id):
    from core.models import Curriculum, TaskManage
    import json
    curriculum = Curriculum.objects.get(pk=curriculum_id)
    tasks = TaskManage.objects.filter(curriculum_id=curriculum).order_by('week', 'order')
    # Task 정보도 모두 넘김
    task_list = [
        {
            'week': t.week,
            'title': t.title,
            'guideline': t.guideline,
            'description': t.description,
            'period': str(t.period) if t.period is not None else '',
            'priority': t.priority
        }
        for t in tasks
    ]
    curriculum_dict = {
        'curriculum_id': curriculum.pk,
        'curriculum_title': curriculum.curriculum_title,
        'curriculum_description': curriculum.curriculum_description,
        'week_schedule': curriculum.week_schedule,
        'is_common': curriculum.common,
        # 필요시 추가 필드
    }
    return render(request, 'mentor/add_template.html', {
        'edit_mode': True,
        'curriculum': json.dumps(curriculum_dict, ensure_ascii=False),
        'tasks_json': json.dumps(task_list, ensure_ascii=False),
    })


@login_required
@require_POST
@csrf_exempt
def clone_curriculum(request, curriculum_id):
    """커리큘럼 복제"""
    try:
        user = request.user
        
        # 원본 커리큘럼 조회
        try:
            original = fastapi_client.get_curriculum(curriculum_id)
        except Exception as e:
            print(f"FastAPI에서 커리큘럼 조회 실패: {e}")
            # 백업으로 Django에서 조회
            original = Curriculum.objects.get(pk=curriculum_id)
            original = {
                'curriculum_id': original.pk,
                'curriculum_title': original.curriculum_title,
                'curriculum_description': original.curriculum_description,
                'week_schedule': original.week_schedule,
                'common': original.common,
                'department_id': original.department_id,
            }
        
        # 복제본 생성 데이터 준비
        clone_data = {
            'curriculum_title': f"{original['curriculum_title']} (복사본)",
            'curriculum_description': original.get('curriculum_description', ''),
            'week_schedule': original.get('week_schedule', ''),
            'common': False,  # 복제본은 일반 커리큘럼으로 설정
            'department_id': user.department_id
        }
        
        # FastAPI로 커리큘럼 생성
        try:
            new_curriculum = fastapi_client.create_curriculum(clone_data)
            new_curriculum_id = new_curriculum.get('curriculum_id')
        except Exception as e:
            print(f"FastAPI에서 커리큘럼 생성 실패: {e}")
            # Django 백업으로 생성
            with transaction.atomic():
                new_curriculum = Curriculum.objects.create(
                    curriculum_title=clone_data['curriculum_title'],
                    curriculum_description=clone_data['curriculum_description'],
                    week_schedule=clone_data['week_schedule'],
                    common=clone_data['common'],
                    department_id=clone_data['department_id']
                )
                new_curriculum_id = new_curriculum.pk
        
        # 원본의 태스크들도 복제
        try:
            original_tasks = fastapi_client.get_curriculum_tasks(curriculum_id)
            if original_tasks:
                for task in original_tasks:
                    task_data = {
                        'curriculum_id': new_curriculum_id,
                        'week': task.get('week', 1),
                        'title': task.get('title', ''),
                        'guideline': task.get('guideline', ''),
                        'description': task.get('description', ''),
                        'period': task.get('period', 7),
                        'priority': task.get('priority', 'medium')
                    }
                    try:
                        fastapi_client.create_task(task_data)
                    except Exception as task_error:
                        print(f"태스크 복제 실패: {task_error}")
                        # Django 백업
                        TaskManage.objects.create(
                            curriculum_id=new_curriculum_id,
                            week=task_data['week'],
                            title=task_data['title'],
                            guideline=task_data['guideline'],
                            description=task_data['description'],
                            period=task_data['period'],
                            priority=task_data['priority']
                        )
        except Exception as e:
            print(f"태스크 복제 중 오류: {e}")
        
        return JsonResponse({'success': True, 'message': '커리큘럼이 성공적으로 복제되었습니다.'})
        
    except Exception as e:
        print(f"커리큘럼 복제 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
def delete_curriculum(request, curriculum_id):
    """커리큘럼 삭제 - DELETE 메소드만 허용"""
    print(f"[DEBUG] 삭제 요청 - 커리큘럼 ID: {curriculum_id}, 메소드: {request.method}")
    
    if request.method != 'DELETE':
        print(f"[ERROR] 잘못된 메소드: {request.method}")
        return JsonResponse({'success': False, 'error': 'DELETE 메소드만 허용됩니다.'}, status=405)
        
    try:
        print(f"[INFO] 커리큘럼 삭제 시작: {curriculum_id}")
        
        # 먼저 해당 커리큘럼이 사용 중인 멘토쉽이 있는지 확인
        try:
            print("[INFO] 멘토쉽 사용 여부 확인 중...")
            mentorships = fastapi_client.get_mentorships_by_curriculum(curriculum_id)
            print(f"[DEBUG] 멘토쉽 조회 결과: {mentorships}")
            
            if mentorships and len(mentorships) > 0:
                print(f"[WARNING] 사용 중인 멘토쉽이 있음: {len(mentorships)}개")
                return JsonResponse({
                    'success': False, 
                    'error': '이 커리큘럼을 사용 중인 멘토쉽이 있어 삭제할 수 없습니다.'
                }, status=400)
        except Exception as e:
            print(f"[ERROR] FastAPI 멘토쉽 확인 실패: {e}")
            # Django 백업으로 확인
            try:
                django_mentorships = Mentorship.objects.filter(curriculum_id=curriculum_id)
                print(f"[DEBUG] Django 멘토쉽 조회: {django_mentorships.count()}개")
                
                if django_mentorships.exists():
                    print("[WARNING] Django에서 사용 중인 멘토쉽 발견")
                    return JsonResponse({
                        'success': False, 
                        'error': '이 커리큘럼을 사용 중인 멘토쉽이 있어 삭제할 수 없습니다.'
                    }, status=400)
            except Exception as django_error:
                print(f"[ERROR] Django 멘토쉽 확인도 실패: {django_error}")
        
        print("[INFO] 멘토쉽 사용 확인 완료 - 삭제 가능")
        
        # 커리큘럼 삭제
        try:
            print("[INFO] FastAPI로 커리큘럼 삭제 시도...")
            result = fastapi_client.delete_curriculum(curriculum_id)
            print(f"[SUCCESS] FastAPI 삭제 성공: {result}")
        except Exception as e:
            print(f"[ERROR] FastAPI에서 커리큘럼 삭제 실패: {e}")
            print("[INFO] Django 백업으로 삭제 시도...")
            
            # Django 백업으로 삭제
            with transaction.atomic():
                # 먼저 관련 태스크들 삭제
                deleted_tasks = TaskManage.objects.filter(curriculum_id=curriculum_id).delete()
                print(f"[INFO] 삭제된 태스크 수: {deleted_tasks[0] if deleted_tasks[0] else 0}")
                
                # 커리큘럼 삭제
                deleted_curriculum = Curriculum.objects.filter(pk=curriculum_id).delete()
                print(f"[INFO] 삭제된 커리큘럼 수: {deleted_curriculum[0] if deleted_curriculum[0] else 0}")
                
                if deleted_curriculum[0] == 0:
                    raise Exception(f"커리큘럼 ID {curriculum_id}를 찾을 수 없습니다.")
        
        print(f"[SUCCESS] 커리큘럼 {curriculum_id} 삭제 완료")
        return JsonResponse({'success': True, 'message': '커리큘럼이 성공적으로 삭제되었습니다.'})
        
    except Exception as e:
        print(f"[ERROR] 커리큘럼 삭제 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}, status=500)
