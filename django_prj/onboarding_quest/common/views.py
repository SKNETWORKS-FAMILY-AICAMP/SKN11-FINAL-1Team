from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
@csrf_exempt
def doc_upload(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            title = data.get('name')
            description = data.get('description')
            tags = data.get('tags')
            common_doc = data.get('common_doc', False)
            department = request.user.department
            if not title or not department:
                return JsonResponse({'success': False, 'error': '필수 정보 누락'})
            doc = Docs.objects.create(
                title=title,
                description=description,
                department=department,
                file_path='',  # 파일 업로드 미구현, 경로는 빈 값
                common_doc=common_doc
            )
            # 태그 필드가 있으면 추가 구현 필요
            return JsonResponse({'success': True, 'doc_id': doc.docs_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})

from django.shortcuts import render, redirect
from core.models import Docs, ChatSession, ChatMessage

def chatbot(request):
    if request.method == 'POST':
        # 메시지 전송 처리
        if request.user.is_authenticated:
            message_text = request.POST.get('message', '').strip()
            if message_text:
                # 사용자의 최신 세션을 가져오거나 새로 생성
                latest_session = ChatSession.objects.filter(user=request.user).order_by('-session_id').first()
                
                if not latest_session:
                    # 첫 번째 세션 생성
                    session = ChatSession.objects.create(
                        user=request.user,
                        summary=message_text[:50] + '...' if len(message_text) > 50 else message_text
                    )
                else:
                    session = latest_session
                
                # 사용자 메시지 저장
                ChatMessage.objects.create(
                    session=session,
                    message_type='user',
                    message_text=message_text
                )
                
                # 간단한 챗봇 응답 (실제로는 AI 모델과 연동)
                bot_response = f"'{message_text}'에 대한 답변을 준비 중입니다."
                ChatMessage.objects.create(
                    session=session,
                    message_type='chatbot',
                    message_text=bot_response
                )
        
        return redirect('common:chatbot')
    
    # GET 요청 처리
    chat_sessions = []
    if request.user.is_authenticated:
        # 로그인한 사용자의 채팅 세션들을 가져옴
        sessions = ChatSession.objects.filter(user=request.user).order_by('-session_id')
        for session in sessions:
            # 각 세션의 메시지들을 가져옴
            messages = ChatMessage.objects.filter(session=session).order_by('create_time')
            chat_sessions.append({
                'session': session,
                'messages': messages
            })
    
    return render(request, 'common/chatbot.html', {
        'chat_sessions': chat_sessions
    })

def doc(request):
    user = request.user
    # 공통문서
    common_docs = Docs.objects.filter(common_doc=True)
    # 유저 부서 문서 (공통문서가 아닌 것)
    dept_docs = Docs.objects.filter(department=user.department, common_doc=False) if user.is_authenticated and user.department else Docs.objects.none()
    # 합치기 (중복 방지)
    all_docs = list(common_docs) + [doc for doc in dept_docs if doc not in common_docs]
    return render(request, 'common/doc.html', {'core_docs': all_docs})

def task_add(request):
    return render(request, 'common/task_add.html')

@csrf_exempt
def doc_delete(request, doc_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            doc = Docs.objects.get(pk=doc_id)
            # 관리부서 체크: 본인 부서만 삭제 가능
            if doc.department != request.user.department:
                return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
            doc.delete()
            return JsonResponse({'success': True})
        except Docs.DoesNotExist:
            return JsonResponse({'success': False, 'error': '문서를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})