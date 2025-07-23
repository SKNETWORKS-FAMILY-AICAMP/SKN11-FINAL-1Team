from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from core.models import Docs, ChatSession, ChatMessage
import json
import os
import uuid
import threading
from django.utils import timezone
import mimetypes
from urllib.parse import quote
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from core.utils.fastapi_client import fastapi_client, APIError, AuthenticationError
from django.contrib import messages
import aiohttp
import asyncio
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from embed_and_upsert import advanced_embed_and_upsert, get_existing_point_ids
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# 로깅 설정
logger = logging.getLogger(__name__)

# Qdrant 삭제 함수
def delete_from_qdrant(file_path, department_id):
    """Qdrant에서 특정 파일의 모든 청크 삭제"""
    try:
        client = QdrantClient(url=os.getenv("QDRANT_URL"))
        absolute_path = os.path.abspath(file_path)
        
        # 파일 기반 필터링으로 삭제
        delete_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.source",
                    match=MatchValue(value=absolute_path)
                ),
                FieldCondition(
                    key="metadata.department_id",
                    match=MatchValue(value=department_id)
                )
            ]
        )
        
        # 삭제 실행
        delete_result = client.delete(
            collection_name="rag_multiformat",
            points_selector=delete_filter
        )
        
        return delete_result.operation_id
        
    except Exception as e:
        logger.error(f"Qdrant 삭제 중 오류: {e}")
        return None

# 비동기 임베딩 함수
def embed_document_async(file_path, department_id, common_doc, original_file_name=None):
    """비동기로 문서 임베딩 처리"""
    try:
        existing_ids = get_existing_point_ids()
        embedded_chunks = advanced_embed_and_upsert(
            file_path, 
            existing_ids,
            department_id=department_id,
            common_doc=common_doc,
            original_file_name=original_file_name
        )
        logger.info(f"문서 임베딩 완료: {file_path}, 청크 수: {embedded_chunks}")
        return embedded_chunks
    except Exception as e:
        logger.error(f"문서 임베딩 중 오류: {e}")
        return 0

# RAG API 호출 함수
async def call_rag_api(question, session_id=None, user_id=None, department_id=None):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.RAG_API_URL}/chat",
                json={
                    "question": question,
                    "session_id": str(session_id) if session_id else None,
                    "user_id": str(user_id) if user_id else "anonymous",
                    "department_id": int(department_id) if department_id else 0
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"RAG API 오류 ({response.status}): {error_text}")
                    return {
                        "answer": "죄송합니다. 일시적인 오류가 발생했습니다.",
                        "success": False,
                        "error": error_text
                    }
    except Exception as e:
        logger.error(f"RAG API 연결 오류: {str(e)}")
        return {
            "answer": f"시스템 오류가 발생했습니다: {str(e)}",
            "success": False,
            "error": str(e)
        }

# 챗봇 메인 함수
def chatbot(request):
    current_session_id = request.GET.get('session')
    chat_sessions = []

    if request.user.is_authenticated:
        sessions = ChatSession.objects.filter(user=request.user, is_active=True).order_by('-session_id')

        # ✅ 세션 ID가 없으면 가장 최근 세션으로 자동 리디렉션
        if not current_session_id and sessions.exists():
            return redirect(f'/common/chatbot/?session={sessions.first().session_id}')

        for session in sessions:
            messages = ChatMessage.objects.filter(session=session, is_active=True).order_by('message_id')
            # ✅ 첫 번째 user 메시지 추출
            first_user_message = next((m for m in messages if m.message_type == 'user'), None)

            chat_sessions.append({
                'session': session,
                'messages': messages,
                'first_user_message': first_user_message
            })

    # FastAPI 토큰 생성
    fastapi_token = None
    if request.user.is_authenticated:
        try:
            # FastAPI 토큰 생성을 위한 유틸리티 함수 호출
            fastapi_token = fastapi_client.generate_token_for_user(request.user)
        except Exception as e:
            logger.warning(f"FastAPI 토큰 생성 실패: {e}")

    return render(request, 'common/chatbot.html', {
        'chat_sessions': chat_sessions,
        'current_session_id': current_session_id,
        'fastapi_token': fastapi_token,
    })


# 문서 업로드 API (djnago DB에 저장)
@csrf_exempt
@login_required
def doc_upload(request):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('file')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            common_doc = request.POST.get('common_doc', 'false').lower() == 'true'
            department = request.user.department

            if not uploaded_file or not title or not department:
                return JsonResponse({'success': False, 'error': '필수 정보 누락'})

            # ✅ FastAPI에 업로드 요청 전송
            import requests
            files = {
                'file': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
            }
            data = {
                'department_id': department.department_id,
                'common_doc': str(common_doc).lower(),
                'original_file_name': uploaded_file.name
            }

            rag_api_url = f"{settings.RAG_API_URL}/upload"
            response = requests.post(rag_api_url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # ✅ FastAPI 업로드 성공 시 Django DB에도 저장
                    original_name = uploaded_file.name
                    file_extension = os.path.splitext(original_name)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    upload_dir = f"documents/{department.department_name}/"
                    
                    # 디렉토리 생성
                    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, upload_dir)):
                        os.makedirs(os.path.join(settings.MEDIA_ROOT, upload_dir))
                    
                    file_path = os.path.join(upload_dir, unique_filename)
                    
                    # 파일 재저장 (FastAPI용과 Django용 별도 저장)
                    uploaded_file.seek(0)  # 파일 포인터 초기화
                    saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
                    
                    # 제목 정리
                    clean_title = title
                    if not clean_title.endswith(file_extension):
                        clean_title += file_extension
                    
                    # Django DB에 저장
                    doc = Docs.objects.create(
                        title=clean_title,
                        description=description,
                        department=department,
                        file_path=saved_path,
                        common_doc=common_doc
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'doc_id': doc.docs_id,
                        'message': f"문서 업로드 완료 (청크 수: {result.get('chunks_uploaded')})",
                        'file': result.get('original_file')
                    })
                else:
                    return JsonResponse({'success': False, 'error': result.get('error', 'FastAPI 처리 실패')})
            else:
                return JsonResponse({'success': False, 'error': f'FastAPI 응답 오류 {response.status_code}'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})

