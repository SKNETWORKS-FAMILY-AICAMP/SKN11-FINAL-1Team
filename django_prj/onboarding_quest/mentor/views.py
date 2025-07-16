<<<<<<< Updated upstream
from django.shortcuts import render

def mentor(request):
    return render(request, 'mentor/mentor.html')

def add_template(request):
    return render(request, 'mentor/add_template.html')

def manage_mentee(request):
    return render(request, 'mentor/manage_mentee.html')
=======
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from core.models import User, Mentorship, TaskAssign, Curriculum, TaskManage, Department
from common.api_client import get_fastapi_client
from datetime import date, timedelta
import json
import logging
import requests

logger = logging.getLogger(__name__)

@login_required
def mentor(request):
    """멘토 메인 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 현재 멘토가 담당하는 멘토십 목록 가져오기
    mentorships = Mentorship.objects.filter(
        mentor_id=user.user_id,
        is_active=True
    ).order_by('-start_date')
    
    # 멘티 카드 데이터 생성
    mentee_cards = []
    for mentorship in mentorships:
        try:
            # 멘티 정보 가져오기
            mentee = User.objects.get(user_id=mentorship.mentee_id)
            
            # 진척도 계산
            total_tasks = TaskAssign.objects.filter(mentorship_id=mentorship.mentorship_id).count()
            completed_tasks = TaskAssign.objects.filter(
                mentorship_id=mentorship.mentorship_id,
                status='완료'
            ).count()
            
            progress = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
            
            # D-day 계산
            if mentorship.end_date:
                dday = calculate_dday(mentorship.end_date)
            else:
                dday = 'D-?'
            
            # 멘티 태그 생성 (부서, 직급 등)
            tags = []
            if mentee.department:
                tags.append(mentee.department.department_name)
            if mentee.position:
                tags.append(mentee.position)
            
            mentee_card = {
                'mentorship_id': mentorship.mentorship_id,
                'name': f"{mentee.last_name}{mentee.first_name}",
                'email': mentee.email,
                'curriculum_title': mentorship.curriculum_title,
                'total_weeks': mentorship.total_weeks,
                'progress': progress,
                'dday': dday,
                'tags': tags,
                'start_date': mentorship.start_date,
                'end_date': mentorship.end_date,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks
            }
            mentee_cards.append(mentee_card)
            
        except User.DoesNotExist:
            logger.warning(f"멘티 사용자를 찾을 수 없습니다: {mentorship.mentee_id}")
            continue
    
    context = {
        'user': request.user,
        'mentee_cards': mentee_cards,
        'total_mentees': len(mentee_cards),
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '멘토 대시보드'
    }
    return render(request, 'mentor/mentor.html', context)

@login_required
def manage_mentee(request):
    """멘티 관리 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 현재 멘토가 담당하는 멘토십 목록 가져오기
    mentorships = Mentorship.objects.filter(
        mentor_id=user.user_id,
        is_active=True
    ).order_by('-start_date')
    
    # 멘티 상세 정보 가져오기
    mentee_details = []
    for mentorship in mentorships:
        try:
            mentee = User.objects.get(user_id=mentorship.mentee_id)
            
            # 과제 통계
            tasks = TaskAssign.objects.filter(mentorship_id=mentorship.mentorship_id)
            task_stats = {
                'total': tasks.count(),
                'todo': tasks.filter(status='진행 전').count(),
                'in_progress': tasks.filter(status='진행 중').count(),
                'review': tasks.filter(status='검토 요청').count(),
                'completed': tasks.filter(status='완료').count()
            }
            
            mentee_detail = {
                'mentorship_id': mentorship.mentorship_id,
                'mentee': mentee,
                'mentorship': mentorship,
                'task_stats': task_stats,
                'progress': int((task_stats['completed'] / task_stats['total'] * 100)) if task_stats['total'] > 0 else 0
            }
            mentee_details.append(mentee_detail)
            
        except User.DoesNotExist:
            continue
    
    # 멘토쉽 생성을 위한 멘티 목록 가져오기 (현재 멘토쉽이 없는 역할이 'mentee'인 사용자들)
    existing_mentee_ids = Mentorship.objects.filter(is_active=True).values_list('mentee_id', flat=True)
    mentees = User.objects.filter(
        role='mentee', 
        is_active=True
    ).exclude(user_id__in=existing_mentee_ids).order_by('last_name', 'first_name')
    
    # 사용 가능한 커리큘럼 목록 가져오기
    curriculums = []
    if user.department:
        curriculums = Curriculum.objects.filter(
            Q(department=user.department) | Q(common=True)
        ).order_by('-curriculum_id')
    else:
        curriculums = Curriculum.objects.filter(common=True).order_by('-curriculum_id')
    
    context = {
        'user': request.user,
        'mentee_details': mentee_details,
        'mentees': mentees,  # 멘토쉽 생성을 위한 멘티 목록 추가
        'curriculums': curriculums,  # 커리큘럼 목록 추가
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '멘티 관리'
    }
    return render(request, 'mentor/manage_mentee.html', context)
