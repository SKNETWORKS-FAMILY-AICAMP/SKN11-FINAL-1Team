from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from core.models import Docs, ChatSession, ChatMessage
import json
import os
import uuid
import mimetypes
from urllib.parse import quote
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import aiohttp
import asyncio
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# RAG API 호출 함수
async def call_rag_api(question, session_id=None, user_id=None):
    """RAG API 호출"""
    try:
        logger.info(f"RAG API 호출: {question[:50]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.RAG_API_URL}/chat",
                json={
                    "question": question,
                    "session_id": session_id,
                    "user_id": user_id or "anonymous"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("RAG API 응답 성공")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"RAG API 오류: {error_text}")
                    return {
                        "answer": "죄송합니다. 일시적인 오류가 발생했습니다.",
                        "success": False,
                        "error": error_text
                    }
    except asyncio.TimeoutError:
        logger.error("RAG API 타임아웃")
        return {
            "answer": "응답 시간이 초과되었습니다. 다시 시도해주세요.",
            "success": False,
            "error": "timeout"
        }
    except Exception as e:
        logger.error(f"RAG API 연결 오류: {str(e)}")
        return {
            "answer": f"연결 오류가 발생했습니다: {str(e)}",
            "success": False,
            "error": str(e)
        }

def chatbot(request):
    current_session_id = None
    if request.method == 'POST':
        if request.user.is_authenticated:
            message_text = request.POST.get('message', '').strip()
            selected_session_id = request.POST.get('session_id')

            if message_text:
                logger.info(f"사용자 메시지: {message_text[:50]}...")
                
                # 세션 처리 로직
                if selected_session_id:
                    try:
                        session = ChatSession.objects.get(session_id=selected_session_id, user=request.user)
                        current_session_id = session.session_id
                    except ChatSession.DoesNotExist:
                        session = ChatSession.objects.create(
                            user=request.user,
                            summary=message_text[:50] + '...' if len(message_text) > 50 else message_text
                        )
                        current_session_id = session.session_id
                else:
                    session = ChatSession.objects.create(
                        user=request.user,
                        summary=message_text[:50] + '...' if len(message_text) > 50 else message_text
                    )
                    current_session_id = session.session_id

                # 사용자 메시지 저장
                ChatMessage.objects.create(
                    session=session,
                    message_type='user',
                    message_text=message_text
                )

                # RAG API 호출
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    rag_result = loop.run_until_complete(
                        call_rag_api(
                            question=message_text,
                            session_id=current_session_id,
                            user_id=str(request.user.user_id)
                        )
                    )
                    
                    bot_response = rag_result.get("answer", "응답을 생성할 수 없습니다.")
                    
                    # 세션 요약 업데이트 (RAG에서 제공한 경우)
                    if rag_result.get("summary"):
                        session.summary = rag_result["summary"]
                        session.save()
                        
                    logger.info(f"RAG 응답: {bot_response[:50]}...")
                        
                except Exception as e:
                    logger.error(f"RAG 시스템 오류: {str(e)}")
                    bot_response = f"RAG 시스템 오류: {str(e)}"

                # 봇 응답 저장
                ChatMessage.objects.create(
                    session=session,
                    message_type='chatbot',
                    message_text=bot_response
                )

                return redirect(f'/common/chatbot/?session={current_session_id}')
    
    # 기존 렌더링 로직
    current_session_id = request.GET.get('session')
    chat_sessions = []
    if request.user.is_authenticated:
        sessions = ChatSession.objects.filter(user=request.user).order_by('-session_id')
        for session in sessions:
            messages = ChatMessage.objects.filter(session=session).order_by('create_time')
            chat_sessions.append({
                'session': session,
                'messages': messages
            })

    return render(request, 'common/chatbot.html', {
        'chat_sessions': chat_sessions,
        'current_session_id': current_session_id,
    })

# 기존 문서 업로드 관련 함수들은 그대로 유지
@csrf_exempt
def doc_upload(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            uploaded_file = request.FILES.get('file')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            tags = request.POST.get('tags', '')
            common_doc = request.POST.get('common_doc', 'false').lower() == 'true'
            department = request.user.department

            if not uploaded_file or not title or not department:
                return JsonResponse({'success': False, 'error': '필수 정보 누락'})

            # 원본 파일명에서 확장자 추출
            original_name = uploaded_file.name
            file_extension = os.path.splitext(original_name)[1]

            # 고유한 파일명 생성
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # 부서별 디렉토리 생성
            upload_dir = f"documents/{department.department_name}/"
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, upload_dir)):
                os.makedirs(os.path.join(settings.MEDIA_ROOT, upload_dir))

            # 파일 저장
            file_path = os.path.join(upload_dir, unique_filename)
            saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))

            # 데이터베이스에 저장
            clean_title = title
            if not clean_title.endswith(file_extension):
                clean_title += file_extension

            doc = Docs.objects.create(
                title=clean_title,
                description=description,
                department=department,
                file_path=saved_path,
                common_doc=common_doc
            )

            return JsonResponse({'success': True, 'doc_id': doc.docs_id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})

