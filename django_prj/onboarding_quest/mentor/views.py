
from django.shortcuts import render
from django.db import models
from django.contrib.auth.decorators import login_required
from core.models import Curriculum, TaskManage
import json
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

# 커리큘럼+Task 저장 API
@require_POST
@login_required
@csrf_exempt
def save_curriculum(request):
    import json
    from core.models import Curriculum, TaskManage
    from django.db import transaction
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
    return render(request, 'mentor/mentor.html')

@login_required
def add_template(request):
    return render(request, 'mentor/add_template.html')

@login_required
def manage_mentee(request):
    return render(request, 'mentor/manage_mentee.html')

@login_required
def manage_template(request):
    user = request.user
    curriculums = Curriculum.objects.filter(
        models.Q(common=True) | models.Q(department=user.department)
    ).order_by('-common', 'curriculum_title')
    curriculum_tasks = {}
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
