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


# 멘토링 생성 API

@login_required
@require_POST
@csrf_exempt
def create_mentorship(request):
    try:
        data = json.loads(request.body)
        mentor_id = request.user.user_id
        mentee_id = int(data.get('mentee_id'))
        scheduled_start_date = data.get('start_date')  # yyyy-mm-dd
        scheduled_end_date = data.get('end_date')      # yyyy-mm-dd
        curriculum_ids = data.get('curriculum_ids', [])  # 다중 커리큘럼 ID 배열
        
        # 단일 커리큘럼도 지원 (기존 호환성)
        if 'curriculum_id' in data and not curriculum_ids:
            curriculum_ids = [int(data.get('curriculum_id'))]
        elif isinstance(curriculum_ids, str):
            curriculum_ids = [int(curriculum_ids)]
        elif isinstance(curriculum_ids, list):
            curriculum_ids = [int(cid) for cid in curriculum_ids]
        
        if not curriculum_ids:
            return JsonResponse({'success': False, 'message': '커리큘럼을 선택해주세요.'})
        
        from core.models import Curriculum, TaskManage, TaskAssign
        
        # 선택된 커리큘럼들 가져오기
        curriculums = Curriculum.objects.filter(curriculum_id__in=curriculum_ids)
        curriculum_titles = [c.curriculum_title for c in curriculums]
        combined_title = ' + '.join(curriculum_titles)
        
        # 전체 주차 수 계산 (가장 긴 커리큘럼 기준)
        max_weeks = max([c.total_weeks for c in curriculums]) if curriculums else 0
        
        with transaction.atomic():
            # 이미 존재하는 멘토-멘티 조합 처리
            mentorship, created = Mentorship.objects.get_or_create(
                mentor_id=mentor_id,
                mentee_id=mentee_id,
                defaults={
                    'start_date': scheduled_start_date,
                    'end_date': scheduled_end_date,
                    'is_active': True,
                    'curriculum_title': combined_title,
                    'total_weeks': max_weeks
                }
            )
            if not created:
                mentorship.start_date = scheduled_start_date
                mentorship.end_date = scheduled_end_date
                mentorship.curriculum_title = combined_title
                mentorship.total_weeks = max_weeks
                mentorship.save()

            # 기존 TaskAssign 삭제 (새로 생성하기 위해)
            TaskAssign.objects.filter(mentorship_id=mentorship).delete()

            # 모든 커리큘럼의 Task들을 주차별로 병합
            weekly_tasks = {}  # {week: [tasks]}
            
            for curriculum in curriculums:
                tasks = TaskManage.objects.filter(curriculum_id=curriculum).order_by('week', 'order')
                for task in tasks:
                    week = task.week
                    if week not in weekly_tasks:
                        weekly_tasks[week] = []
                    
                    # 같은 주차에 동일한 제목의 과제가 있는지 확인
                    existing_titles = [t.title for t in weekly_tasks[week]]
                    if task.title not in existing_titles:
                        weekly_tasks[week].append(task)

            # TaskManage → TaskAssign 생성
            from datetime import datetime, timedelta
            mentorship_start = datetime.strptime(scheduled_start_date, '%Y-%m-%d')
            
            for week in sorted(weekly_tasks.keys()):
                tasks_in_week = weekly_tasks[week]
                # 같은 주차 내에서 order로 정렬
                tasks_in_week.sort(key=lambda x: x.order if x.order else 0)
                
                for order_index, task in enumerate(tasks_in_week, 1):
                    # 주차별 시작일 계산: mentorship 시작일 + (week-1)*7
                    task_start = mentorship_start + timedelta(days=(week-1)*7)
                    period = task.period if task.period else 1
                    scheduled_start = task_start.date()
                    scheduled_end = (task_start + timedelta(days=period-1)).date()
                    
                    TaskAssign.objects.create(
                        mentorship_id=mentorship,
                        title=task.title,
                        description=task.description,
                        guideline=task.guideline,
                        week=week,
                        order=order_index,  # 주차 내 순서 재정렬
                        scheduled_start_date=scheduled_start,
                        scheduled_end_date=scheduled_end,
                        real_start_date=None,
                        real_end_date=None,
                        priority=task.priority,
                        status='진행전'
                    )
                    
        return JsonResponse({'success': True, 'mentorship_id': mentorship.mentorship_id})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
        

