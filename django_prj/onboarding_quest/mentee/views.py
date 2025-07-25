from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from core.models import TaskAssign
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from core.models import Memo, User
from datetime import date, datetime
from core.utils.fastapi_client import fastapi_client, APIError, AuthenticationError
from django.contrib import messages
from core.models import Mentorship
from report_langgraph import run_report_workflow

# 하위 테스크(TaskAssign) 생성 API
@csrf_exempt
def create_subtask(request, parent_id):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"하위 태스크 생성 요청 - parent_id: {parent_id}")
        logger.info(f"요청 메서드: {request.method}")
        logger.info(f"요청 본문: {request.body}")
        
        data = json.loads(request.body)
        logger.info(f"파싱된 데이터: {data}")
        
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
            logger.error("제목이 입력되지 않음")
            return JsonResponse({'success': False, 'error': '제목을 입력하세요.'}, status=400)
            
        # 멘토십 ID 처리 개선
        if not mentorship_id and parent:
            mentorship_id = parent.get('mentorship_id')
        
        # URL에서 mentorship_id 추출 시도
        if not mentorship_id:
            mentorship_id = request.GET.get('mentorship_id')
            
        # 여전히 없다면 세션에서 시도
        if not mentorship_id:
            user_data = request.session.get('user_data', {})
            mentorship_id = user_data.get('mentorship_id')
        
        logger.info(f"최종 멘토십 ID: {mentorship_id}")
        
        if not mentorship_id:
            logger.error("멘토쉽 ID를 찾을 수 없음")
            return JsonResponse({'success': False, 'error': '멘토쉽 정보가 필요합니다.'}, status=400)
        
        # week, order 기본값 상속
        if not week and parent:
            week = parent.get('week')
        if not order and parent:
            order = None
        
        # FastAPI 우선, Django ORM 대체
        try:
            # FastAPI로 서브태스크 생성 시도
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
            
        except Exception as fastapi_error:
            print(f"FastAPI 하위태스크 생성 실패: {fastapi_error}")
            
            # 🔧 Django ORM 대체 로직
            from core.models import TaskAssign, Mentorship
            from django.utils import timezone
            
            # 상위 태스크 확인
            parent_task = None
            if int(parent_id) != 0:
                try:
                    parent_task = TaskAssign.objects.get(task_assign_id=int(parent_id))
                except TaskAssign.DoesNotExist:
                    return JsonResponse({'success': False, 'error': '상위 태스크를 찾을 수 없습니다.'}, status=404)
            
            # 멘토십 확인
            try:
                mentorship = Mentorship.objects.get(mentorship_id=mentorship_id)
                logger.info(f"멘토십 찾음: {mentorship.mentorship_id}")
            except Mentorship.DoesNotExist:
                logger.error(f"멘토쉽 ID {mentorship_id}를 찾을 수 없음")
                return JsonResponse({'success': False, 'error': f'멘토쉽 ID {mentorship_id}을 찾을 수 없습니다.'}, status=404)
            
            # 날짜 변환
            scheduled_start_date_obj = None
            scheduled_end_date_obj = None
            
            if data.get('scheduled_start_date'):
                try:
                    from datetime import datetime
                    scheduled_start_date_obj = datetime.strptime(data['scheduled_start_date'], '%Y-%m-%d').date()
                except:
                    pass
                    
            if scheduled_end_date:
                try:
                    from datetime import datetime
                    scheduled_end_date_obj = datetime.strptime(scheduled_end_date, '%Y-%m-%d').date()
                except:
                    pass
            
            # 🔧 하위 태스크 생성 (Django ORM)
            try:
                logger.info(f"Django ORM으로 하위 태스크 생성 시도:")
                logger.info(f"  - parent: {parent_task}")
                logger.info(f"  - mentorship_id: {mentorship} (type: {type(mentorship)})")
                logger.info(f"  - title: {title}")
                logger.info(f"  - week: {week if week is not None else (parent_task.week if parent_task else 1)}")
                
                subtask = TaskAssign.objects.create(
                    parent=parent_task,
                    mentorship_id=mentorship,  # 🔧 수정: mentorship → mentorship_id
                    title=title,
                    guideline=guideline,
                    description=description,
                    week=week if week is not None else (parent_task.week if parent_task else 1),
                    order=order,
                    scheduled_start_date=scheduled_start_date_obj,
                    scheduled_end_date=scheduled_end_date_obj,
                    status=status,
                    priority=priority or (parent_task.priority if parent_task else '중'),
                )
                
                logger.info(f"Django ORM 하위태스크 생성 성공 - ID: {subtask.task_assign_id}")
                return JsonResponse({'success': True, 'subtask_id': subtask.task_assign_id})
                
            except Exception as orm_error:
                logger.error(f"Django ORM 하위태스크 생성 실패: {orm_error}")
                return JsonResponse({'success': False, 'error': f'Django ORM 실패: {str(orm_error)}'}, status=500)
        
    except Exception as e:
        print(f"하위태스크 생성 전체 실패: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
@csrf_exempt
@require_POST
@login_required
def task_comment(request, task_assign_id):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"메모 저장 요청 - task_assign_id: {task_assign_id}")
        
        data = json.loads(request.body)
        comment = data.get('comment', '').strip()
        if not comment:
            return JsonResponse({'success': False, 'error': '댓글 내용을 입력하세요.'}, status=400)
        
        # 현재 사용자 정보
        user_data = request.session.get('user_data', {})
        user_id = user_data.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': '사용자 정보를 찾을 수 없습니다.'}, status=400)
        
        # FastAPI 우선, Django ORM 대체
        try:
            logger.info(f"FastAPI로 메모 저장 시도 - task_assign_id: {task_assign_id}")
            
            # FastAPI로 태스크 존재 확인
            task_info = fastapi_client.get_task_assign(task_assign_id)
            
            # FastAPI로 메모 생성
            memo_data = {
                'task_assign_id': task_assign_id,
                'user_id': user_id,
                'comment': comment,
                'create_date': datetime.now().date().isoformat()
            }
            
            result = fastapi_client.create_memo(memo_data)
            
            logger.info(f"FastAPI 메모 저장 성공")
            return JsonResponse({'success': True, 'memo': {
                'user': f"{user_data.get('last_name', '')}{user_data.get('first_name', '')}",
                'comment': result.get('comment'),
                'create_date': result.get('create_date'),
            }})
            
        except Exception as fastapi_error:
            logger.warning(f"FastAPI 메모 저장 실패: {fastapi_error}")
            
            # 🔧 Django ORM 대체 로직
            logger.info(f"Django ORM으로 메모 저장 시도 - task_assign_id: {task_assign_id}")
            
            from core.models import TaskAssign, Memo, User
            from django.utils import timezone
            
            # 태스크 존재 확인
            try:
                task_assign = TaskAssign.objects.get(task_assign_id=task_assign_id)
            except TaskAssign.DoesNotExist:
                return JsonResponse({'success': False, 'error': '해당 태스크를 찾을 수 없습니다.'}, status=404)
            
            # 사용자 확인
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'}, status=404)
            
            # 메모 생성 (중요: task_assign 객체로 올바르게 설정!)
            memo = Memo.objects.create(
                task_assign=task_assign,  # 핵심: TaskAssign 객체 직접 할당
                user=user,
                comment=comment,
                create_date=timezone.now().date()
            )
            
            logger.info(f"Django ORM 메모 저장 성공 - memo_id: {memo.memo_id}")
            
            return JsonResponse({'success': True, 'memo': {
                'user': f"{user.last_name}{user.first_name}",
                'comment': memo.comment,
                'create_date': memo.create_date.isoformat() if memo.create_date else '',
            }})
        
    except Exception as e:
        logger.error(f"메모 저장 전체 실패: {str(e)}", exc_info=True)
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

         # 🔔 검토요청 상태일 때 알람 생성
        if new_status == '검토요청':
            try:
                create_review_request_alarm(task_info.get('mentorship_id'), task_info.get('title'))
            except Exception as e:
                print(f"검토요청 알람 생성 실패: {e}")
        
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
        user_data = request.session.get('user_data', {})
        session_user_id = user_data.get('user_id')
        request_user_id = getattr(request.user, 'user_id', None)
        
        print(f"🔍 DEBUG - 사용자 ID 검증:")
        print(f"🔍 DEBUG - session user_id: {session_user_id}")
        print(f"🔍 DEBUG - request.user.user_id: {request_user_id}")
        print(f"🔍 DEBUG - request.user.username: {getattr(request.user, 'username', 'None')}")
        
        # request.user.user_id를 우선적으로 사용 (더 신뢰할 수 있음)
        user_id = request_user_id if request_user_id else session_user_id
        
        if not user_id:
            print("🔍 DEBUG - 사용자 ID를 찾을 수 없음. 로그인 페이지로 리다이렉트")
            messages.error(request, '사용자 정보를 찾을 수 없습니다.')
            return redirect('account:login')
            
        print(f"🔍 DEBUG - 최종 사용 user_id: {user_id}")
        
        # 🔍 실제 데이터베이스에서 해당 사용자의 멘토십 확인
        try:
            from core.models import Mentorship
            user_mentorships = Mentorship.objects.filter(mentee_id=user_id)
            print(f"🔍 DEBUG - 실제 DB에서 해당 사용자({user_id})의 멘토십:")
            for ms in user_mentorships:
                print(f"🔍 DEBUG -   mentorship_id={ms.mentorship_id}, is_active={ms.is_active}, curriculum_title={ms.curriculum_title}")
                
            active_mentorships = user_mentorships.filter(is_active=True)
            if active_mentorships.exists():
                expected_mentorship_id = active_mentorships.first().mentorship_id  
                print(f"🔍 DEBUG - 예상되는 mentorship_id: {expected_mentorship_id}")
            else:
                print("🔍 DEBUG - 활성 멘토십이 없음")
        except Exception as e:
            print(f"🔍 DEBUG - DB 확인 중 오류: {e}")
        
        context = {}
        
        # 🔧 URL 파라미터에서 멘토십 ID 가져오기
        mentorship_id = request.GET.get('mentorship_id')
        
        # URL 파라미터가 없으면 FastAPI로 사용자의 활성 멘토십을 조회하여 리다이렉트
        if not mentorship_id:
            print(f"🔍 DEBUG - 멘토십 ID가 URL에 없음. 사용자 정보 확인:")
            print(f"🔍 DEBUG - user_id: {user_id}")
            print(f"🔍 DEBUG - request.user: {request.user}")
            print(f"🔍 DEBUG - request.user.user_id: {getattr(request.user, 'user_id', '없음')}")
            print(f"🔍 DEBUG - session user_data: {user_data}")
            
            found_mentorship_id = None
            
            # 🚀 FastAPI 우선 사용
            try:
                print(f"🔍 DEBUG - FastAPI로 사용자 활성 멘토십 조회 시도... user_id={user_id}")
                mentorships_response = fastapi_client.get_mentorships(mentee_id=user_id, is_active=True)
                mentorships = mentorships_response.get('mentorships', [])
                print(f"🔍 DEBUG - FastAPI 활성 멘토십 조회 성공: {len(mentorships)}개")
                print(f"🔍 DEBUG - 전체 조회된 멘토십들: {mentorships}")
                
                for idx, mentorship_data in enumerate(mentorships):
                    print(f"🔍 DEBUG - 멘토십 {idx+1}: id={mentorship_data.get('id')}, mentee_id={mentorship_data.get('mentee_id')}, is_active={mentorship_data.get('is_active')}")
                
                if mentorships:
                    print(f"🔍 DEBUG - 조회된 멘토십 상세 분석:")
                    for i, mentorship_data in enumerate(mentorships):
                        print(f"🔍 DEBUG - 멘토십 [{i}]: 전체 데이터 = {mentorship_data}")
                        mentorship_id_val = mentorship_data.get('id')
                        print(f"🔍 DEBUG - 멘토십 [{i}]: id = {mentorship_id_val} (타입: {type(mentorship_id_val)})")
                    found_mentorship_id = mentorships[0].get('id')
                    print(f"🔍 DEBUG - 선택된 멘토십: id={found_mentorship_id} (타입: {type(found_mentorship_id)})")
                    # 값이 1인지 확인
                    if found_mentorship_id == 1:
                        print("⚠️  WARNING - id가 1입니다! 이것이 예상되지 않은 값입니다.")
                    else:
                        print(f"✅ INFO - id가 {found_mentorship_id}로 올바르게 설정됨")
                else:
                    print("🔍 DEBUG - 사용자의 활성 멘토십이 없음")
                    
            except Exception as fastapi_error:
                print(f"🔍 DEBUG - FastAPI 멘토십 조회 실패: {fastapi_error}")
                
                # Django ORM fallback (FastAPI 실패 시에만)
                try:
                    print(f"🔍 DEBUG - Django ORM fallback으로 사용자 활성 멘토십 조회 시도... user_id={user_id}")
                    from core.models import Mentorship
                    
                    # 모든 멘토십 출력 (디버깅)
                    all_mentorships = Mentorship.objects.filter(mentee_id=user_id)
                    print(f"🔍 DEBUG - 해당 사용자의 모든 멘토십 수: {all_mentorships.count()}")
                    for mentorship_obj in all_mentorships:
                        print(f"🔍 DEBUG - 멘토십: ID={mentorship_obj.mentorship_id}, mentee_id={mentorship_obj.mentee_id}, is_active={mentorship_obj.is_active}")
                    
                    # 활성 멘토십만 조회
                    active_mentorship = Mentorship.objects.filter(mentee_id=user_id, is_active=True).first()
                    if active_mentorship:
                        found_mentorship_id = active_mentorship.mentorship_id
                        print(f"🔍 DEBUG - Django ORM으로 활성 멘토십 ID 조회: {found_mentorship_id} (타입: {type(found_mentorship_id)})")
                        
                        # 값이 1인지 확인
                        if found_mentorship_id == 1:
                            print("⚠️  WARNING - Django ORM에서도 mentorship_id가 1입니다!")
                        else:
                            print(f"✅ INFO - Django ORM에서 mentorship_id가 {found_mentorship_id}로 올바르게 조회됨")
                    else:
                        print("🔍 DEBUG - Django ORM에서도 활성 멘토십을 찾을 수 없음")
                except Exception as orm_error:
                    print(f"🔍 DEBUG - Django ORM fallback도 실패: {orm_error}")
            
            # 활성 멘토십을 찾았으면 올바른 URL로 리다이렉트
            if found_mentorship_id:
                from django.shortcuts import redirect
                from django.http import HttpResponseRedirect
                
                redirect_url = f"{request.path}?mentorship_id={found_mentorship_id}"
                print(f"🚀 DEBUG - 리다이렉트 준비:")
                print(f"🚀 DEBUG - found_mentorship_id: {found_mentorship_id} (타입: {type(found_mentorship_id)})")
                print(f"🚀 DEBUG - request.path: {request.path}")
                print(f"🚀 DEBUG - redirect_url: {redirect_url}")
                print(f"🚀 DEBUG - 리다이렉트 실행 중...")
                
                # 캐시 무효화를 위한 커스텀 리다이렉트
                response = HttpResponseRedirect(redirect_url)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                print("DEBUG - 활성 멘토십이 없음. 빈 페이지 렌더링")
                messages.error(request, '활성화된 멘토십이 없습니다. 관리자에게 문의하세요.')
                return render(request, 'mentee/mentee.html', {
                    'mentorship': None,
                    'status_tasks': {'진행전': [], '진행중': [], '검토요청': [], '완료': []},
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'completion_percentage': 0,
                    'tasks_all': []
                })
        
        # 이 시점에서는 mentorship_id가 URL에 있음이 확실
        print(f"🔍 DEBUG - URL에서 멘토십 ID 확인: {mentorship_id} (타입: {type(mentorship_id)})")
        print(f"🔍 DEBUG - 전체 GET 파라미터: {dict(request.GET)}")
        print(f"🔍 DEBUG - 요청 URL: {request.build_absolute_uri()}")
        
        if mentorship_id == '1':
            print("⚠️  CRITICAL - URL에서 받은 mentorship_id가 '1'입니다!")
            print("⚠️  CRITICAL - 이것은 리다이렉트가 제대로 되지 않았거나 다른 곳에서 덮어쓴 것입니다!")
        
        # 🔧 mentorship_id가 있을 때 is_active 및 사용자 권한 검증
        if mentorship_id:
            # 먼저 해당 멘토십이 현재 사용자의 활성 멘토십인지 확인
            try:
                from core.models import Mentorship
                mentorship_obj = Mentorship.objects.filter(
                    mentorship_id=int(mentorship_id),
                    mentee_id=user_id,
                    is_active=True  # 🔧 is_active=True 체크 필수
                ).first()
                
                if not mentorship_obj:
                    print(f"⚠️ WARNING - 접근 시도된 mentorship_id={mentorship_id}가 사용자({user_id})의 활성 멘토십이 아님")
                    print(f"⚠️ WARNING - 활성 멘토십으로 리다이렉트 시도")
                    
                    # 사용자의 실제 활성 멘토십을 찾아서 리다이렉트
                    active_mentorship = Mentorship.objects.filter(
                        mentee_id=user_id,
                        is_active=True
                    ).first()
                    
                    if active_mentorship:
                        redirect_url = f"{request.path}?mentorship_id={active_mentorship.mentorship_id}"
                        print(f"🚀 DEBUG - 올바른 활성 멘토십으로 리다이렉트: {redirect_url}")
                        messages.warning(request, '비활성 멘토십에 접근할 수 없습니다. 활성 멘토십으로 이동합니다.')
                        return redirect(redirect_url)
                    else:
                        print("⚠️ WARNING - 사용자에게 활성 멘토십이 없음")
                        messages.error(request, '활성화된 멘토십이 없습니다.')
                        return render(request, 'mentee/mentee.html', {
                            'mentorship': None,
                            'status_tasks': {'진행전': [], '진행중': [], '검토요청': [], '완료': []},
                            'total_tasks': 0,
                            'completed_tasks': 0,
                            'completion_percentage': 0,
                            'tasks_all': []
                        })
                else:
                    print(f"✅ INFO - mentorship_id={mentorship_id}가 사용자({user_id})의 활성 멘토십으로 확인됨")
                    
            except Exception as validation_error:
                print(f"⚠️ ERROR - 멘토십 검증 중 오류: {validation_error}")
                messages.error(request, '멘토십 정보 확인 중 오류가 발생했습니다.')
                return redirect('account:login')
        
        # 🚀 FastAPI로 특정 멘토십 상세 정보 가져오기
        mentorship = None
        if mentorship_id:
            print(f"DEBUG - FastAPI로 멘토십 상세 조회 시작... mentorship_id={mentorship_id}")
            
            # FastAPI 우선 사용
            try:
                print(f"DEBUG - FastAPI 멘토십 상세 조회 시도... mentorship_id={mentorship_id}")
                mentorship_response = fastapi_client.get_mentorship(mentorship_id=int(mentorship_id))
                print(f"DEBUG - FastAPI 멘토십 응답: {mentorship_response}")
                
                mentorship = mentorship_response.get('mentorship')
                if mentorship:
                    print(f"DEBUG - FastAPI 멘토십 상세 조회 성공: {mentorship.get('curriculum_title')}")
                else:
                    print("DEBUG - FastAPI에서 멘토십 데이터가 None")
                
            except Exception as fastapi_error:
                print(f"DEBUG - FastAPI 멘토십 상세 조회 실패: {fastapi_error}")
                
                # Django ORM fallback (FastAPI 실패 시에만)
                try:
                    print(f"DEBUG - Django ORM fallback으로 멘토십 상세 조회... mentorship_id={mentorship_id}")
                    from core.models import Mentorship
                    
                    mentorship_obj = Mentorship.objects.filter(mentorship_id=mentorship_id).first()
                    if mentorship_obj:
                        mentorship = {
                            'mentorship_id': mentorship_obj.mentorship_id,
                            'curriculum_title': mentorship_obj.curriculum_title,
                            'total_weeks': mentorship_obj.total_weeks,
                            'start_date': mentorship_obj.start_date.isoformat() if mentorship_obj.start_date else None,
                            'end_date': mentorship_obj.end_date.isoformat() if mentorship_obj.end_date else None,
                        }
                        print(f"DEBUG - Django ORM으로 멘토십 상세 조회 성공: {mentorship_obj.curriculum_title}")
                    else:
                        print(f"DEBUG - Django ORM에서도 mentorship_id={mentorship_id}를 찾을 수 없음")
                        
                except Exception as orm_error:
                    print(f"DEBUG - Django ORM 멘토십 fallback도 실패: {orm_error}")
        
        print(f"DEBUG - 최종 멘토십 확인: {mentorship is not None}")
        print(f"DEBUG - 멘토십 ID 확인: {mentorship_id}")
        
        # 🚀 FastAPI로 태스크 데이터 조회 (멘토십 있을 때만)
        if mentorship_id:
            print(f"DEBUG - FastAPI로 태스크 로딩 시작... mentorship_id={mentorship_id}")
            
            all_tasks = []
            use_django_orm = False
            
            # FastAPI 우선 사용
            try:
                print(f"DEBUG - FastAPI로 태스크 조회 시도... mentorship_id={mentorship_id}")
                tasks_response = fastapi_client.get_task_assigns(mentorship_id=int(mentorship_id))
                print(f"DEBUG - FastAPI 태스크 응답: {tasks_response}")
                
                all_tasks = tasks_response.get('task_assigns', [])
                print(f"DEBUG - FastAPI 태스크 조회 성공: {len(all_tasks)}개")
                use_django_orm = False
                
            except Exception as task_fastapi_error:
                print(f"DEBUG - FastAPI 태스크 조회 실패: {task_fastapi_error}")
                
                # Django ORM fallback (FastAPI 실패 시에만)
                try:
                    print(f"DEBUG - Django ORM fallback으로 태스크 조회 시도... mentorship_id={mentorship_id}")
                    from core.models import TaskAssign
                    all_tasks_qs = TaskAssign.objects.filter(
                        mentorship_id=mentorship_id
                    ).order_by('week', 'order')
                    
                    print(f"DEBUG - Django ORM 쿼리 결과: {all_tasks_qs.count()}개")
                    
                    # Django ORM 데이터를 dict 형태로 변환
                    all_tasks = []
                    for task_obj in all_tasks_qs:
                        task_data = {
                            'task_assign_id': task_obj.task_assign_id,
                            'title': task_obj.title,
                            'description': task_obj.description,
                            'status': task_obj.status,
                            'priority': task_obj.priority,
                            'scheduled_end_date': task_obj.scheduled_end_date.isoformat() if task_obj.scheduled_end_date else None,
                            'scheduled_start_date': task_obj.scheduled_start_date.isoformat() if task_obj.scheduled_start_date else None,
                            'real_start_date': task_obj.real_start_date.isoformat() if task_obj.real_start_date else None,
                            'real_end_date': task_obj.real_end_date.isoformat() if task_obj.real_end_date else None,
                            'week': task_obj.week,
                            'order': task_obj.order,
                            'parent_id': task_obj.parent_id,
                            'guideline': task_obj.guideline,
                        }
                        all_tasks.append(task_data)
                    
                    use_django_orm = True
                    print(f"DEBUG - Django ORM 태스크 조회 성공: {len(all_tasks)}개")
                    
                except Exception as task_orm_error:
                    print(f"DEBUG - Django ORM 태스크 fallback도 실패: {task_orm_error}")
                    all_tasks = []
                    use_django_orm = False

            
            # 🔧 task_list와 동일한 태스크 데이터 처리 로직
            print(f"DEBUG - 전체 태스크 수: {len(all_tasks)}")
            
            # 모든 태스크 처리 (상위 + 하위 태스크 포함)
            processed_tasks = []
            for task in all_tasks:
                # 서브태스크 찾기 (task_list와 동일)
                subtasks = [t for t in all_tasks if t.get('parent_id') == task.get('task_assign_id')]
                
                # D-day 계산 (task_list와 동일)
                dday = None
                dday_text = None
                dday_class = None
                if task.get('scheduled_end_date'):
                    try:
                        from datetime import datetime
                        today = date.today()
                        end_date = datetime.strptime(task['scheduled_end_date'], '%Y-%m-%d').date()
                        diff = (end_date - today).days
                        dday = diff
                        
                        if diff < 0:
                            dday_text = f'D+{abs(diff)}'
                            dday_class = 'urgent'  # 마감일 지남
                        elif diff == 0:
                            dday_text = 'D-Day'
                            dday_class = 'urgent'  # 오늘 마감
                        elif diff <= 3:
                            dday_text = f'D-{diff}'
                            dday_class = 'warning'  # 3일 이내
                        else:
                            dday_text = f'D-{diff}'
                            dday_class = 'normal'  # 여유 있음
                    except:
                        dday_text = None
                        dday_class = None
                
                # 🚀 FastAPI로 메모 정보 로드
                memos = []
                try:
                    print(f"DEBUG - FastAPI로 메모 조회 시도... task_assign_id={task.get('task_assign_id')}")
                    memos_response = fastapi_client.get_memos(task_assign_id=task.get('task_assign_id'))
                    
                    # FastAPI 클라이언트가 직접 List[Memo] 반환
                    if isinstance(memos_response, list):
                        for memo in memos_response:
                            user_info = memo.get('user', {})
                            user_name = '익명'
                            if user_info:
                                last_name = user_info.get('last_name', '')
                                first_name = user_info.get('first_name', '')
                                if last_name or first_name:
                                    user_name = f"{last_name}{first_name}".strip()
                            
                            memos.append({
                                'user': user_name,
                                'comment': memo.get('comment'),
                                'create_date': memo.get('create_date'),
                            })
                    
                    print(f"DEBUG - 태스크 {task.get('task_assign_id')}의 메모 {len(memos)}개 로드")
                except Exception as memo_error:
                    print(f"DEBUG - 메모 조회 실패: {memo_error}")
                    memos = []
                
                # task_list와 동일한 데이터 구조
                task_data = {
                    'id': task.get('task_assign_id'),  # task_list용 필드
                    'task_assign_id': task.get('task_assign_id'),  # mentee용 필드
                    'title': task.get('title'),
                    'desc': task.get('description'),  # task_list용 필드
                    'description': task.get('description'),  # mentee용 필드
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
                    'parent': task.get('parent_id'),
                    'dday': dday,
                    'dday_text': dday_text,
                    'dday_class': dday_class,
                    'memos': memos
                }
                processed_tasks.append(task_data)
            
            print(f"DEBUG - 처리된 태스크 수: {len(processed_tasks)}")
            
            
            # 상위 태스크만 필터링 (진행률 계산용)
            main_tasks = [t for t in processed_tasks if t.get('parent') is None]
            print(f"DEBUG - 상위 태스크 수: {len(main_tasks)}")
            
            # 상태별로 분류 (상위 태스크만)
            status_groups = {
                '진행전': [t for t in main_tasks if t.get('status') == '진행전'],
                '진행중': [t for t in main_tasks if t.get('status') == '진행중'],
                '검토요청': [t for t in main_tasks if t.get('status') == '검토요청'],
                '완료': [t for t in main_tasks if t.get('status') == '완료']
            }
            
            print(f"DEBUG - 상태별 분포: {dict((k, len(v)) for k, v in status_groups.items())}")
            
            # 진행률 계산
            total_tasks = len(main_tasks)
            completed_tasks = len(status_groups['완료'])
            completion_percentage = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
            
            context.update({
                'mentorship': mentorship,  # None일 수도 있음
                'status_tasks': status_groups,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_percentage': completion_percentage,
                'tasks_all': processed_tasks  # 🚨 모든 태스크 (상위+하위) 포함
            })
        else:
            print("DEBUG - 멘토십 ID가 없음. 빈 데이터로 초기화")
            # 빈 데이터로 초기화
            context.update({
                'mentorship': None,
                'status_tasks': {'진행전': [], '진행중': [], '검토요청': [], '완료': []},
                'total_tasks': 0,
                'completed_tasks': 0,
                'completion_percentage': 0,
                'tasks_all': []
            })
            
        print(f"DEBUG - 최종 컨텍스트 확인:")
        print(f"DEBUG - 멘토십: {context.get('mentorship') is not None}")
        print(f"DEBUG - 진행전 태스크 수: {len(context.get('status_tasks', {}).get('진행전', []))}")
        print(f"DEBUG - 진행중 태스크 수: {len(context.get('status_tasks', {}).get('진행중', []))}")
        print(f"DEBUG - 검토요청 태스크 수: {len(context.get('status_tasks', {}).get('검토요청', []))}")
        print(f"DEBUG - 완료 태스크 수: {len(context.get('status_tasks', {}).get('완료', []))}")
        print(f"DEBUG - 전체 태스크 수: {context.get('total_tasks', 0)}")
        print(f"DEBUG - 모든 태스크 수: {len(context.get('tasks_all', []))}")
        
        # 🔍 각 상태별 태스크 제목도 출력 (디버깅용)
        status_tasks = context.get('status_tasks', {})
        for status, tasks in status_tasks.items():
            if tasks:
                print(f"DEBUG - {status} 태스크들:")
                for task in tasks[:3]:  # 최대 3개만 표시
                    print(f"  - ID: {task.get('task_assign_id')}, 제목: {task.get('title')}, D-day: {task.get('dday_text')}, 클래스: {task.get('dday_class')}")

        
        return render(request, 'mentee/mentee.html', context)
        
    except Exception as e:
        messages.error(request, f'데이터를 불러오는 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'mentee/mentee.html', {'mentorship': None})
    
    
@login_required
def task_list(request):
    try:
        mentorship_id = request.GET.get('mentorship_id')
        week_tasks = defaultdict(list)
        selected_task = None
        
        # 해당 멘토-멘티 멘토쉽 정보 확인 
        user_id = getattr(request.user, 'user_id', None)
        user_role = getattr(request.user, 'role', None)
        if not user_id:
            user_data = request.session.get('user_data', {})
            user_id = user_data.get('user_id')
            user_role = user_data.get('role')
        
        if not user_id:
            messages.error(request, '사용자 정보를 찾을 수 없습니다.')
            return redirect('account:login')
        
        from core.models import Mentorship
        final_report = None
        mentorship_obj = Mentorship.objects.filter(mentorship_id=mentorship_id).first()
        print(f"🔍 DEBUG - 현재 사용자({user_id})의 멘토십 정보: {mentorship_obj}")
        if mentorship_obj and mentorship_obj.is_active == False:
            # 온보딩 종료 시 레포트 가져오기
            final_report = getattr(mentorship_obj, 'report', None)
            print(f"🔍 DEBUG - 최종 레포트 정보: {final_report}")
        
        # 🔧 mentorship_id가 있을 때 is_active 및 사용자 권한 검증
        if mentorship_id:
            try:
                from core.models import Mentorship
                
                # 멘토인 경우: mentor_id로 검증
                if user_role == 'mentor':
                    mentorship_obj = Mentorship.objects.filter(
                        mentorship_id=int(mentorship_id),
                        mentor_id=user_id,
                    ).first()
                    
                    if not mentorship_obj:
                        print(f"⚠️ WARNING - 멘토({user_id})가 접근 시도한 mentorship_id={mentorship_id}는 해당 멘토의 멘토십이 아님")
                        messages.error(request, '해당 멘토십에 접근할 권한이 없습니다.')
                        return redirect('mentor:mentor')
                    else:
                        print(f"✅ INFO - 멘토({user_id})가 mentorship_id={mentorship_id}에 정상 접근")
                
                # 멘티인 경우: mentee_id로 검증 (기존 로직)
                else:
                    mentorship_obj = Mentorship.objects.filter(
                        mentorship_id=int(mentorship_id),
                        mentee_id=user_id,
                        is_active=True
                    ).first()
                    
                    if not mentorship_obj:
                        print(f"⚠️ WARNING - task_list에서 접근 시도된 mentorship_id={mentorship_id}가 사용자({user_id})의 활성 멘토십이 아님")
                        
                        # 사용자의 실제 활성 멘토십을 찾아서 리다이렉트
                        active_mentorship = Mentorship.objects.filter(
                            mentee_id=user_id,
                            is_active=True
                        ).first()
                        
                        if active_mentorship:
                            redirect_url = f"{request.path}?mentorship_id={active_mentorship.mentorship_id}"
                            print(f"🚀 DEBUG - task_list에서 올바른 활성 멘토십으로 리다이렉트: {redirect_url}")
                            messages.warning(request, '비활성 멘토십에 접근할 수 없습니다. 활성 멘토십으로 이동합니다.')
                            return redirect(redirect_url)
                        else:
                            messages.error(request, '활성화된 멘토십이 없습니다.')
                            return render(request, 'mentee/task_list.html', {
                                'week_tasks': {},
                                'mentorship_id': None
                            })
                    else:
                        print(f"✅ INFO - task_list에서 mentorship_id={mentorship_id}가 사용자({user_id})의 활성 멘토십으로 확인됨")
                    
            except Exception as validation_error:
                print(f"⚠️ ERROR - task_list에서 멘토십 검증 중 오류: {validation_error}")
                messages.error(request, '멘토십 정보 확인 중 오류가 발생했습니다.')
                return redirect('account:login')
        
        if mentorship_id:
            # FastAPI로 태스크 목록 조회
            tasks_response = fastapi_client.get_task_assigns(mentorship_id=int(mentorship_id))
            all_tasks = tasks_response.get('task_assigns', [])
            
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
                    'task_id': task.get('task_assign_id'),  # 🚨 task_id 필드 추가
                    'task_assign_id': task.get('task_assign_id'),
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
            'user_role': user_role,  # 멘토/멘티 구분을 위한 역할 정보
        }
        return render(request, 'mentee/task_list.html', context)
        
    except Exception as e:
        messages.error(request, f'태스크 목록을 불러오는 중 오류가 발생했습니다: {str(e)}')
        return render(request, 'mentee/task_list.html', {'week_tasks': {}, 'selected_task': None})


