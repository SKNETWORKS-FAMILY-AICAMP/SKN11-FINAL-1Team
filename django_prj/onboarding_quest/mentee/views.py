# TaskAssign 수정 API (AJAX)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
import json
from django.http import JsonResponse
from django.shortcuts import render
from core.models import TaskAssign
from collections import defaultdict
# 댓글 저장 API
from django.contrib.auth.decorators import login_required
from core.models import Memo, User

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
        status = data.get('status', '진행 전').strip() or '진행 전'
        priority = data.get('priority', '').strip() or (parent.priority if parent else None)
        scheduled_end_date = data.get('end_date', None)
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
        t.status = data.get('status', t.status)
        t.title = data.get('title', t.title)
        t.guideline = data.get('guideline', t.guideline)
        t.description = data.get('description', t.description)
        t.priority = data.get('priority', t.priority)
        t.end_date = data.get('end_date', t.end_date)
        t.save()
        return JsonResponse({'success': True})
    except TaskAssign.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def mentee(request):
    return render(request, 'mentee/mentee.html')

def task_list(request):
    mentorship_id = request.GET.get('mentorship_id')
    week_tasks = defaultdict(list)
    selected_task = None
    if mentorship_id:
        task_qs = TaskAssign.objects.filter(mentorship_id=mentorship_id).order_by('week', 'order')
        for t in task_qs:
            subtasks = list(t.subtasks.all().values('task_assign_id', 'title', 'status', 'parent'))
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
            'scheduled_start_date': t.scheduled_start_date,
            'scheduled_end_date': t.scheduled_end_date,
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