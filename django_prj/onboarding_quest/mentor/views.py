from django.shortcuts import render
from django.db import models
from django.contrib.auth.decorators import login_required
from core.models import Curriculum, TaskManage
import json


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