# AJAX용 Task 상세정보 API
@login_required
def task_detail(request, task_assign_id):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"태스크 상세 정보 요청 - task_assign_id: {task_assign_id}, 사용자: {request.user}")
        
        # 사용자 정보 확인
        user_data = request.session.get('user_data', {})
        user_id = user_data.get('user_id')
        
        if not user_id and hasattr(request.user, 'user_id'):
            user_id = request.user.user_id
            
        logger.info(f"사용자 ID: {user_id}")
        
        if not user_id:
            logger.warning("사용자 ID를 찾을 수 없음")
            return JsonResponse({'success': False, 'error': '사용자 정보를 찾을 수 없습니다.'}, status=401)
        
        # FastAPI로 태스크 상세 정보 조회
        logger.info(f"FastAPI로 태스크 조회 중... task_assign_id: {task_assign_id}")
        task_info = fastapi_client.get_task_assign(task_assign_id)
        logger.info(f"태스크 정보 조회 성공: {task_info.get('title')}")
        logger.info(f"DEBUG - 받은 task_info 전체: {task_info}")
        logger.info(f"DEBUG - description 필드: '{task_info.get('description')}'")
        logger.info(f"DEBUG - guideline 필드: '{task_info.get('guideline')}'")
        
        data = {
            'id': task_info.get('task_assign_id'),
            'task_assign_id': task_info.get('task_assign_id'),  # 추가
            'title': task_info.get('title'),
            'desc': task_info.get('description'),
            'description': task_info.get('description'),  # 중복이지만 확실히 하기 위해
            'guideline': task_info.get('guideline'),
            'week': task_info.get('week'),
            'order': task_info.get('order'),
            'scheduled_start_date': task_info.get('scheduled_start_date'),
            'scheduled_end_date': task_info.get('scheduled_end_date'),
            'real_start_date': task_info.get('real_start_date'),
            'real_end_date': task_info.get('real_end_date'),
            'status': task_info.get('status'),
            'priority': task_info.get('priority'),
        }
        
        logger.info(f"DEBUG - 생성된 data: {data}")
        
        # 메모 목록 조회 - FastAPI 우선, Django ORM 대체
        memo_list = []
        try:
            logger.info(f"FastAPI로 메모 목록 조회 중... task_assign_id: {task_assign_id}")
            memos_response = fastapi_client.get_memos(task_assign_id=task_assign_id)
            
            # FastAPI 클라이언트가 직접 List[Memo] 반환
            if isinstance(memos_response, list):
                for memo in memos_response:
                    user_info = memo.get('user', {})
                    user_name = '익명'
                    if user_info:
                        last_name = user_info.get('last_name', '')
                        first_name = user_info.get('first_name', '')
                        if last_name or first_name:
                            user_name = f"{last_name}{first_name}".strip()
                    
                    memo_list.append({
                        'user': user_name,
                        'comment': memo.get('comment'),
                        'create_date': memo.get('create_date'),
                    })
            
            logger.info(f"FastAPI로 메모 {len(memo_list)}개 조회 성공")
        except Exception as memo_error:
            logger.warning(f"FastAPI 메모 조회 실패: {memo_error}")
            
            # 🔧 Django ORM 대체 로직
            try:
                logger.info(f"Django ORM으로 메모 조회 중... task_assign_id: {task_assign_id}")
                from core.models import Memo
                
                # 해당 태스크의 메모만 조회 (중요!)  
                django_memos = Memo.objects.filter(task_assign__task_assign_id=task_assign_id).select_related('user').order_by('create_date')
                
                for memo in django_memos:
                    user_name = '알 수 없음'
                    if memo.user:
                        user_name = f"{memo.user.last_name}{memo.user.first_name}"
                    
                    memo_list.append({
                        'user': user_name,
                        'comment': memo.comment,
                        'create_date': memo.create_date.isoformat() if memo.create_date else '',
                    })
                
                logger.info(f"Django ORM으로 메모 {len(memo_list)}개 조회 성공")
            except Exception as django_error:
                logger.error(f"Django ORM 메모 조회 실패: {django_error}")
                memo_list = []
        
        data['memos'] = memo_list
        logger.info(f"최종 메모 개수: {len(memo_list)} (task_assign_id: {task_assign_id})")
        
        logger.info(f"태스크 상세 정보 반환 성공 - ID: {task_assign_id}")
        return JsonResponse({'success': True, 'task': data})
        
    except AuthenticationError as e:
        logger.error(f"인증 오류: {e}")
        return JsonResponse({'success': False, 'error': '인증이 만료되었습니다.'}, status=401)
    except APIError as e:
        logger.error(f"API 오류: {e}")
        return JsonResponse({'success': False, 'error': f'태스크를 찾을 수 없습니다: {str(e)}'}, status=404)
    except Exception as e:
        logger.error(f"예상치 못한 오류 - task_assign_id: {task_assign_id}, 오류: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': f'서버 오류가 발생했습니다: {str(e)}'}, status=500)

# 태스크 상태 업데이트 API (Drag&Drop용) - 🔧 강화된 인증 및 오류 처리
@csrf_exempt
@require_POST
def update_task_status(request, task_id):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔍 태스크 상태 업데이트 요청 시작 - task_id: {task_id}")
        logger.info(f"🔍 요청 헤더: {dict(request.headers)}")
        logger.info(f"🔍 세션 데이터: {request.session.keys()}")
        
        # 🚨 task_id를 정수로 변환
        try:
            task_id = int(task_id)
            logger.info(f"✅ task_id 변환 성공: {task_id}")
        except (ValueError, TypeError):
            logger.error(f"❌ task_id 변환 실패: {task_id}")
            return JsonResponse({
                'success': False, 
                'error': f'유효하지 않은 태스크 ID: {task_id}'
            }, status=400)
        
        # 🔧 강화된 사용자 인증 (세션 + Django User 모두 지원)
        user_data = request.session.get('user_data', {})
        user_id = user_data.get('user_id')
        
        logger.info(f"🔍 세션 user_data: {user_data}")
        
        # Django User 모델에서도 시도
        if not user_id and request.user.is_authenticated:
            if hasattr(request.user, 'user_id'):
                user_id = request.user.user_id
                logger.info(f"🔍 Django User에서 user_id 가져옴: {user_id}")
            else:
                user_id = request.user.id
                logger.info(f"🔍 Django User ID 사용: {user_id}")
            
        logger.info(f"🎯 최종 user_id: {user_id}")
            
        if not user_id:
            logger.error(f"❌ 사용자 ID를 찾을 수 없음")
            return JsonResponse({'success': False, 'error': '사용자 정보를 찾을 수 없습니다.'}, status=401)
        
        # 요청 데이터에서 mentorship_id 가져오기
        try:
            if request.content_type and 'application/json' in request.content_type:
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON 형식이 올바르지 않습니다.'}, status=400)
        
        # 🔧 JavaScript에서 전달받은 mentorship_id 사용
        client_mentorship_id = data.get('mentorship_id')
        logger.info(f"🔍 클라이언트에서 전달받은 mentorship_id: {client_mentorship_id}")
        
        if not client_mentorship_id:
            logger.error("❌ mentorship_id가 전달되지 않음")
            return JsonResponse({'success': False, 'error': 'mentorship_id가 필요합니다.'}, status=400)
            
        # 🔍 사용자가 해당 멘토쉽에 접근 권한이 있는지 확인
        mentorships_result = fastapi_client.get_mentorships(
            mentee_id=user_id,
            is_active=True
        )
        mentorships = mentorships_result.get('mentorships', [])
        
        # 사용자의 멘토쉽 목록에서 요청된 mentorship_id가 있는지 확인
        user_mentorship_ids = [m.get('id') for m in mentorships]
        logger.info(f"🔍 사용자의 활성 멘토쉽 ID들: {user_mentorship_ids}")
        
        if client_mentorship_id not in user_mentorship_ids:
            logger.error(f"❌ 권한 없음: 사용자 {user_id}는 멘토쉽 {client_mentorship_id}에 접근할 수 없음")
            return JsonResponse({'success': False, 'error': '해당 멘토쉽에 대한 권한이 없습니다.'}, status=403)
        
        # 🎯 클라이언트에서 요청한 mentorship_id 사용 (검증 완료)
        mentorship_id = client_mentorship_id
        logger.info(f"✅ 사용할 mentorship_id: {mentorship_id}")
        tasks_result = fastapi_client.get_task_assigns(mentorship_id=mentorship_id)
        all_tasks = tasks_result.get('task_assigns', [])
        
        # 🔍 요청된 task_id가 존재하는지 확인
        target_task = next((t for t in all_tasks if t.get('task_assign_id') == task_id), None)
        
        if not target_task:
            logger.warning(f"❌ Task ID {task_id}를 찾을 수 없음. 사용 가능한 ID들: {[t.get('task_assign_id') for t in all_tasks]}")
            return JsonResponse({
                'success': False, 
                'error': f'태스크 ID {task_id}를 찾을 수 없습니다.',
                'available_task_ids': [t.get('task_assign_id') for t in all_tasks]
            }, status=404)
        
        # 🔍 권한 확인 (해당 태스크가 사용자의 멘토쉽에 속하는지)
        if target_task.get('mentorship_id') != mentorship_id:
            return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
        
        # 🚨 FastAPI 조회 시도 (실패 시 즉시 Django ORM으로 전환)
        logger.info(f"🔍 FastAPI로 개별 태스크 조회 시도: task_id={task_id}")
        task_result = None
        use_fastapi = True
        
        try:
            task_result = fastapi_client.get_task_assign(task_id)
            logger.info(f"✅ FastAPI 개별 태스크 조회 성공: {task_result.get('title')}")
        except Exception as api_error:
            logger.error(f"❌ FastAPI 개별 태스크 조회 실패: {api_error}")
            logger.info(f"🔄 Django ORM 개별 태스크 조회로 전환...")
            
            # 🔧 Django ORM으로 즉시 전환 (FastAPI 스키마에 맞는 완전한 데이터)
            try:
                from core.models import TaskAssign
                task_obj = TaskAssign.objects.get(task_assign_id=task_id)
                task_result = {
                    'task_assign_id': task_obj.task_assign_id,
                    'title': task_obj.title,
                    'description': task_obj.description,
                    'guideline': task_obj.guideline,
                    'week': task_obj.week,
                    'order': task_obj.order,
                    'scheduled_start_date': task_obj.scheduled_start_date.isoformat() if task_obj.scheduled_start_date else None,
                    'scheduled_end_date': task_obj.scheduled_end_date.isoformat() if task_obj.scheduled_end_date else None,
                    'real_start_date': task_obj.real_start_date.isoformat() if task_obj.real_start_date else None,
                    'real_end_date': task_obj.real_end_date.isoformat() if task_obj.real_end_date else None,
                    'status': task_obj.status,
                    'priority': task_obj.priority,
                    'mentorship_id': task_obj.mentorship_id,
                }
                use_fastapi = False
                logger.info(f"✅ Django ORM 개별 태스크 조회 성공: {task_obj.title}")
                logger.info(f"🔧 Django ORM 태스크 데이터: {task_result}")
                
            except Exception as orm_error:
                logger.error(f"❌ Django ORM 개별 태스크 조회도 실패: {orm_error}")
                return JsonResponse({
                    'success': False, 
                    'error': f'태스크 정보 조회 실패 (FastAPI: {api_error}, Django ORM: {orm_error})',
                    'debug_info': {
                        'requested_task_id': task_id,
                        'mentorship_id': mentorship_id,
                        'available_task_ids': [t.get('task_assign_id') for t in all_tasks[:10]],
                        'total_tasks': len(all_tasks)
                    }
                }, status=500)
        
        # 이미 위에서 data 파싱 완료
        
        new_status = data.get('status', '').strip()
        new_description = data.get('description', '').strip()
        valid_statuses = ['진행전', '진행중', '검토요청', '완료']
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False, 
                'error': f'유효하지 않은 상태입니다. 가능한 상태: {valid_statuses}'
            }, status=400)
        
        # 🔧 FastAPI 스키마에 맞는 업데이트 데이터 준비
        old_status = task_result.get('status')
        task_mentorship_id = task_result.get('mentorship_id')
        
        logger.info(f"🔍 태스크 정보:")
        logger.info(f"🔍 - task_id: {task_id}")
        logger.info(f"🔍 - 현재 상태: {old_status}")
        logger.info(f"🔍 - 새로운 상태: {new_status}")
        logger.info(f"🔍 - 태스크의 mentorship_id: {task_mentorship_id}")
        logger.info(f"🔍 - 요청된 mentorship_id: {mentorship_id}")
        
        # 🚀 FastAPI TaskAssignCreate 스키마에 맞는 완전한 데이터 구성
        update_data = {
            'title': task_result.get('title') or '',
            'description': new_description or task_result.get('description') or '', 
            'guideline': task_result.get('guideline') or '',
            'week': task_result.get('week', 1),  # 기본값 1
            'order': task_result.get('order', 1),  # 기본값 1
            'scheduled_start_date': task_result.get('scheduled_start_date'),
            'scheduled_end_date': task_result.get('scheduled_end_date'),
            'real_start_date': task_result.get('real_start_date'),
            'real_end_date': task_result.get('real_end_date'),
            'status': new_status,  # 🎯 새로운 상태
            'priority': task_result.get('priority', '중'),  # 기본값 '중'
            'mentorship_id': mentorship_id,  # 🎯 클라이언트에서 요청한 mentorship_id 사용
        }
        
        # 🔧 None 값 제거 (FastAPI에서 Optional 필드 처리)
        clean_update_data = {}
        for key, value in update_data.items():
            if value is not None:
                clean_update_data[key] = value
        
        update_data = clean_update_data
        
        logger.info(f"🔄 상태 변경: {old_status} -> {new_status}")
        logger.info(f"🔧 FastAPI 업데이트 데이터: {update_data}")
        
        # 🔧 날짜 필드 업데이트 로직
        if new_status == '진행중' and not task_result.get('real_start_date'):
            from datetime import datetime
            update_data['real_start_date'] = datetime.now().date().isoformat()
            logger.info(f"📅 실제 시작일 설정: {update_data['real_start_date']}")
        elif new_status == '완료' and not task_result.get('real_end_date'):
            from datetime import datetime
            update_data['real_end_date'] = datetime.now().date().isoformat()
            logger.info(f"📅 실제 완료일 설정: {update_data['real_end_date']}")
        
        # 🔧 데이터 소스에 따라 업데이트 방식 선택
        if use_fastapi:
        # FastAPI로 태스크 상태 업데이트
            try:
                result = fastapi_client.update_task_assign(task_id, update_data)
                logger.info(f"✅ FastAPI 태스크 상태 업데이트 성공 - {old_status} -> {new_status}")
                # ✅ 검토요청 알람 생성
                if new_status == '검토요청':
                    try:
                        create_review_request_alarm(mentorship_id, task_result.get('title'))
                    except Exception as alarm_error:
                        logger.error(f"❌ 검토요청 알람 생성 실패: {alarm_error}")
                
                # 🤖 Agent 시스템 통합: 상태 변화 이벤트 트리거
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                    from agent_integration import agent_integrator
                    agent_integrator.trigger_status_change_event(
                        task_id=task_id,
                        old_status=old_status,
                        new_status=new_status,
                        user_id=user_id
                    )
                    logger.info(f"🤖 Agent 시스템 이벤트 트리거 성공: {old_status} -> {new_status}")
                except Exception as agent_error:
                    logger.error(f"🤖 Agent 시스템 이벤트 트리거 실패: {agent_error}")
                
                return JsonResponse({
                    'success': True,
                    'old_status': old_status,
                    'new_status': new_status,
                    'task_id': task_id,
                    'message': f'태스크 상태가 "{old_status}"에서 "{new_status}"로 변경되었습니다.',
                    'method': 'fastapi'
                })
                
            except Exception as update_error:
                logger.error(f"❌ FastAPI 상태 업데이트 실패: {update_error}")
                logger.info(f"🔄 FastAPI 업데이트 실패로 Django ORM Fallback 시도...")
                use_fastapi = False  # Django ORM으로 전환
        
        if not use_fastapi:
            # Django ORM으로 직접 업데이트
            try:
                from core.models import TaskAssign
                from datetime import datetime
                
                logger.info(f"🔧 Django ORM으로 태스크 상태 업데이트 시도...")
                task_obj = TaskAssign.objects.get(task_assign_id=task_id)
                task_obj.status = new_status
                if new_description:
                    task_obj.description = new_description  # ✨ 추가
                
                # 날짜 필드 업데이트
                if new_status == '진행중' and not task_obj.real_start_date:
                    task_obj.real_start_date = datetime.now().date()
                    logger.info(f"📅 Django ORM 실제 시작일 설정")
                elif new_status == '완료' and not task_obj.real_end_date:
                    task_obj.real_end_date = datetime.now().date()
                    logger.info(f"📅 Django ORM 실제 완료일 설정")
                
                task_obj.save()
                logger.info(f"✅ Django ORM 태스크 상태 업데이트 성공 - {old_status} -> {new_status}")
                
                # ✅ 검토요청 알람 생성
                if new_status == '검토요청':
                    try:
                        create_review_request_alarm(mentorship_id, task_result.get('title'))
                    except Exception as alarm_error:
                        logger.error(f"❌ 검토요청 알람 생성 실패: {alarm_error}")
                
                # 🤖 Agent 시스템 통합: 상태 변화 이벤트 트리거 (Django ORM)
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                    from agent_integration import agent_integrator
                    agent_integrator.trigger_status_change_event(
                        task_id=task_id,
                        old_status=old_status,
                        new_status=new_status,
                        user_id=user_id
                    )
                    logger.info(f"🤖 Agent 시스템 이벤트 트리거 성공 (Django ORM): {old_status} -> {new_status}")
                except Exception as agent_error:
                    logger.error(f"🤖 Agent 시스템 이벤트 트리거 실패 (Django ORM): {agent_error}")
                
                return JsonResponse({
                    'success': True,
                    'old_status': old_status,
                    'new_status': new_status,
                    'task_id': task_id,
                    'message': f'태스크 상태가 "{old_status}"에서 "{new_status}"로 변경되었습니다.',
                    'method': 'django_orm',
                    'notice': 'FastAPI 연동 문제로 Django ORM을 사용했습니다.'
                })
                
            except Exception as orm_error:
                logger.error(f"❌ Django ORM 상태 업데이트도 실패: {orm_error}")
                return JsonResponse({
                    'success': False, 
                    'error': f'상태 업데이트 실패: {str(orm_error)}'
                }, status=500)
        
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)
    

    
def create_review_request_alarm(mentorship_id, task_title):
    import logging
    logger = logging.getLogger(__name__)
    try:
        from core.models import Mentorship, Alarm, User
        mentorship_obj = Mentorship.objects.filter(
            mentorship_id=mentorship_id,
            is_active=True
        ).first()
        if mentorship_obj:
            mentee = User.objects.get(user_id=mentorship_obj.mentee_id)
            mentor = User.objects.get(user_id=mentorship_obj.mentor_id)
            full_name = f"{mentee.last_name}{mentee.first_name}"
            Alarm.objects.create(
                user=mentor,
                message=f"{full_name} 멘티가 '{task_title}' 태스크를 검토요청했습니다.",
                is_active=True
            )
            return True
    except Exception as e:
        logger.error(f"검토요청 알람 생성 실패: {e}")
    return False



