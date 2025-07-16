<<<<<<< Updated upstream
from django.shortcuts import render

def chatbot(request):
    return render(request, 'common/chatbot.html')
=======
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from core.models import (
    User, ChatSession, ChatMessage, Docs, 
    TaskAssign, Mentorship, Department, Curriculum
)
from .api_client import (
    call_fastapi_auth, 
    call_fastapi_users, 
    call_fastapi_user_stats,
    call_fastapi_mentorship_stats,
    call_fastapi_task_stats,
    get_fastapi_client
)
from datetime import date, timedelta
import json
import logging

logger = logging.getLogger(__name__)

# FastAPI 연동 뷰들 - 유지
@login_required
def api_dashboard(request):
    """FastAPI 연동 대시보드"""
    context = {
        'title': 'API 대시보드',
        'fastapi_url': settings.FASTAPI_BASE_URL,
    }
    return render(request, 'common/api_dashboard.html', context)

@login_required
def api_test_auth(request):
    """FastAPI 인증 테스트 - FastAPI로 프록시"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            import requests
            
            # FastAPI로 요청 전송
            response = requests.post(
                f'{settings.FASTAPI_BASE_URL}/api/v1/common/api/test/auth',
                json={
                    'email': email,
                    'password': password
                },
                headers={
                    'Authorization': f'Bearer {request.user.email}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                return JsonResponse(response.json())
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
                return JsonResponse({
                    'success': False,
                    'error': error_data.get('detail', '인증 실패'),
                    'message': 'FastAPI 인증 실패'
                }, status=400)
        except Exception as e:
            logger.error(f"인증 테스트 API 에러: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'FastAPI 인증 실패'
            }, status=400)
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

@login_required
def api_test_users(request):
    """FastAPI 사용자 목록 테스트"""
    token = request.GET.get('token')
    if not token:
        return JsonResponse({'error': 'JWT 토큰이 필요합니다.'}, status=400)
    
    try:
        page = int(request.GET.get('page', 1))
        size = int(request.GET.get('size', 20))
        
        result = call_fastapi_users(token, page, size)
        return JsonResponse({
            'success': True,
            'data': result,
            'message': 'FastAPI 사용자 목록 조회 성공'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'FastAPI 사용자 목록 조회 실패'
        }, status=400)

@login_required
def api_test_stats(request):
    """FastAPI 통계 데이터 테스트"""
    token = request.GET.get('token')
    if not token:
        return JsonResponse({'error': 'JWT 토큰이 필요합니다.'}, status=400)
    
    try:
        # 여러 통계 데이터를 병렬로 조회
        user_stats = call_fastapi_user_stats(token)
        mentorship_stats = call_fastapi_mentorship_stats(token)
        task_stats = call_fastapi_task_stats(token)
        
        return JsonResponse({
            'success': True,
            'data': {
                'user_stats': user_stats,
                'mentorship_stats': mentorship_stats,
                'task_stats': task_stats
            },
            'message': 'FastAPI 통계 데이터 조회 성공'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'FastAPI 통계 데이터 조회 실패'
        }, status=400)

@login_required
def api_proxy(request, endpoint):
    """FastAPI로의 프록시 요청"""
    token = request.META.get('HTTP_AUTHORIZATION')
    if token and token.startswith('Bearer '):
        token = token[7:]  # 'Bearer ' 제거
    
    try:
        with get_fastapi_client() as client:
            if request.method == 'GET':
                result = client.get(f"/{endpoint}", request.GET.dict(), token)
            elif request.method == 'POST':
                data = json.loads(request.body) if request.body else {}
                result = client.post(f"/{endpoint}", data, token)
            elif request.method == 'PUT':
                data = json.loads(request.body) if request.body else {}
                result = client.put(f"/{endpoint}", data, token)
            elif request.method == 'DELETE':
                result = client.delete(f"/{endpoint}", token)
            else:
                return JsonResponse({'error': '지원하지 않는 HTTP 메서드입니다.'}, status=405)
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"API 프록시 에러: {endpoint} - {e}")
        return JsonResponse({
            'error': str(e),
            'message': 'FastAPI 프록시 요청 실패'
        }, status=500)

@login_required
def integrated_dashboard(request):
    """Django + FastAPI 통합 대시보드"""
    context = {
        'title': '통합 대시보드',
        'user': request.user,
        'fastapi_url': settings.FASTAPI_BASE_URL,
    }
    
    # FastAPI에서 추가 데이터를 가져올 수 있지만, 토큰이 필요하므로 
    # 클라이언트 사이드에서 AJAX로 처리하는 것이 좋습니다.
    
    return render(request, 'common/integrated_dashboard.html', context)

# 기본 프론트엔드 뷰들
@login_required
def chatbot(request):
    """챗봇 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 메시지 전송 처리
    if request.method == 'POST':
        message_text = request.POST.get('message')
        session_id = request.POST.get('session_id')
        
        if message_text:
            # 세션이 없으면 새로 생성
            if not session_id:
                session = ChatSession.objects.create(
                    user=user,
                    summary=message_text[:50] + '...' if len(message_text) > 50 else message_text
                )
                session_id = session.session_id
            else:
                try:
                    session = ChatSession.objects.get(session_id=session_id, user=user)
                except ChatSession.DoesNotExist:
                    session = ChatSession.objects.create(
                        user=user,
                        summary=message_text[:50] + '...' if len(message_text) > 50 else message_text
                    )
                    session_id = session.session_id
            
            # 사용자 메시지 저장
            ChatMessage.objects.create(
                session_id=session_id,
                message_type='user',
                message_text=message_text
            )
            
            # 간단한 챗봇 응답 (실제로는 AI 모델 연동 가능)
            bot_response = generate_chatbot_response(message_text, user)
            ChatMessage.objects.create(
                session_id=session_id,
                message_type='chatbot',
                message_text=bot_response
            )
        
        return redirect('common:chatbot')
    
    # 사용자의 채팅 세션 목록 가져오기
    chat_sessions_data = []
    sessions = ChatSession.objects.filter(user=user).order_by('-session_id')
    
    for session in sessions:
        messages = ChatMessage.objects.filter(session=session).order_by('message_id')
        chat_sessions_data.append({
            'session': session,
            'messages': messages
        })
    
    # 멘토인 경우 담당 멘티 목록 제공
    mentees = []
    if user.role == 'mentor':
        mentorships = Mentorship.objects.filter(
            mentor_id=user.user_id,
            is_active=True
        )
        for mentorship in mentorships:
            try:
                mentee = User.objects.get(user_id=mentorship.mentee_id)
                mentees.append({
                    'name': f"{mentee.last_name}{mentee.first_name}",
                    'email': mentee.email,
                    'department': mentee.department.department_name if mentee.department else '',
                    'mentorship_id': mentorship.mentorship_id
                })
            except User.DoesNotExist:
                continue
    
    context = {
        'user': request.user,
        'chat_sessions': chat_sessions_data,
        'mentees': mentees,  # 멘토의 담당 멘티 목록 추가
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '챗봇'
    }
    return render(request, 'common/chatbot.html', context)
