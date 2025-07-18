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


# 멘토링 생성 API
@login_required
@require_POST
@csrf_exempt
def create_mentorship(request):
    try:
        data = json.loads(request.body)
        
        # 현재 사용자 정보 가져오기
        user_data = request.session.get('user_data', {})
        mentor_id = user_data.get('user_id')
        
        if not mentor_id:
            return JsonResponse({'success': False, 'message': '멘토 정보를 찾을 수 없습니다.'})
        
        mentee_id = int(data.get('mentee_id'))
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        curriculum_ids = data.get('curriculum_ids', [])
        
        # 단일 커리큘럼도 지원 (기존 호환성)
        if 'curriculum_id' in data and not curriculum_ids:
            curriculum_ids = [int(data.get('curriculum_id'))]
        elif isinstance(curriculum_ids, str):
            curriculum_ids = [int(curriculum_ids)]
        elif isinstance(curriculum_ids, list):
            curriculum_ids = [int(cid) for cid in curriculum_ids]
        
        if not curriculum_ids:
            return JsonResponse({'success': False, 'message': '커리큘럼을 선택해주세요.'})
        
        # FastAPI로 커리큘럼들 조회
        curriculum_titles = []
        max_weeks = 0
        
        for curriculum_id in curriculum_ids:
            try:
                curriculum = fastapi_client.get_curriculum(curriculum_id)
                curriculum_titles.append(curriculum['curriculum_title'])
                max_weeks = max(max_weeks, curriculum.get('total_weeks', 0))
            except:
                continue
        
        combined_title = ' + '.join(curriculum_titles)
        
        # FastAPI로 멘토쉽 생성
        mentorship_data = {
            'mentor_id': mentor_id,
            'mentee_id': mentee_id,
            'start_date': start_date,
            'end_date': end_date,
            'curriculum_title': combined_title,
            'total_weeks': max_weeks,
            'is_active': True
        }
        
        result = fastapi_client.create_mentorship(mentorship_data)
        mentorship_id = result.get('mentorship_id')
        
        # FastAPI로 TaskManage들 조회하고 TaskAssign 생성
        for curriculum_id in curriculum_ids:
            try:
                task_manages = fastapi_client.get_task_manages(curriculum_id=curriculum_id)
                
                # TaskManage → TaskAssign 변환 로직
                mentorship_start = datetime.strptime(start_date, '%Y-%m-%d')
                
                for task in task_manages.get('tasks', []):
                    week = task.get('week', 1)
                    task_start = mentorship_start + timedelta(days=(week-1)*7)
                    period = task.get('period', 1)
                    
                    task_assign_data = {
                        'title': task.get('title'),
                        'description': task.get('description'),
                        'guideline': task.get('guideline'),
                        'week': week,
                        'order': task.get('order'),
                        'scheduled_start_date': task_start.date().isoformat(),
                        'scheduled_end_date': (task_start.date() + timedelta(days=period)).isoformat(),
                        'status': '진행전',
                        'priority': task.get('priority'),
                        'mentorship_id': mentorship_id
                    }
                    
                    fastapi_client.create_task_assign(task_assign_data)
                    
            except Exception as e:
                print(f"Task creation error for curriculum {curriculum_id}: {e}")
                continue
        
        return JsonResponse({'success': True, 'message': '멘토십이 성공적으로 생성되었습니다.'})
        
    except AuthenticationError:
        return JsonResponse({'success': False, 'message': '인증이 만료되었습니다.'})
    except APIError as e:
        return JsonResponse({'success': False, 'message': f'API 오류: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'멘토십 생성 중 오류가 발생했습니다: {str(e)}'})


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
    try:
        # 현재 사용자 정보 - 두 가지 방법 모두 시도
        user_data = request.session.get('user_data', {})
        mentor_id = user_data.get('user_id')
        
        # Django User 모델에서도 시도
        if not mentor_id and hasattr(request.user, 'user_id'):
            mentor_id = request.user.user_id
            user_data = {'role': getattr(request.user, 'role', 'mentor')}
        
        print(f"DEBUG - 멘토 ID: {mentor_id}, 사용자 데이터: {user_data}")
        
        if not mentor_id:
            messages.error(request, '사용자 정보를 찾을 수 없습니다.')
            return render(request, 'mentor/mentor.html', {'mentee_cards': []})
        
        # 역할 확인은 좀 더 유연하게
        user_role = user_data.get('role', '').lower()
        if user_role and user_role not in ['mentor', 'both']:
            messages.error(request, '멘토 권한이 필요합니다.')
            return render(request, 'mentor/mentor.html', {'mentee_cards': []})
        
        # FastAPI에서 로그인한 유저가 멘토로 포함된 멘토쉽 목록 조회
        print(f"DEBUG - 멘토쉽 정보 요청 중... mentor_id={mentor_id}")
        # 멘토별 멘토쉽 조회 API 사용
        mentorships_url = f"{fastapi_client.base_url}/api/mentorship/mentor/{mentor_id}"
        response = fastapi_client.session.get(mentorships_url)
        mentorships = fastapi_client._handle_response(response)
        print(f"DEBUG - 멘토쉽 응답: {mentorships}")
        print(f"DEBUG - 멘토쉽 목록: {mentorships}")
        
        # 멘티 정보 조회
        if mentorships:
            mentee_ids = [m.get('mentee_id') for m in mentorships]
            # 현재 회사의 모든 사용자 조회 (성능 최적화)
            company_id = user_data.get('company_id')
            print(f"DEBUG - 회사 ID: {company_id}")
            if company_id:
                users_result = fastapi_client.get_users(company_id=company_id)
                all_users = {user['user_id']: user for user in users_result.get('users', [])}
                print(f"DEBUG - 사용자 수: {len(all_users)}")
            else:
                all_users = {}
                print("DEBUG - 회사 ID가 없어서 사용자 정보를 가져올 수 없습니다.")
        else:
            mentee_ids = []
            all_users = {}
            print("DEBUG - 멘토쉽이 없습니다.")
        
        # 진척도, D-day 등 계산
        mentee_cards = []
        from datetime import date
        
        print(f"DEBUG - 멘토쉽 카드 생성 시작... 총 {len(mentorships)}개")
        
        for ms in mentorships:
            mentee_id = ms.get('mentee_id')
            mentee = all_users.get(mentee_id)
            print(f"DEBUG - 멘토쉽 처리 중: mentee_id={mentee_id}, mentee={mentee}")
            
            if not mentee:
                print(f"DEBUG - 멘티 정보를 찾을 수 없음: mentee_id={mentee_id}")
                continue

            # D-day 계산: 멘토쉽 종료일 기준
            dday = ''
            end_date_str = ms.get('end_date')
            if end_date_str:
                from datetime import datetime
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    dday_val = (end_date - date.today()).days
                    if dday_val > 0:
                        dday = f"D-{dday_val}"
                    elif dday_val == 0:
                        dday = "D-DAY"
                    else:
                        dday = "종료"
                except:
                    dday = ""
            else:
                dday = ""
            
            # 진척도: 멘토쉽에 할당된 TaskAssign 중 완료된 개수/전체 개수
            print(f"DEBUG - 태스크 조회 중... mentorship_id={ms.get('mentorship_id')}")
            try:
                tasks_result = fastapi_client.get_task_assigns(mentorship_id=ms.get('mentorship_id'))
                all_tasks = tasks_result.get('task_assigns', [])  # 'tasks' 대신 'task_assigns' 사용
                total_tasks = len(all_tasks)
                completed_tasks = len([t for t in all_tasks if t.get('status') == '완료'])
                progress = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
                
                print(f"DEBUG - 진척도 계산: 총 {total_tasks}개, 완료 {completed_tasks}개, 진척도 {progress}%")
            except (AuthenticationError, APIError) as e:
                print(f"DEBUG - 태스크 조회 실패: {e}")
                # 태스크 조회에 실패해도 멘토쉽 카드는 표시 (진척도는 0%)
                total_tasks = 0
                completed_tasks = 0
                progress = 0
                print(f"DEBUG - 태스크 조회 실패로 진척도 0%로 설정")
            except Exception as e:
                print(f"DEBUG - 태스크 조회 중 예외 발생: {e}")
                total_tasks = 0
                completed_tasks = 0
                progress = 0
            
            card_data = {
                'name': f'{mentee.get("last_name", "")}{mentee.get("first_name", "")}',
                'tags': [mentee.get('tag')] if mentee.get('tag') else [],
                'dday': dday,
                'progress': progress,
                'mentorship_id': ms.get('mentorship_id'),
                'curriculum_title': ms.get('curriculum_title', '커리큘럼 정보 없음'),
                'total_weeks': ms.get('total_weeks', 0),
            }
            
            mentee_cards.append(card_data)
            print(f"DEBUG - 카드 생성 완료: {card_data}")
            
        print(f"DEBUG - 최종 멘티 카드 수: {len(mentee_cards)}")
        return render(request, 'mentor/mentor.html', {'mentee_cards': mentee_cards})
        
    except (AuthenticationError, APIError) as e:
        print(f"DEBUG - API 오류: {e}")
        messages.error(request, f'멘토 정보 조회 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'mentor/mentor.html', {'mentee_cards': []})
    except Exception as e:
        print(f"DEBUG - 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'데이터를 불러오는 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'mentor/mentor.html', {'mentee_cards': []})

@login_required
def add_template(request):
    return render(request, 'mentor/add_template.html')

@login_required

@login_required
def manage_mentee(request):
    try:
        user_data = request.session.get('user_data', {})
        company_id = user_data.get('company_id')
        department_id = user_data.get('department_id')
        
        # 같은 회사의 모든 멘티 목록
        mentees_result = fastapi_client.get_users(company_id=company_id, role='mentee')
        mentees = mentees_result.get('users', [])
        
        # 부서 커리큘럼 목록 (공용+부서)
        curriculums_result = fastapi_client.get_curriculums(department_id=department_id)
        curriculums = curriculums_result.get('curriculums', [])
        
        # 공통 커리큘럼도 포함
        common_curriculums_result = fastapi_client.get_curriculums(common=True)
        common_curriculums = common_curriculums_result.get('curriculums', [])
        
        all_curriculums = common_curriculums + curriculums
        
        return render(request, 'mentor/manage_mentee.html', {
            'mentees': mentees,
            'curriculums': all_curriculums,
        })
        
    except (AuthenticationError, APIError) as e:
        messages.error(request, f'멘티 관리 정보 조회 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'mentor/manage_mentee.html', {
            'mentees': [],
            'curriculums': [],
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
