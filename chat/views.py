import time
import asyncio
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import json
import logging

from .models import ChatSession, ChatMessage, Document
from .serializers import (
    ChatSessionSerializer, ChatMessageSerializer, 
    ChatRequestSerializer, ChatResponseSerializer,
    DocumentSerializer
)

# chatbot.py에서 챗봇 함수 import
from chatbot import chat_sync

logger = logging.getLogger(__name__)


class ChatbotView(TemplateView):
    """챗봇 메인 페이지 뷰"""
    template_name = 'chat/chatbot.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'AI 챗봇'
        return context


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_api(request):
    """챗봇 API 엔드포인트"""
    try:
        # 요청 데이터 검증
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': '잘못된 요청 데이터입니다.', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        
        # 채팅 세션 처리
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create()
        else:
            session = ChatSession.objects.create()
        
        # 사용자 메시지 저장
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message
        )
        
        # 채팅 히스토리 준비
        chat_history = []
        recent_messages = session.messages.filter(
            message_type__in=['user', 'assistant']
        ).order_by('created_at')[-10:]  # 최근 10개 메시지만
        
        for msg in recent_messages[:-1]:  # 현재 메시지 제외
            if msg.message_type == 'user':
                chat_history.append({'user': msg.content, 'assistant': ''})
            else:
                if chat_history:
                    chat_history[-1]['assistant'] = msg.content
        
        # 챗봇 응답 생성
        start_time = time.time()
        
        try:
            # 동기적으로 챗봇 호출
            bot_response = chat_sync(message, chat_history)
            response_time = time.time() - start_time
            
            # 어시스턴트 메시지 저장
            assistant_message = ChatMessage.objects.create(
                session=session,
                message_type='assistant',
                content=bot_response['response'],
                query_type=bot_response.get('query_type', 'general'),
                retrieved_docs_count=bot_response.get('retrieved_docs_count', 0),
                response_time=response_time
            )
            
            # 세션 업데이트 시간 갱신
            session.save()
            
            # 응답 데이터 준비
            response_data = {
                'response': bot_response['response'],
                'query_type': bot_response.get('query_type', 'general'),
                'retrieved_docs_count': bot_response.get('retrieved_docs_count', 0),
                'response_time': response_time,
                'session_id': str(session.id),
                'message_id': str(assistant_message.id)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"챗봇 응답 생성 오류: {e}")
            
            # 오류 메시지 저장
            ChatMessage.objects.create(
                session=session,
                message_type='assistant',
                content="죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.",
                query_type='error',
                response_time=time.time() - start_time
            )
            
            return Response(
                {
                    'response': "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.",
                    'query_type': 'error',
                    'retrieved_docs_count': 0,
                    'response_time': time.time() - start_time,
                    'session_id': str(session.id),
                    'message_id': None
                },
                status=status.HTTP_200_OK
            )
    
    except Exception as e:
        logger.error(f"채팅 API 오류: {e}")
        return Response(
            {'error': '서버 오류가 발생했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def chat_sessions_api(request):
    """채팅 세션 목록 API"""
    try:
        sessions = ChatSession.objects.filter(is_active=True)[:20]  # 최근 20개
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"세션 목록 조회 오류: {e}")
        return Response(
            {'error': '세션 목록을 불러올 수 없습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def chat_session_detail_api(request, session_id):
    """특정 채팅 세션 상세 정보 API"""
    try:
        session = get_object_or_404(ChatSession, id=session_id)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"세션 상세 조회 오류: {e}")
        return Response(
            {'error': '세션 정보를 불러올 수 없습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_session_api(request):
    """새 채팅 세션 생성 API"""
    try:
        session_name = request.data.get('session_name', '새 채팅')
        session = ChatSession.objects.create(session_name=session_name)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"세션 생성 오류: {e}")
        return Response(
            {'error': '세션을 생성할 수 없습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_session_api(request, session_id):
    """채팅 세션 삭제 API"""
    try:
        session = get_object_or_404(ChatSession, id=session_id)
        session.is_active = False
        session.save()
        return Response(
            {'message': '세션이 삭제되었습니다.'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"세션 삭제 오류: {e}")
        return Response(
            {'error': '세션을 삭제할 수 없습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def upload_document_api(request):
    """문서 업로드 API"""
    try:
        title = request.data.get('title', '제목 없음')
        content = request.data.get('content', '')
        
        if not content.strip():
            return Response(
                {'error': '문서 내용은 비어있을 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 문서 저장
        document = Document.objects.create(
            title=title,
            content=content.strip()
        )
        
        # TODO: 실제 구현에서는 여기서 벡터 DB에 문서를 추가
        # from chatbot import chatbot_instance
        # if chatbot_instance:
        #     chatbot_instance.add_documents([content])
        #     document.is_indexed = True
        #     document.save()
        
        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"문서 업로드 오류: {e}")
        return Response(
            {'error': '문서를 업로드할 수 없습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_api(request):
    """헬스 체크 API"""
    try:
        # 간단한 챗봇 테스트
        test_response = chat_sync("안녕하세요")
        
        return Response({
            'status': 'healthy',
            'chatbot_status': 'working' if test_response else 'error',
            'message': '모든 시스템이 정상 작동 중입니다.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"헬스 체크 오류: {e}")
        return Response({
            'status': 'error',
            'chatbot_status': 'error',
            'message': '시스템에 문제가 있습니다.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE) 