@login_required 
def change_task_status_for_test(request):
    """🧪 테스트용: 태스크 상태 변경 유틸리티"""
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        new_status = request.POST.get('status')
        
        try:
            from core.models import TaskAssign
            task = TaskAssign.objects.get(task_assign_id=task_id)
            task.status = new_status
            task.save()
            
            messages.success(request, f'태스크 "{task.title}"의 상태를 "{new_status}"로 변경했습니다.')
            
        except TaskAssign.DoesNotExist:
            messages.error(request, f'태스크 ID {task_id}를 찾을 수 없습니다.')
        except Exception as e:
            messages.error(request, f'오류 발생: {str(e)}')
            
        return redirect('mentee:change_task_status_for_test')
    
    # GET 요청: 태스크 목록 표시
    from core.models import TaskAssign
    
    # 멘토십 2의 상위 태스크들만 가져오기
    tasks = TaskAssign.objects.filter(
        mentorship_id=2, 
        parent_id__isnull=True
    ).order_by('week', 'order')
    
    return render(request, 'mentee/test_status_change.html', {'tasks': tasks})

@login_required
def debug_memos(request):
    """메모 디버깅용 임시 뷰"""
    from core.models import Memo, TaskAssign
    from django.http import HttpResponse
    
    # 모든 메모 조회
    memos = Memo.objects.select_related('task_assign', 'user').all()
    
    html = "<html><body><h1>메모 디버깅</h1>"
    html += f"<p>총 메모 개수: {memos.count()}</p>"
    
    # 태스크별 메모 개수
    html += "<h2>태스크별 메모 개수</h2>"
    from django.db.models import Count
    task_memo_counts = Memo.objects.values('task_assign__task_assign_id').annotate(count=Count('memo_id'))
    
    for item in task_memo_counts:
        task_id = item['task_assign__task_assign_id']
        count = item['count']
        html += f"<p>Task {task_id}: {count}개 메모</p>"
    
    # 최근 메모 10개
    html += "<h2>최근 메모 10개</h2>"
    recent_memos = memos.order_by('-create_date')[:10]
    
    html += "<table border='1'><tr><th>메모ID</th><th>태스크ID</th><th>사용자</th><th>내용</th><th>생성일</th></tr>"
    for memo in recent_memos:
        user_name = f"{memo.user.last_name}{memo.user.first_name}" if memo.user else "알수없음"
        html += f"<tr><td>{memo.memo_id}</td><td>{memo.task_assign.task_assign_id if memo.task_assign else 'None'}</td><td>{user_name}</td><td>{memo.comment[:50]}...</td><td>{memo.create_date}</td></tr>"
    
    html += "</table></body></html>"
    
    return HttpResponse(html)