>>>>>>> Stashed changes

@login_required
def doc(request):
<<<<<<< Updated upstream
    return render(request, 'common/doc.html')
=======
    """문서 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # 사용자가 접근할 수 있는 문서 목록 가져오기
    docs_query = Docs.objects.all()
    
    # 공통 문서 + 본인 부서 문서
    if user.department:
        docs_query = docs_query.filter(
            Q(common_doc=True) | Q(department=user.department)
        )
    else:
        docs_query = docs_query.filter(common_doc=True)
    
    core_docs = docs_query.order_by('-create_time')
    
    context = {
        'user': request.user,
        'core_docs': core_docs,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '문서'
    }
    return render(request, 'common/doc.html', context)
>>>>>>> Stashed changes

@login_required
@require_http_methods(["POST"])
def doc_upload(request):
    """문서 업로드 처리 - FastAPI로 프록시"""
    try:
        # FormData에서 데이터 가져오기
        uploaded_file = request.FILES.get('file')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        tags = request.POST.get('tags', '')
        common_doc = request.POST.get('common_doc', 'false').lower() == 'true'
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': '파일명이 필요합니다.'
            }, status=400)
        
        # FastAPI로 파일 업로드 요청 전송
        import requests
        
        files = {'file': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)} if uploaded_file else {}
        data = {
            'name': name,
            'description': description,
            'tags': tags,
            'common_doc': common_doc
        }
        
        response = requests.post(
            f'{settings.FASTAPI_BASE_URL}/api/v1/common/doc/upload',
            files=files,
            data=data,
            headers={
                'Authorization': f'Bearer {request.user.email}'
            }
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
            return JsonResponse({
                'success': False,
                'error': error_data.get('detail', '문서 업로드 중 오류가 발생했습니다.')
            }, status=500)
        
    except Exception as e:
        logger.error(f"문서 업로드 API 에러: {e}")
        return JsonResponse({
            'success': False,
            'error': f'문서 업로드 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

 
@login_required
def task_add(request):
<<<<<<< Updated upstream
    return render(request, 'common/task_add.html')
=======
    """과제 추가 페이지 - 실제 데이터베이스 데이터 가져오기"""
    user = request.user
    
    # POST 요청 처리 (과제 생성)
    if request.method == 'POST':
        title = request.POST.get('title')
        detail = request.POST.get('detail')
        status = request.POST.get('status', '진행 전')
        level = request.POST.get('level')
        xp = request.POST.get('xp')
        deadline = request.POST.get('deadline')
        
        # 현재 사용자의 활성 멘토십 찾기
        mentorship = None
        if user.role == 'mentee':
            mentorship = Mentorship.objects.filter(
                mentee_id=user.user_id,
                is_active=True
            ).first()
        elif user.role == 'mentor':
            # 멘토의 경우 특정 멘토십 선택 필요 (여기서는 첫 번째로 설정)
            mentorship = Mentorship.objects.filter(
                mentor_id=user.user_id,
                is_active=True
            ).first()
        
        if mentorship and title and detail and level and xp and deadline:
            try:
                TaskAssign.objects.create(
                    mentorship_id=mentorship,
                    title=title,
                    description=detail,
                    status=status,
                    priority=level,
                    week=1,  # 기본값
                    order=1,  # 기본값
                    end_date=deadline
                )
                messages.success(request, '과제가 성공적으로 생성되었습니다.')
                
                # 역할에 따라 리다이렉트
                if user.role == 'mentee':
                    return redirect('mentee:mentee')
                elif user.role == 'mentor':
                    return redirect('mentor:mentor')
                else:
                    return redirect('common:task_add')
            except Exception as e:
                messages.error(request, f'과제 생성 중 오류가 발생했습니다: {str(e)}')
        else:
            messages.error(request, '모든 필드를 입력해주세요.')
    
    # 사용자의 멘토십 정보 가져오기
    mentorship = None
    if user.role == 'mentee':
        mentorship = Mentorship.objects.filter(
            mentee_id=user.user_id,
            is_active=True
        ).first()
    elif user.role == 'mentor':
        mentorship = Mentorship.objects.filter(
            mentor_id=user.user_id,
            is_active=True
        ).first()
    
    context = {
        'user': request.user,
        'mentorship': mentorship,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '과제 추가'
    }
    return render(request, 'common/task_add.html', context)

# 헬퍼 함수들
def generate_chatbot_response(message, user):
    """간단한 챗봇 응답 생성 - 사용자 정보 기반"""
    message_lower = message.lower()
    
    if '안녕' in message_lower or '헬로' in message_lower or 'hello' in message_lower:
        return f"안녕하세요 {user.last_name}{user.first_name}님! 온보딩 챗봇입니다. 어떤 도움이 필요하신가요?"
    elif '과제' in message_lower or 'task' in message_lower:
        if user.role == 'mentee':
            return "과제 관련 질문이시군요! 현재 진행 중인 과제나 완료된 과제에 대해 문의하실 수 있습니다. 멘티 대시보드에서 과제 현황을 확인하실 수 있습니다."
        elif user.role == 'mentor':
            return "과제 관련 질문이시군요! 멘토로서 멘티들의 과제 진행상황을 확인하거나 피드백을 제공하실 수 있습니다."
        else:
            return "과제 관련 질문이시군요! 현재 진행 중인 과제나 완료된 과제에 대해 문의하실 수 있습니다."
    elif '멘토' in message_lower:
        if user.role == 'mentee':
            return "멘토 관련 질문이시네요. 멘토와의 소통이나 피드백에 대해 도움을 드릴 수 있습니다. 멘토에게 궁금한 점이 있으시면 언제든지 문의해주세요."
        elif user.role == 'mentor':
            return "멘토 관련 질문이시네요. 멘토로서 멘티들을 효과적으로 지도하는 방법이나 커리큘럼 관리에 대해 도움을 드릴 수 있습니다."
        else:
            return "멘토 관련 질문이시네요. 멘토와의 소통이나 피드백에 대해 도움을 드릴 수 있습니다."
    elif '멘티' in message_lower and user.role == 'mentor':
        mentorship_count = Mentorship.objects.filter(mentor_id=user.user_id, is_active=True).count()
        return f"멘티 관련 질문이시군요! 현재 {mentorship_count}명의 멘티를 담당하고 계시네요. 멘티 관리나 진행상황에 대해 도움을 드릴 수 있습니다."
    elif '문서' in message_lower or '자료' in message_lower:
        return "문서나 자료 관련 질문이시군요. 온보딩 관련 문서들을 문서 페이지에서 확인하실 수 있습니다. 부서별 문서와 공통 문서가 준비되어 있습니다."
    elif '도움' in message_lower or 'help' in message_lower:
        return f"도움이 필요하시군요! {user.role} 역할로 온보딩 과정에서 궁금한 점이나 문제가 있으시면 언제든지 말씀해주세요."
    else:
        return "네, 말씀하신 내용을 잘 들었습니다. 더 구체적인 질문이 있으시면 언제든지 말씀해주세요!"

# 임시 더미 함수들 - URL 호환성 유지
def doc_delete(request, doc_id):
    """문서 삭제 - 실제 데이터베이스 처리"""
    if request.method == 'POST':
        try:
            doc = Docs.objects.get(docs_id=doc_id)
            # 사용자가 해당 문서를 삭제할 권한이 있는지 확인
            if (request.user.department and doc.department and 
                request.user.department.pk == doc.department.pk):
                doc.delete()
                messages.success(request, '문서가 성공적으로 삭제되었습니다.')
            else:
                messages.error(request, '문서를 삭제할 권한이 없습니다.')
        except Docs.DoesNotExist:
            messages.error(request, '문서를 찾을 수 없습니다.')
        except Exception as e:
            messages.error(request, f'문서 삭제 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('common:doc')
>>>>>>> Stashed changes