>>>>>>> Stashed changes

def manage_template(request):
<<<<<<< Updated upstream
    return render(request, 'mentor/manage_template.html')
=======
    """템플릿 관리 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 사용자 부서의 커리큘럼 목록 가져오기
    if user.department:
        curriculums = Curriculum.objects.filter(
            Q(department=user.department) | Q(common=True)
        ).order_by('-curriculum_id')
    else:
        curriculums = Curriculum.objects.filter(common=True).order_by('-curriculum_id')
    
    # 커리큘럼 작업 데이터 생성 (JavaScript용)
    curriculum_tasks_data = {}
    for curriculum in curriculums:
        tasks = TaskManage.objects.filter(curriculum_id=curriculum.curriculum_id).order_by('week', 'order')
        curriculum_tasks_data[curriculum.curriculum_id] = [
            {
                'week': task.week,
                'title': task.title,
                'description': task.description,
                'guideline': task.guideline,
                'period': task.period,
                'priority': task.priority,
                'order': task.order
            } for task in tasks
        ]
    
    context = {
        'user': request.user,
        'curriculums': curriculums,  # 템플릿에서 사용하는 변수명으로 수정
        'curriculum_tasks_json': json.dumps(curriculum_tasks_data, ensure_ascii=False),
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '템플릿 관리'
    }
    return render(request, 'mentor/manage_template.html', context)

@login_required
def add_template(request):
    """템플릿 추가 페이지 - 실제 데이터베이스 데이터 가져오기"""
    # 부서 목록 가져오기
    departments = Department.objects.filter(is_active=True).order_by('department_name')
    
    # 기존 커리큘럼 목록 (복제용)
    existing_curriculums = Curriculum.objects.all().order_by('-curriculum_id')
    
    context = {
        'user': request.user,
        'departments': departments,
        'existing_curriculums': existing_curriculums,
        'tasks_json': '[]',  # 빈 배열로 초기화
        'curriculum_json': 'null',  # null로 초기화
        'is_edit': False,
        'edit_mode': False,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '템플릿 추가'
    }
    return render(request, 'mentor/add_template.html', context)

@login_required
def mentee_detail(request, user_id):
    """멘티 상세 페이지 - 실제 데이터베이스 데이터 가져오기"""
    try:
        mentee = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return redirect('mentor:mentor')
    
    # 현재 멘토와 멘티 간의 멘토십 확인
    mentorship = Mentorship.objects.filter(
        mentor_id=request.user.user_id,
        mentee_id=user_id,
        is_active=True
    ).first()
    
    if not mentorship:
        return redirect('mentor:mentor')
    
    # 과제 목록 가져오기
    tasks = TaskAssign.objects.filter(
        mentorship_id=mentorship.mentorship_id
    ).order_by('week', 'order')
    
    # 과제 통계
    task_stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status='진행 전').count(),
        'in_progress': tasks.filter(status='진행 중').count(),
        'review': tasks.filter(status='검토 요청').count(),
        'completed': tasks.filter(status='완료').count()
    }
    
    context = {
        'user': request.user,
        'mentee': mentee,
        'mentorship': mentorship,
        'tasks': tasks,
        'task_stats': task_stats,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': f'멘티 상세 - {mentee.get_full_name()}'
    }
    return render(request, 'mentor/mentee_detail.html', context)

# 헬퍼 함수들
def calculate_dday(end_date):
    """D-day 계산"""
    if not end_date:
        return 'D-?'
    
    today = date.today()
    delta = end_date - today
    
    if delta.days > 0:
        return f'D-{delta.days}'
    elif delta.days == 0:
        return 'D-Day'
    else:
        return f'D+{abs(delta.days)}'

# FastAPI 프록시 뷰들 (필요시)
@login_required
def mentees_api(request):
    """멘티 목록 API - FastAPI로 프록시"""
    try:
        import requests
        
        # 현재 사용자 정보를 헤더에 추가 (임시로 간단한 방식)
        response = requests.get(
            f'{settings.FASTAPI_BASE_URL}/api/v1/mentor/mentees',
            headers={
                'Authorization': f'Bearer {request.user.email}',  # 임시 토큰 방식
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False)
        else:
            return JsonResponse({'error': '멘티 목록을 가져올 수 없습니다.'}, status=response.status_code)
            
    except Exception as e:
        logger.error(f"멘티 목록 API 에러: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def save_curriculum(request):
    """커리큘럼 저장 API - FastAPI 호출"""
    if request.method == 'POST':
        try:
            # 요청 데이터 파싱
            data = json.loads(request.body)
            
            # 사용자 정보 추가 (권한 체크용)
            data['user_id'] = request.user.user_id
            data['department_id'] = request.user.department.department_id if request.user.department else None
            
            # FastAPI 서버 URL 설정
            fastapi_url = "http://localhost:8003/api/v1/mentor/save_curriculum"
            
            # FastAPI 서버로 요청 보내기
            response = requests.post(fastapi_url, json=data)
            
            if response.status_code == 200:
                return JsonResponse(response.json())
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'FastAPI 서버에서 커리큘럼 저장 실패'
                }, status=response.status_code)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"커리큘럼 저장 API 에러: {e}")
            return JsonResponse({
                'success': False,
                'message': f'FastAPI 서버 연결 오류: {str(e)}'
            }, status=500)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 JSON 형식입니다.'
            }, status=400)
        except Exception as e:
            logger.error(f"커리큘럼 저장 에러: {e}")
            return JsonResponse({
                'success': False,
                'message': f'커리큘럼 저장 중 오류가 발생했습니다: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'POST 요청만 허용'}, status=405)

# 템플릿 및 멘토쉽 관리 CRUD 함수들
@login_required
def clone_template(request, curriculum_id):
    """템플릿 복제"""
    if request.method == 'POST':
        try:
            original_curriculum = Curriculum.objects.get(curriculum_id=curriculum_id)
            
            # 새로운 커리큘럼 생성
            new_curriculum = Curriculum.objects.create(
                curriculum_title=f"{original_curriculum.curriculum_title} (복제)",
                curriculum_description=original_curriculum.curriculum_description,
                department=request.user.department,
                common=False,
                total_weeks=original_curriculum.total_weeks,
                week_schedule=original_curriculum.week_schedule
            )
            
            # 기존 과제들도 복제
            original_tasks = TaskManage.objects.filter(curriculum_id=original_curriculum)
            for task in original_tasks:
                TaskManage.objects.create(
                    curriculum_id=new_curriculum,
                    title=task.title,
                    description=task.description,
                    guideline=task.guideline,
                    week=task.week,
                    order=task.order,
                    period=task.period,
                    priority=task.priority
                )
            
            return JsonResponse({
                'success': True,
                'message': f'커리큘럼 "{original_curriculum.curriculum_title}"이(가) 성공적으로 복제되었습니다.'
            })
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '커리큘럼을 찾을 수 없습니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'커리큘럼 복제 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'POST 요청만 허용됩니다.'
    })

@login_required
def delete_template(request, curriculum_id):
    """템플릿 삭제"""
    if request.method == 'POST':
        try:
            curriculum = Curriculum.objects.get(curriculum_id=curriculum_id)
            curriculum_title = curriculum.curriculum_title
            
            # 사용 중인 멘토쉽이 있는지 확인
            mentorship_count = Mentorship.objects.filter(curriculum_title=curriculum_title).count()
            if mentorship_count > 0:
                return JsonResponse({
                    'success': False,
                    'message': f'커리큘럼 "{curriculum_title}"은(는) 멘토쉽에서 사용 중이어서 삭제할 수 없습니다.'
                })
            
            # 관련 과제들도 삭제
            TaskManage.objects.filter(curriculum_id=curriculum).delete()
            curriculum.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'커리큘럼 "{curriculum_title}"이(가) 성공적으로 삭제되었습니다.'
            })
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '커리큘럼을 찾을 수 없습니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'커리큘럼 삭제 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'POST 요청만 허용됩니다.'
    })

@login_required
def edit_template(request, curriculum_id):
    """템플릿 수정"""
    if request.method == 'GET':
        # 수정 페이지로 이동 (add_template 페이지 재사용)
        try:
            curriculum = Curriculum.objects.get(curriculum_id=curriculum_id)
            departments = Department.objects.filter(is_active=True).order_by('department_name')
            
            # 커리큘럼 과제 목록 가져오기
            tasks = TaskManage.objects.filter(curriculum_id=curriculum).order_by('week', 'order')
            
            # JavaScript용 tasks_json 생성
            tasks_json = []
            for task in tasks:
                tasks_json.append({
                    'title': task.title,
                    'description': task.description,
                    'guideline': task.guideline,
                    'week': task.week,
                    'order': task.order,
                    'period': task.period,
                    'priority': task.priority
                })
            
            # JavaScript용 curriculum_json 생성
            curriculum_json = {
                'curriculum_id': curriculum.curriculum_id,
                'curriculum_title': curriculum.curriculum_title,
                'curriculum_description': curriculum.curriculum_description,
                'week_schedule': curriculum.week_schedule,
                'total_weeks': curriculum.total_weeks,
                'common': curriculum.common,
                'department_id': curriculum.department.department_id if curriculum.department else None
            }
            
            context = {
                'user': request.user,
                'curriculum': curriculum,
                'departments': departments,
                'tasks': tasks,
                'tasks_json': json.dumps(tasks_json, ensure_ascii=False),
                'curriculum_json': json.dumps(curriculum_json, ensure_ascii=False),
                'is_edit': True,
                'edit_mode': True,
                'fastapi_url': settings.FASTAPI_BASE_URL,
                'title': f'커리큘럼 수정 - {curriculum.curriculum_title}'
            }
            return render(request, 'mentor/add_template.html', context)
            
        except Curriculum.DoesNotExist:
            messages.error(request, '커리큘럼을 찾을 수 없습니다.')
            return redirect('mentor:manage_template')
    
    elif request.method == 'POST':
        # 커리큘럼 정보 업데이트
        try:
            curriculum = Curriculum.objects.get(curriculum_id=curriculum_id)
            
            curriculum.curriculum_title = request.POST.get('curriculum_title', curriculum.curriculum_title)
            curriculum.curriculum_description = request.POST.get('curriculum_description', curriculum.curriculum_description)
            curriculum.total_weeks = int(request.POST.get('total_weeks', curriculum.total_weeks))
            curriculum.week_schedule = request.POST.get('week_schedule', curriculum.week_schedule)
            
            # 부서 설정
            department_id = request.POST.get('department')
            if department_id:
                curriculum.department = Department.objects.get(department_id=department_id)
            
            # 공통 설정 업데이트
            curriculum.common = request.POST.get('common') == 'on'
            curriculum.save()
            
            return JsonResponse({
                'success': True,
                'message': f'커리큘럼 "{curriculum.curriculum_title}"이(가) 성공적으로 수정되었습니다.'
            })
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '커리큘럼을 찾을 수 없습니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'커리큘럼 수정 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': '지원되지 않는 요청입니다.'
    })

@login_required
@csrf_exempt
def create_mentorship(request):
    """멘토쉽 생성 API - FastAPI 호출"""
    if request.method == 'POST':
        try:
            # 요청 데이터 파싱
            data = json.loads(request.body)
            
            # 필수 필드 확인
            if not data.get('mentee_id') or not data.get('curriculum_id'):
                return JsonResponse({
                    'success': False,
                    'message': '멘티 ID와 커리큘럼 ID가 필요합니다.'
                }, status=400)
            
            # 멘토 정보 추가
            data['mentor_id'] = request.user.user_id
            
            # 날짜 정보 추가 (기본값 설정)
            from datetime import datetime, timedelta
            if not data.get('start_date'):
                data['start_date'] = datetime.now().strftime('%Y-%m-%d')
            if not data.get('end_date'):
                # 기본적으로 12주 후로 설정
                end_date = datetime.now() + timedelta(weeks=12)
                data['end_date'] = end_date.strftime('%Y-%m-%d')
            
            # FastAPI 서버 URL 설정
            fastapi_url = "http://localhost:8003/api/v1/mentor/create_mentorship"
            
            # FastAPI 서버로 요청 보내기
            response = requests.post(fastapi_url, json=data)
            
            if response.status_code == 200:
                return JsonResponse(response.json())
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'FastAPI 서버에서 멘토쉽 생성 실패'
                }, status=response.status_code)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"멘토쉽 생성 API 에러: {e}")
            return JsonResponse({
                'success': False,
                'message': f'FastAPI 서버 연결 오류: {str(e)}'
            }, status=500)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 JSON 형식입니다.'
            }, status=400)
        except Exception as e:
            logger.error(f"멘토쉽 생성 에러: {e}")
            return JsonResponse({
                'success': False,
                'message': f'멘토쉽 생성 중 오류가 발생했습니다: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'POST 요청만 허용'}, status=405)
>>>>>>> Stashed changes
