from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from core.models import TaskAssign
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from core.models import Memo, User
from datetime import date, datetime
from core.utils.fastapi_client import fastapi_client, APIError, AuthenticationError
from django.contrib import messages

# 하위 테스크(TaskAssign) 생성 API
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_subtask(request, parent_id):
    try:
        data = json.loads(request.body)
        
        # 부모 태스크 정보 가져오기 (0이면 최상위)
        parent = None
        if int(parent_id) != 0:
            try:
                parent = fastapi_client.get_task_assign(int(parent_id))
            except:
                return JsonResponse({'success': False, 'error': '상위 Task가 존재하지 않습니다.'}, status=404)
        
        title = data.get('title', '').strip()
        guideline = data.get('guideline', '').strip()
        description = data.get('description', '').strip()
        status = data.get('status', '진행전').strip() or '진행전'
        priority = data.get('priority', '').strip() or (parent.get('priority') if parent else None)
        scheduled_end_date = data.get('scheduled_end_date', None)
        week = data.get('week', None)
        order = data.get('order', None)
        mentorship_id = data.get('mentorship_id', None)
        
        # 필수값 체크
        if not title:
            return JsonResponse({'success': False, 'error': '제목을 입력하세요.'}, status=400)
            
        if not mentorship_id and parent:
            mentorship_id = parent.get('mentorship_id')
        if not mentorship_id:
            return JsonResponse({'success': False, 'error': '멘토쉽 정보가 필요합니다.'}, status=400)
        
        # week, order 기본값 상속
        if not week and parent:
            week = parent.get('week')
        if not order and parent:
            order = None
        
        # FastAPI로 서브태스크 생성
        subtask_data = {
            'parent_id': int(parent_id) if int(parent_id) != 0 else None,
            'mentorship_id': mentorship_id,
            'title': title,
            'guideline': guideline,
            'description': description,
            'week': week if week is not None else 1,
            'order': order,
            'scheduled_start_date': None,
            'scheduled_end_date': scheduled_end_date if scheduled_end_date else None,
            'real_start_date': None,
            'real_end_date': None,
            'status': status,
            'priority': priority,
        }
        
        result = fastapi_client.create_task_assign(subtask_data)
        return JsonResponse({'success': True, 'subtask_id': result.get('task_assign_id')})
        
    except AuthenticationError:
        return JsonResponse({'success': False, 'error': '인증이 만료되었습니다.'}, status=401)
    except APIError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
@csrf_exempt
@require_POST
@login_required
def task_comment(request, task_assign_id):
    try:
        # FastAPI로 태스크 존재 확인
        task_info = fastapi_client.get_task_assign(task_assign_id)
        
        data = json.loads(request.body)
        comment = data.get('comment', '').strip()
        if not comment:
            return JsonResponse({'success': False, 'error': '댓글 내용을 입력하세요.'}, status=400)
        
        # 현재 사용자 정보
        user_data = request.session.get('user_data', {})
        user_id = user_data.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': '사용자 정보를 찾을 수 없습니다.'}, status=400)
        
        # FastAPI로 메모 생성
        memo_data = {
            'task_assign_id': task_assign_id,
            'user_id': user_id,
            'comment': comment,
            'create_date': datetime.now().date().isoformat()
        }
        
        result = fastapi_client.create_memo(memo_data)
        
        return JsonResponse({'success': True, 'memo': {
            'user': f"{user_data.get('last_name', '')}{user_data.get('first_name', '')}",
            'comment': result.get('comment'),
            'create_date': result.get('create_date'),
        }})
        
    except AuthenticationError:
        return JsonResponse({'success': False, 'error': '인증이 만료되었습니다.'}, status=401)
    except APIError:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