def debug_mentorship(request):
    """멘토십 정보 디버깅용 뷰"""
    from core.models import Mentorship, TaskAssign
    import json
    
    try:
        # 모든 멘토십 조회
        mentorships = Mentorship.objects.all().values()
        mentorships_list = list(mentorships)
        
        # 특정 멘토십의 태스크들 조회
        mentorship_id = request.GET.get('mentorship_id', '2')
        tasks = []
        if mentorship_id.isdigit():
            tasks = TaskAssign.objects.filter(mentorship_id=int(mentorship_id)).values()
            tasks = list(tasks)
        
        html = f"""
        <h2>멘토십 디버깅</h2>
        <h3>모든 멘토십:</h3>
        <pre>{json.dumps(mentorships_list, indent=2, ensure_ascii=False)}</pre>
        
        <h3>멘토십 ID {mentorship_id}의 태스크들:</h3>
        <pre>{json.dumps(tasks, indent=2, ensure_ascii=False, default=str)}</pre>
        
        <hr>
        <p><a href="?mentorship_id=1">멘토십 1 확인</a> | 
           <a href="?mentorship_id=2">멘토십 2 확인</a> | 
           <a href="?mentorship_id=3">멘토십 3 확인</a></p>
        """
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"오류: {str(e)}")

def test_task_list(request):
    """하위 태스크 생성 테스트용 뷰"""
    try:
        mentorship_id = request.GET.get('mentorship_id', 2)  # 기본값 2
        week_tasks = defaultdict(list)
        
        if mentorship_id:
            # FastAPI로 태스크 목록 조회
            tasks_response = fastapi_client.get_task_assigns(mentorship_id=int(mentorship_id))
            all_tasks = tasks_response.get('task_assigns', [])
            
            for task in all_tasks:
                # 서브태스크 찾기
                subtasks = [t for t in all_tasks if t.get('parent_id') == task.get('task_assign_id')]
                
                task_data = {
                    'task_id': task.get('task_assign_id'),
                    'task_assign_id': task.get('task_assign_id'),
                    'title': task.get('title'),
                    'desc': task.get('description'),
                    'description': task.get('description'),
                    'subtasks': subtasks,
                    'parent': task.get('parent_id'),
                }
                week_tasks[task.get('week', 1)].append(task_data)
        
        context = {
            'week_tasks': dict(week_tasks),
            'mentorship_id': mentorship_id,
        }
        return render(request, 'mentee/task_list_test.html', context)
        
    except Exception as e:
        print(f"test_task_list 오류: {e}")
        return render(request, 'mentee/task_list_test.html', {'week_tasks': {}, 'mentorship_id': 2})

