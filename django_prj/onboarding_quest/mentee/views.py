from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
import json
from django.http import JsonResponse
from django.shortcuts import render
from core.models import TaskAssign
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from core.models import Memo, User
from datetime import date

# 하위 테스크(TaskAssign) 생성 API
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_subtask(request, parent_id):
    try:
        # parent_id는 상위 TaskAssign의 id, 0이면 최상위로 간주
        parent = None
        if int(parent_id) != 0:
            parent = TaskAssign.objects.get(task_assign_id=parent_id)
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        guideline = data.get('guideline', '').strip()
        description = data.get('description', '').strip()
        status = data.get('status', '진행전').strip() or '진행전'
        priority = data.get('priority', '').strip() or (parent.priority if parent else None)
        scheduled_end_date = data.get('scheduled_end_date', None)
        week = data.get('week', None)
        order = data.get('order', None)
        mentorship_id = data.get('mentorship_id', None)
        # 필수값 체크
        if not title:
            return JsonResponse({'success': False, 'error': '제목을 입력하세요.'}, status=400)
        if not mentorship_id and parent:
            mentorship_id = parent.mentorship_id_id if hasattr(parent, 'mentorship_id_id') else parent.mentorship_id.id
        if not mentorship_id:
            return JsonResponse({'success': False, 'error': '멘토쉽 정보가 필요합니다.'}, status=400)
        # week, order 기본값 상속
        if not week and parent:
            week = parent.week
        if not order and parent:
            order = None
        subtask = TaskAssign.objects.create(
            parent=parent,
            mentorship_id_id=mentorship_id,
            title=title,
            guideline=guideline,
            description=description,
            week=week if week is not None else 1,
            order=order,
            scheduled_start_date=None,
            scheduled_end_date=scheduled_end_date if scheduled_end_date else None,
            real_start_date=None,
            real_end_date=None,
            status=status,
            priority=priority,
        )
        return JsonResponse({'success': True, 'subtask_id': subtask.task_assign_id})
    except TaskAssign.DoesNotExist:
        return JsonResponse({'success': False, 'error': '상위 Task가 존재하지 않습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
@csrf_exempt
@require_POST
@login_required
def task_comment(request, task_assign_id):
    try:
        t = TaskAssign.objects.get(task_assign_id=task_assign_id)
        data = json.loads(request.body)
        comment = data.get('comment', '').strip()
        if not comment:
            return JsonResponse({'success': False, 'error': '댓글 내용을 입력하세요.'}, status=400)
        user = request.user
        memo = Memo.objects.create(task_assign=t, user=user, comment=comment)
        return JsonResponse({'success': True, 'memo': {
            'user': f"{user.last_name}{user.first_name}",
            'comment': memo.comment,
            'create_date': memo.create_date.strftime('%Y-%m-%d'),
        }})
    except TaskAssign.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
@csrf_exempt
@require_POST
def task_update(request, task_assign_id):
    try:
        t = TaskAssign.objects.get(task_assign_id=task_assign_id)
        data = json.loads(request.body)
        
        # 기존 상태와 새 상태 비교
        old_status = t.status
        new_status = data.get('status', t.status)
        
        t.status = new_status
        t.title = data.get('title', t.title)
        t.guideline = data.get('guideline', t.guideline)
        t.description = data.get('description', t.description)
        t.priority = data.get('priority', t.priority)
        t.scheduled_end_date = data.get('scheduled_end_date', t.scheduled_end_date)
        t.save()
        
        # 상위 태스크가 '완료'로 변경된 경우, 모든 하위 태스크도 '완료'로 변경
        if old_status != '완료' and new_status == '완료' and not t.parent:
            # 하위 태스크들 찾아서 완료 처리
            subtasks = TaskAssign.objects.filter(parent=t)
            subtasks.update(status='완료')
        
        return JsonResponse({'success': True})
    except TaskAssign.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def mentee(request):
    context = {}
    
    # 로그인한 멘티의 멘토쉽 정보 가져오기
    if request.user.is_authenticated and request.user.role == 'mentee':
        try:
            from core.models import Mentorship
            mentorship = Mentorship.objects.filter(
                mentee_id=request.user.user_id,
                is_active=True
            ).first()
            
            if mentorship:
                # 해당 멘토쉽의 태스크들을 상태별로 분류
                tasks = TaskAssign.objects.filter(
                    mentorship_id=mentorship,
                    parent__isnull=True  # 상위 태스크만 (하위 태스크 제외)
                ).order_by('week', 'order')
                
                # 상태별로 태스크 분류
                status_tasks = {
                    '진행전': [],
                    '진행중': [],
                    '검토요청': [],
                    '완료': []
                }
                
                for task in tasks:
                    # D-day 계산
                    dday = None
                    dday_text = None
                    if task.scheduled_end_date:
                        from datetime import date
                        today = date.today()
                        diff = (task.scheduled_end_date - today).days
                        dday = diff
                        if diff >= 0:
                            dday_text = f"D-{diff}"
                        else:
                            dday_text = f"D+{abs(diff)}"
                    
                    task_data = {
                        'id': task.task_assign_id,
                        'title': task.title,
                        'description': task.description,
                        'priority': task.priority or '하',
                        'status': task.status,
                        'dday': dday,
                        'dday_text': dday_text,
                        'week': task.week,
                        'scheduled_end_date': task.scheduled_end_date,
                    }
                    
                    status = task.status or '진행전'
                    if status in status_tasks:
                        status_tasks[status].append(task_data)
                
                # 태스크 진행률 계산
                total_tasks = len(tasks)
                completed_tasks = len(status_tasks['완료'])
                completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                context['status_tasks'] = status_tasks
                context['mentorship'] = mentorship
                context['total_tasks'] = total_tasks
                context['completed_tasks'] = completed_tasks
                context['completion_percentage'] = round(completion_percentage, 1)
        except Exception as e:
            print(f"Error loading mentorship data: {e}")
    
    return render(request, 'mentee/mentee.html', context)

def task_list(request):
    mentorship_id = request.GET.get('mentorship_id')
    week_tasks = defaultdict(list)
    selected_task = None
    if mentorship_id:
        task_qs = TaskAssign.objects.filter(mentorship_id=mentorship_id).order_by('week', 'order')
        for t in task_qs:
            subtasks = list(t.subtasks.all().values('task_assign_id', 'title', 'status', 'parent'))
            
            # D-day 계산
            dday = None
            if t.scheduled_end_date:
                today = date.today()
                diff = (t.scheduled_end_date - today).days
                dday = diff
            
            task = {
                'id': t.task_assign_id,
                'title': t.title,
                'desc': t.description,
                'guideline': t.guideline,
                'week': t.week,
                'order': t.order,
                'scheduled_start_date': t.scheduled_start_date,
                'scheduled_end_date': t.scheduled_end_date,
                'real_start_date': t.real_start_date,
                'real_end_date': t.real_end_date,
                'status': t.status,
                'priority': t.priority,
                'subtasks': subtasks,
                'description': t.description,
                'parent': t.parent_id,
                'dday': dday,
            }
            week_tasks[t.week].append(task)
        # 첫 번째 주의 첫 번째 Task를 기본 선택
        if week_tasks:
            first_week = sorted(week_tasks.keys())[0]
            if week_tasks[first_week]:
                selected_task = week_tasks[first_week][0]
    context = {
        'week_tasks': dict(week_tasks),
        'selected_task': selected_task,
        'mentorship_id': mentorship_id,
    }
    return render(request, 'mentee/task_list.html', context)

# AJAX용 Task 상세정보 API
def task_detail(request, task_assign_id):
    try:
        t = TaskAssign.objects.get(task_assign_id=task_assign_id)
        data = {
            'id': t.task_assign_id,
            'title': t.title,
            'desc': t.description,
            'guideline': t.guideline,
            'week': t.week,
            'order': t.order,
            'scheduled_start_date': t.scheduled_start_date.strftime('%Y-%m-%d') if t.scheduled_start_date else None,
            'scheduled_end_date': t.scheduled_end_date.strftime('%Y-%m-%d') if t.scheduled_end_date else None,
            'real_start_date': t.real_start_date,
            'real_end_date': t.real_end_date,
            'status': t.status,
            'priority': t.priority,
            'description': t.description,
        }
        # 댓글 목록 추가
        memos = Memo.objects.filter(task_assign=t).select_related('user').order_by('create_date')
        memo_list = [
            {
                'user': f"{m.user.last_name}{m.user.first_name}",
                'comment': m.comment,
                'create_date': m.create_date.strftime('%Y-%m-%d'),
            }
            for m in memos
        ]
        data['memos'] = memo_list
        return JsonResponse({'success': True, 'task': data})
    except TaskAssign.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)

# 태스크 상태 업데이트 API (Drag&Drop용)
@csrf_exempt  # CSRF 토큰을 JavaScript에서 처리하므로 exempt 사용
@require_POST
@login_required
def update_task_status(request, task_id):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"태스크 상태 업데이트 요청 - 사용자: {request.user.user_id}, 태스크: {task_id}")
        
        # TaskAssign 객체 찾기
        task = TaskAssign.objects.get(task_assign_id=task_id)
        logger.info(f"태스크 찾음 - ID: {task.task_assign_id}, 현재 상태: {task.status}")
        
        # 멘토쉽 권한 확인 (현재 로그인한 유저가 해당 태스크의 멘티인지 확인)
        from core.models import Mentorship
        mentorship = Mentorship.objects.filter(
            mentorship_id=task.mentorship_id_id,
            mentee_id=request.user.user_id,
            is_active=True
        ).first()
        
        if not mentorship:
            logger.warning(f"권한 없음 - 사용자: {request.user.user_id}, 태스크: {task_id}")
            return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
        
        # 요청 데이터 파싱
        try:
            if request.content_type and 'application/json' in request.content_type:
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            logger.info(f"요청 데이터: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return JsonResponse({'success': False, 'error': 'JSON 형식이 올바르지 않습니다.'}, status=400)
        
        new_status = data.get('status', '').strip()
        logger.info(f"새로운 상태: {new_status}")
        
        # 유효한 상태값인지 확인
        valid_statuses = ['진행전', '진행중', '검토요청', '완료']
        if new_status not in valid_statuses:
            logger.error(f"유효하지 않은 상태: {new_status}")
            return JsonResponse({'success': False, 'error': f'유효하지 않은 상태입니다. 가능한 상태: {valid_statuses}'}, status=400)
        
        # 상태 업데이트
        old_status = task.status
        task.status = new_status
        
        # 상태에 따른 날짜 업데이트
        from datetime import datetime
        if new_status == '진행중' and not task.real_start_date:
            task.real_start_date = datetime.now().date()
            logger.info(f"실제 시작일 설정: {task.real_start_date}")
        elif new_status == '완료' and not task.real_end_date:
            task.real_end_date = datetime.now().date()
            logger.info(f"실제 완료일 설정: {task.real_end_date}")
        
        task.save()
        logger.info(f"태스크 상태 업데이트 완료 - {old_status} -> {new_status}")
        
        response_data = {
            'success': True,
            'old_status': old_status,
            'new_status': new_status,
            'task_id': task_id,
            'message': f'태스크 상태가 "{old_status}"에서 "{new_status}"로 변경되었습니다.'
        }
        
        response = JsonResponse(response_data)
        response['Content-Type'] = 'application/json'
        # CORS 헤더 추가 (필요한 경우)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken'
        return response
        
    except TaskAssign.DoesNotExist:
        logger.error(f"태스크를 찾을 수 없음 - ID: {task_id}")
        return JsonResponse({'success': False, 'error': '태스크를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        logger.error(f"예상치 못한 오류 - 태스크: {task_id}, 오류: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': f'서버 오류가 발생했습니다: {str(e)}'}, status=500)