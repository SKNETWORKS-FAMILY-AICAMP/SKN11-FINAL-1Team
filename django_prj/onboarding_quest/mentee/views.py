<<<<<<< Updated upstream
from django.shortcuts import render
=======
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
from core.models import User, TaskAssign, Mentorship, Memo
from common.api_client import get_fastapi_client
from datetime import date, timedelta
import json
import logging

logger = logging.getLogger(__name__)
>>>>>>> Stashed changes

@login_required
def mentee(request):
<<<<<<< Updated upstream
    return render(request, 'mentee/mentee.html')

def task_list(request):
    return render(request, 'mentee/task_list.html')
=======
    """멘티 메인 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 현재 사용자의 멘토십 정보 가져오기
    try:
        mentorship = Mentorship.objects.filter(mentee_id=user.user_id, is_active=True).first()
    except Exception as e:
        logger.error(f"멘토십 조회 오류: {e}")
        mentorship = None
    
    # 과제 목록 가져오기
    tasks = []
    if mentorship:
        tasks = TaskAssign.objects.filter(mentorship_id=mentorship.mentorship_id).order_by('week', 'order')
    
    # 과제를 상태별로 분류
    todo_tasks = []
    in_progress_tasks = []
    review_tasks = []
    completed_tasks = []
    
    for task in tasks:
        task_data = {
            'id': task.task_assign_id,
            'title': task.title or '제목 없음',
            'description': task.description or '설명 없음',
            'week': task.week,
            'priority': task.priority or '중',
            'status': task.status or '진행 전',
            'start_date': task.start_date,
            'end_date': task.end_date,
            'exp': calculate_exp_by_priority(task.priority),
            'dday': calculate_dday(task.end_date) if task.end_date else 'D-?'
        }
        
        if task.status == '진행 전':
            todo_tasks.append(task_data)
        elif task.status == '진행 중':
            in_progress_tasks.append(task_data)
        elif task.status == '검토 요청':
            review_tasks.append(task_data)
        elif task.status == '완료':
            completed_tasks.append(task_data)
    
    # 최근 활동 가져오기
    recent_activities = []
    if mentorship:
        recent_memos = Memo.objects.filter(
            task_assign__mentorship_id=mentorship.mentorship_id,
            user=user
        ).order_by('-create_date')[:5]
        
        for memo in recent_memos:
            recent_activities.append({
                'action': memo.comment,
                'date': memo.create_date,
                'task_title': memo.task_assign.title
            })
    
    # 경험치 계산
    total_exp = sum(task['exp'] for task in completed_tasks)
    level = calculate_level(total_exp)
    current_level_exp = total_exp % 300
    max_exp_for_level = 300
    
    context = {
        'user': request.user,
        'mentorship': mentorship,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'review_tasks': review_tasks,
        'completed_tasks': completed_tasks,
        'recent_activities': recent_activities,
        'total_exp': total_exp,
        'level': level,
        'current_level_exp': current_level_exp,
        'max_exp_for_level': max_exp_for_level,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '멘티 대시보드'
    }
    return render(request, 'mentee/mentee.html', context)

@login_required
def task_list(request):
    """과제 목록 페이지 - 실제 데이터베이스 데이터 가져오기"""
    mentorship_id = request.GET.get('mentorship_id')
    user = request.user
    
    # 멘토십 정보 확인
    mentorship = None
    if mentorship_id:
        try:
            mentorship = Mentorship.objects.get(mentorship_id=mentorship_id)
        except Mentorship.DoesNotExist:
            pass
    
    # 멘토십이 없으면 현재 사용자의 활성 멘토십 찾기
    if not mentorship:
        mentorship = Mentorship.objects.filter(
            mentee_id=user.user_id, 
            is_active=True
        ).first()
    
    # 과제 목록 가져오기
    tasks = []
    if mentorship:
        task_assigns = TaskAssign.objects.filter(
            mentorship_id=mentorship.mentorship_id
        ).order_by('week', 'order')
        
        for task in task_assigns:
            task_data = {
                'id': task.task_assign_id,
                'title': task.title or '제목 없음',
                'desc': task.description or '설명 없음',
                'description': task.description or '설명 없음',
                'guideline': task.guideline or '',
                'week': task.week,
                'priority': task.priority or '하',
                'status': task.status or '진행 전',
                'start_date': task.start_date,
                'end_date': task.end_date,
                'exp': calculate_exp_by_priority(task.priority),
                'dday': calculate_dday(task.end_date) if task.end_date else 'D-?'
            }
            tasks.append(task_data)
    
    # 주차별로 과제 그룹화
    week_tasks = {}
    for task in tasks:
        week = task['week']
        if week not in week_tasks:
            week_tasks[week] = []
        week_tasks[week].append(task)
    
    # 주차별 정렬
    week_tasks = dict(sorted(week_tasks.items()))
    
    context = {
        'user': request.user,
        'mentorship': mentorship,
        'tasks': tasks,
        'week_tasks': week_tasks,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '과제 목록'
    }
    return render(request, 'mentee/task_list.html', context)

@login_required
def task_detail(request, task_assign_id):
    """과제 상세 페이지 - JSON 응답만 반환"""
    try:
        task = TaskAssign.objects.get(task_assign_id=task_assign_id)
        
        # 현재 사용자가 이 과제에 접근할 권한이 있는지 확인
        mentorship = task.mentorship_id
        if (mentorship.mentee_id != request.user.user_id and 
            mentorship.mentor_id != request.user.user_id):
            return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
        
        # 과제 데이터 반환
        task_data = {
            'id': task.task_assign_id,
            'title': task.title or '제목 없음',
            'desc': task.description or '설명 없음',
            'description': task.description or '설명 없음',
            'guideline': task.guideline or '',
            'week': task.week,
            'priority': task.priority or '하',
            'status': task.status or '진행 전',
            'start_date': task.start_date.strftime('%Y-%m-%d') if task.start_date else '',
            'end_date': task.end_date.strftime('%Y-%m-%d') if task.end_date else '',
            'exp': calculate_exp_by_priority(task.priority),
            'dday': calculate_dday(task.end_date) if task.end_date else 'D-?'
        }
        
        return JsonResponse({'success': True, 'task': task_data})
        
    except TaskAssign.DoesNotExist:
        return JsonResponse({'success': False, 'error': '과제를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        logger.error(f"과제 상세 조회 에러: {e}")
        return JsonResponse({'success': False, 'error': '서버 오류가 발생했습니다.'}, status=500)

# 헬퍼 함수들
def calculate_exp_by_priority(priority):
    """우선순위에 따른 경험치 계산"""
    if priority == '상':
        return 80
    elif priority == '중':
        return 50
    elif priority == '하':
        return 20
    return 30

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

def calculate_level(total_exp):
    """총 경험치로 레벨 계산"""
    return (total_exp // 300) + 1

# 과제 업데이트 뷰
@login_required
def task_update(request, task_assign_id):
    """과제 업데이트 API - FastAPI로 프록시"""
    if request.method == 'POST':
        try:
            import requests
            
            # 요청 데이터 파싱
            data = json.loads(request.body)
            
            # FastAPI로 요청 전송
            response = requests.put(
                f'{settings.FASTAPI_BASE_URL}/api/v1/mentee/task/{task_assign_id}',
                json=data,
                headers={
                    'Authorization': f'Bearer {request.user.email}',  # 임시 토큰 방식
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                return JsonResponse(response.json())
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
                return JsonResponse({
                    'success': False,
                    'error': error_data.get('detail', '과제 업데이트에 실패했습니다.')
                }, status=response.status_code)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 JSON 형식입니다.'
            }, status=400)
        except Exception as e:
            logger.error(f"과제 업데이트 API 에러: {e}")
            return JsonResponse({
                'success': False,
                'error': f'과제 업데이트 중 오류가 발생했습니다: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용'}, status=405)
>>>>>>> Stashed changes