@login_required
@require_POST
def complete_onboarding(request):
    """온보딩 종료 및 최종 보고서 생성 처리"""
    try:
        data = json.loads(request.body)
        mentorship_id = data.get('mentorship_id')
        
        if not mentorship_id:
            return JsonResponse({
                'success': False,
                'error': '멘토십 ID가 필요합니다.'
            }, status=400)

        # 현재 사용자 정보 확인
        user_data = request.session.get('user_data', {})
        user_id = user_data.get('user_id') or request.user.user_id

        # 멘토십 조회 및 권한 확인
        try:
            mentorship = Mentorship.objects.get(
                mentorship_id=mentorship_id,
                mentee_id=user_id,
                is_active=True
            )
        except Mentorship.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 멘토십을 찾을 수 없거나 접근 권한이 없습니다.'
            }, status=404)

        # 멘토십 비활성화
        mentorship.is_active = False
        mentorship.save()

        # report_langgraph workflow 실행
        try:
            final_state = run_report_workflow(user_id=user_id)
            if final_state:
                return JsonResponse({
                    'success': True,
                    'message': '온보딩이 종료되었으며 최종 보고서가 생성되었습니다.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': '보고서 생성 중 오류가 발생했습니다.'
                }, status=500)
        except Exception as workflow_error:
            print(f"Workflow 실행 오류: {workflow_error}")
            # 워크플로우 실패 시에도 온보딩은 종료된 상태 유지
            return JsonResponse({
                'success': True,
                'message': '온보딩은 종료되었으나, 보고서 생성 중 오류가 발생했습니다.'
            })

    except Exception as e:
        print(f"온보딩 종료 처리 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'처리 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

