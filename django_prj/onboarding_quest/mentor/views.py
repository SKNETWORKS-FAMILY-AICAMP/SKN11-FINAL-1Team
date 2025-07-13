from django.shortcuts import render
from django.db import models
from django.contrib.auth.decorators import login_required
from core.models import Curriculum, TaskManage
import json
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction


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
                'period': t.period.strftime('%Y-%m-%d') if t.period else '',
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