def doc_download(request, doc_id):
    """파일 다운로드 API"""
    if not request.user.is_authenticated:
        return HttpResponse('로그인이 필요합니다.', status=403)

    try:
        doc = get_object_or_404(Docs, docs_id=doc_id)

        # 권한 확인
        if not doc.common_doc and (not request.user.department or doc.department != request.user.department):
            return HttpResponse('다운로드 권한이 없습니다.', status=403)

        # 파일 경로 확인
        if not doc.file_path:
            return HttpResponse('파일을 찾을 수 없습니다.', status=404)

        file_path = os.path.join(settings.MEDIA_ROOT, doc.file_path)
        if not os.path.exists(file_path):
            return HttpResponse('파일이 존재하지 않습니다.', status=404)

        # 파일 읽기
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # 다운로드 파일명 생성
        download_filename = doc.title
        if not os.path.splitext(download_filename)[1]:
            stored_file_ext = os.path.splitext(doc.file_path)[1]
            if stored_file_ext:
                download_filename += stored_file_ext

        # 파일명 UTF-8 인코딩
        encoded_filename = quote(download_filename.encode('utf-8'))

        # HTTP 응답 생성
        response = HttpResponse(file_data, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        response['Content-Length'] = str(len(file_data))
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

    except Exception as e:
        return HttpResponse(f'파일 다운로드 중 오류가 발생했습니다: {str(e)}', status=500)

def doc(request):
    user = request.user
    common_docs = Docs.objects.filter(common_doc=True)
    dept_docs = Docs.objects.filter(department=user.department, common_doc=False) if user.is_authenticated and user.department else Docs.objects.none()
    all_docs = list(common_docs) + [doc for doc in dept_docs if doc not in common_docs]
    return render(request, 'common/doc.html', {'core_docs': all_docs})

def task_add(request):
    return render(request, 'common/task_add.html')

@csrf_exempt
def doc_delete(request, doc_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            doc = Docs.objects.get(pk=doc_id)
            if doc.department != request.user.department:
                return JsonResponse({'success': False, 'error': '권한이 없습니다.'})

            # 실제 파일 삭제
            if doc.file_path:
                file_path = os.path.join(settings.MEDIA_ROOT, doc.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)

            # 데이터베이스에서 문서 삭제
            doc.delete()
            return JsonResponse({'success': True})

        except Docs.DoesNotExist:
            return JsonResponse({'success': False, 'error': '문서를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})

@csrf_exempt
def new_chat_session(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            session = ChatSession.objects.create(
                user=request.user,
                summary="새 채팅"
            )
            return JsonResponse({
                'success': True,
                'session_id': session.session_id,
                'message': '새 채팅 세션이 생성되었습니다.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})

@csrf_exempt
def delete_chat_session(request, session_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            session = ChatSession.objects.get(session_id=session_id, user=request.user)
            session.delete()
            return JsonResponse({'success': True, 'message': '채팅 세션이 삭제되었습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})