@login_required
def mentee_detail(request, user_id):
    try:
        mentee = User.objects.get(user_id=user_id, department=request.user.department, role='mentee')
    except User.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    data = {
        'id': mentee.user_id,
        'emp': mentee.employee_number,
        'email': mentee.email,
        'dept': mentee.department.department_name if mentee.department else '',
        'job': mentee.job_part,
        'position': mentee.position,
        'join': mentee.join_date,
        'tag': mentee.tag,
        'lastname': mentee.last_name,
        'firstname': mentee.first_name,
    }
    return JsonResponse(data)

@login_required
@require_GET
def mentees_api(request):
    user = request.user
    mentees = User.objects.filter(department=user.department, role='mentee')
    mentee_list = [
        {
            'id': m.user_id,
            'emp': m.employee_number,
            'email': m.email,
            'dept': m.department.department_name if m.department else '',
            'job': m.job_part,
            'position': m.position,
            'join': m.join_date,
            'tag': m.tag,
            'lastname': m.last_name,
            'firstname': m.first_name,
        }
        for m in mentees
    ]
    return JsonResponse({'mentees': mentee_list})

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
    from core.models import Mentorship, User
    mentor_id = request.user.user_id
    # 로그인한 유저가 멘토로 포함된 멘토쉽 목록
    mentorships = Mentorship.objects.filter(mentor_id=mentor_id)
    mentee_ids = mentorships.values_list('mentee_id', flat=True)
    mentees = User.objects.filter(user_id__in=mentee_ids)
    # 진척도, D-day 등은 예시값(실제 로직에 맞게 수정 가능)
    mentee_cards = []
    from datetime import date
    for ms in mentorships:
        mentee = mentees.filter(user_id=ms.mentee_id).first()
        if not mentee:
            continue

        # D-day 계산: 멘토쉽 종료일 기준
        dday = ''
        if ms.end_date:
            dday_val = (ms.end_date - date.today()).days
            dday = f"D-{dday_val}" if dday_val > 0 else ("D-DAY" if dday_val == 0 else "종료")
        else:
            dday = ""
        # 진척도: 멘토쉽에 할당된 TaskAssign 중 완료된 개수/전체 개수
        from core.models import TaskAssign
        total_tasks = TaskAssign.objects.filter(mentorship_id=ms).count()
        completed_tasks = TaskAssign.objects.filter(mentorship_id=ms, status='완료').count()
        progress = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
        mentee_cards.append({
            'name': f'{mentee.last_name}{mentee.first_name}',
            'tags': [mentee.tag] if mentee.tag else [],
            'dday': dday,
            'progress': progress,
            'mentorship_id': ms.mentorship_id,
            'curriculum_title': ms.curriculum_title,
            'total_weeks': ms.total_weeks,
        })
    return render(request, 'mentor/mentor.html', {'mentee_cards': mentee_cards})

@login_required
def add_template(request):
    return render(request, 'mentor/add_template.html')

@login_required

@login_required
def manage_mentee(request):
    from core.models import User, Curriculum
    user = request.user
    # 같은 회사의 모든 멘티 목록
    mentees = User.objects.filter(company=user.company, role='mentee')
    # 부서 커리큘럼 목록 (공용+부서)
    curriculums = Curriculum.objects.filter(
        models.Q(common=True) | models.Q(department=user.department)
    ).order_by('-common', 'curriculum_title')
    return render(request, 'mentor/manage_mentee.html', {
        'mentees': mentees,
        'curriculums': curriculums,
    })

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