@csrf_exempt
@require_POST
def task_update(request, task_assign_id):
    try:
        # FastAPI로 태스크 정보 조회
        task_info = fastapi_client.get_task_assign(task_assign_id)
        
        data = json.loads(request.body)
        
        # 기존 상태와 새 상태 비교
        old_status = task_info.get('status')
        new_status = data.get('status', old_status)
        
        # 업데이트할 데이터 준비
        update_data = {'status': new_status}
        
        # 상태에 따른 날짜 업데이트
        if old_status != '진행중' and new_status == '진행중':
            update_data['real_start_date'] = datetime.now().date().isoformat()
        elif old_status != '완료' and new_status == '완료':
            update_data['real_end_date'] = datetime.now().date().isoformat()
        
        # 기타 필드 업데이트
        for field in ['title', 'description', 'guideline']:
            if field in data:
                update_data[field] = data[field]
        
        # FastAPI로 태스크 업데이트
        result = fastapi_client.update_task_assign(task_assign_id, update_data)
        
        return JsonResponse({'success': True, 'message': '태스크가 업데이트되었습니다.'})
        
    except AuthenticationError:
        return JsonResponse({'success': False, 'error': '인증이 만료되었습니다.'}, status=401)
    except APIError:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def mentee(request):
    try:
        # 현재 사용자 정보
        user_data = request.session.get('user_data', {})
        user_id = user_data.get('user_id')
        
        if not user_id or user_data.get('role') != 'mentee':
            messages.error(request, '멘티 권한이 필요합니다.')
            return redirect('account:login')
        
        context = {}
        
        # FastAPI로 멘토쉽 정보 가져오기
        mentorships_response = fastapi_client.get_mentorships(mentee_id=user_id, is_active=True)
        mentorships = mentorships_response.get('mentorships', [])
        
        if mentorships:
            mentorship = mentorships[0]  # 첫 번째 활성 멘토쉽
            mentorship_id = mentorship.get('mentorship_id')
            
            # 해당 멘토쉽의 태스크들 가져오기 (상위 태스크만)
            tasks_response = fastapi_client.get_task_assigns(mentorship_id=mentorship_id)
            all_tasks = tasks_response.get('tasks', [])
            
            # 상위 태스크만 필터링 (parent_id가 None인 것들)
            main_tasks = [task for task in all_tasks if task.get('parent_id') is None]
            
            # 상태별로 분류
            status_groups = defaultdict(list)
            for task in main_tasks:
                status = task.get('status', '진행전')
                status_groups[status].append(task)
            
            context.update({
                'mentorship': mentorship,
                'tasks_todo': status_groups['진행전'],
                'tasks_in_progress': status_groups['진행중'],
                'tasks_completed': status_groups['완료'],
                'tasks_all': main_tasks
            })
        
        return render(request, 'mentee/mentee.html', context)
        
    except AuthenticationError:
        messages.error(request, '인증이 만료되었습니다. 다시 로그인해주세요.')
        return redirect('account:login')
    except Exception as e:
        messages.error(request, f'데이터를 불러오는 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'mentee/mentee.html', {'mentorship': None})


@login_required
def task_list(request):
    try:
        mentorship_id = request.GET.get('mentorship_id')
        week_tasks = defaultdict(list)
        selected_task = None
        
        if mentorship_id:
            # FastAPI로 태스크 목록 조회
            tasks_response = fastapi_client.get_task_assigns(mentorship_id=int(mentorship_id))
            all_tasks = tasks_response.get('tasks', [])
            
            for task in all_tasks:
                # 서브태스크 찾기
                subtasks = [t for t in all_tasks if t.get('parent_id') == task.get('task_assign_id')]
                
                # D-day 계산
                dday = None
                if task.get('scheduled_end_date'):
                    from datetime import datetime
                    today = date.today()
                    end_date = datetime.strptime(task['scheduled_end_date'], '%Y-%m-%d').date()
                    diff = (end_date - today).days
                    dday = diff
                
                task_data = {
                    'id': task.get('task_assign_id'),
                    'title': task.get('title'),
                    'desc': task.get('description'),
                    'guideline': task.get('guideline'),
                    'week': task.get('week'),
                    'order': task.get('order'),
                    'scheduled_start_date': task.get('scheduled_start_date'),
                    'scheduled_end_date': task.get('scheduled_end_date'),
                    'real_start_date': task.get('real_start_date'),
                    'real_end_date': task.get('real_end_date'),
                    'status': task.get('status'),
                    'priority': task.get('priority'),
                    'subtasks': subtasks,
                    'description': task.get('description'),
                    'parent': task.get('parent_id'),
                    'dday': dday,
                }
                week_tasks[task.get('week', 1)].append(task_data)
            
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
        
    except Exception as e:
        messages.error(request, f'태스크 목록을 불러오는 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'mentee/task_list.html', {'week_tasks': {}, 'selected_task': None})


# AJAX용 Task 상세정보 API
@login_required
def task_detail(request, task_assign_id):
    try:
        # FastAPI로 태스크 상세 정보 조회
        task_info = fastapi_client.get_task_assign(task_assign_id)
        
        data = {
            'id': task_info.get('task_assign_id'),
            'title': task_info.get('title'),
            'desc': task_info.get('description'),
            'guideline': task_info.get('guideline'),
            'week': task_info.get('week'),
            'order': task_info.get('order'),
            'scheduled_start_date': task_info.get('scheduled_start_date'),
            'scheduled_end_date': task_info.get('scheduled_end_date'),
            'real_start_date': task_info.get('real_start_date'),
            'real_end_date': task_info.get('real_end_date'),
            'status': task_info.get('status'),
            'priority': task_info.get('priority'),
            'description': task_info.get('description'),
        }
        
        # FastAPI로 댓글 목록 조회
        memos_response = fastapi_client.get_memos(task_assign_id=task_assign_id)
        memo_list = []
        
        for memo in memos_response.get('memos', []):
            user_info = memo.get('user', {})
            memo_list.append({
                'user': f"{user_info.get('last_name', '')}{user_info.get('first_name', '')}",
                'comment': memo.get('comment'),
                'create_date': memo.get('create_date'),
            })
        
        data['memos'] = memo_list
        return JsonResponse({'success': True, 'task': data})
        
    except AuthenticationError:
        return JsonResponse({'success': False, 'error': '인증이 만료되었습니다.'}, status=401)
    except APIError:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# 태스크 상태 업데이트 API (Drag&Drop용)
@csrf_exempt  # CSRF 토큰을 JavaScript에서 처리하므로 exempt 사용
@require_POST
@login_required
def update_task_status(request, task_id):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"태스크 상태 업데이트 요청 - 사용자: {request.user.user_id}, 태스크: {task_id}")
        
        # FastAPI에서 태스크 정보 조회
        task_result = fastapi_client.get_task_assign(task_id)
        task = task_result
        logger.info(f"태스크 찾음 - ID: {task.get('task_assign_id')}, 현재 상태: {task.get('status')}")
        
        # 멘토쉽 권한 확인 (현재 로그인한 유저가 해당 태스크의 멘티인지 확인)
        mentorship_result = fastapi_client.get_mentorships(
            mentee_id=request.user.user_id,
            is_active=True
        )
        mentorships = mentorship_result.get('mentorships', [])
        
        # 해당 태스크의 멘토쉽이 현재 사용자의 멘토쉽인지 확인
        task_mentorship_id = task.get('mentorship_id')
        user_mentorship_ids = [m.get('mentorship_id') for m in mentorships]
        
        if task_mentorship_id not in user_mentorship_ids:
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
        
        # 상태 업데이트 데이터 준비
        old_status = task.get('status')
        
        # 상태에 따른 날짜 업데이트 데이터 준비
        update_data = {'status': new_status}
        
        if new_status == '진행중' and not task.get('real_start_date'):
            from datetime import datetime
            update_data['real_start_date'] = datetime.now().date().isoformat()
            logger.info(f"실제 시작일 설정: {update_data['real_start_date']}")
        elif new_status == '완료' and not task.get('real_end_date'):
            from datetime import datetime
            update_data['real_end_date'] = datetime.now().date().isoformat()
            logger.info(f"실제 완료일 설정: {update_data['real_end_date']}")
        
        # FastAPI로 태스크 상태 업데이트
        result = fastapi_client.update_task_assign(task_id, update_data)
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