@csrf_exempt
def doc_update(request, doc_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            doc = Docs.objects.get(pk=doc_id)

            if doc.department != request.user.department:
                return JsonResponse({'success': False, 'error': '권한이 없습니다.'})

            description = request.POST.get('description', '')
            tags = request.POST.get('tags', '')
            common_doc_str = request.POST.get('common_doc', 'false')  # ← 문자열 그대로 받음
            common_doc = common_doc_str.lower() == 'true'  # ← 정확한 문자열 비교

            doc.description = description
            doc.tags = tags
            doc.common_doc = common_doc
            doc.save()

            return JsonResponse({'success': True, 'message': '문서 정보가 수정되었습니다.'})

        except Docs.DoesNotExist:
            return JsonResponse({'success': False, 'error': '문서를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})


@csrf_exempt
def doc_delete(request, doc_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            doc = Docs.objects.get(pk=doc_id)
            if doc.department != request.user.department:
                return JsonResponse({'success': False, 'error': '권한이 없습니다.'})

            # 파일 정보 저장
            file_path = os.path.join(settings.MEDIA_ROOT, doc.file_path)
            department_id = doc.department.department_id
            
            # 1. 실제 파일 삭제
            if doc.file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            # 2. Qdrant에서 관련 청크 삭제
            delete_operation = delete_from_qdrant(file_path, department_id)
            
            # 3. 데이터베이스에서 문서 삭제
            doc.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'문서 및 벡터 데이터가 삭제되었습니다. (작업 ID: {delete_operation})'
            })

        except Docs.DoesNotExist:
            return JsonResponse({'success': False, 'error': '문서를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '권한 없음 또는 잘못된 요청'})

# 문서 다운로드 함수
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
            session.is_active = False
            session.save()

            ChatMessage.objects.filter(session=session).update(is_active=False)

            return JsonResponse({'success': True, 'message': '채팅 세션이 비활성화되었습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})




@csrf_exempt
@require_POST
def chatbot_send_api(request):
    logger.warning(f"🚨 chatbot_send_api 요청 도착! 사용자: {request.user}, 세션: {request.body}")

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': '로그인이 필요합니다.'})

    try:
        data = json.loads(request.body)

        message_text = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not message_text:
            return JsonResponse({'success': False, 'error': '메시지가 비어 있습니다.'})

        # 세션 가져오기 또는 새로 생성
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                return JsonResponse({'success': False, 'error': '세션을 찾을 수 없습니다.'})
        else:
            session = ChatSession.objects.create(user=request.user)
            session_id = session.session_id

        # ✅ 사용자 메시지는 항상 저장 (중복 차단 없음)
        ChatMessage.objects.create(
            session=session,
            message_type='user',
            message_text=message_text
        )
        logger.info(f"[chatbot_send_api] 사용자 메시지 저장됨: {message_text}")

        # summary는 메시지 저장 후에만 설정
        if not session.summary:
            summary = message_text[:50] + '...' if len(message_text) > 50 else message_text
            session.summary = summary[:255]
            session.save()

        # ✅ RAG 호출 (비동기)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from .views import call_rag_api
        rag_result = loop.run_until_complete(
    call_rag_api(
        question=message_text,
        session_id=session_id,
        user_id=str(request.user.user_id),
        department_id=request.user.department.department_id if request.user.department else None
    )
)

        used_rag = bool(rag_result.get("contexts"))
        logger.info(f"[chatbot_send_api] RAG 여부: {'🧾 사용함' if used_rag else '💬 사용 안 함'} - 질문: {message_text}")

        answer = rag_result.get("answer", "응답을 생성할 수 없습니다.")
        logger.info(f"[chatbot_send_api] 챗봇 응답 생성됨: {answer}")

        # ✅ 챗봇 메시지 저장 (중복 검사 유지 가능)
        already_exists = ChatMessage.objects.filter(
            session=session,
            message_type__in=['chatbot', 'bot'],
            message_text=answer
        ).exists()

        if not already_exists:
            ChatMessage.objects.create(
                session=session,
                message_type='chatbot',
                message_text=answer
            )
            logger.info("[chatbot_send_api] 챗봇 응답 저장됨")
        else:
            logger.warning("[중복 차단] 챗봇 응답 중복 저장 차단됨")

        # RAG summary 반영
        if rag_result.get("summary"):
            session.summary = rag_result["summary"][:255]
            session.save()

        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'answer': answer
        })

    except Exception as e:
        logger.error(f"[chatbot_send_api 오류] {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

