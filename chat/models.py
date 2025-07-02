from django.db import models
from django.contrib.auth.models import User
import uuid


class ChatSession(models.Model):
    """채팅 세션 모델"""
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='chat_sessions'
    )
    session_name = models.CharField(
        max_length=255, 
        default='새 채팅'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '채팅 세션'
        verbose_name_plural = '채팅 세션들'

    def __str__(self):
        return f"{self.session_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class ChatMessage(models.Model):
    """채팅 메시지 모델"""
    MESSAGE_TYPES = [
        ('user', '사용자'),
        ('assistant', '어시스턴트'),
        ('system', '시스템'),
    ]

    QUERY_TYPES = [
        ('document', '문서 관련'),
        ('general', '일반 대화'),
        ('greeting', '인사'),
        ('error', '오류'),
    ]

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='user'
    )
    content = models.TextField()
    query_type = models.CharField(
        max_length=20,
        choices=QUERY_TYPES,
        null=True,
        blank=True
    )
    retrieved_docs_count = models.IntegerField(
        default=0,
        help_text='검색된 문서 수'
    )
    response_time = models.FloatField(
        null=True,
        blank=True,
        help_text='응답 시간 (초)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = '채팅 메시지'
        verbose_name_plural = '채팅 메시지들'

    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."


class Document(models.Model):
    """문서 모델"""
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    file_path = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )
    metadata = models.JSONField(
        default=dict,
        help_text='문서 메타데이터'
    )
    is_indexed = models.BooleanField(
        default=False,
        help_text='벡터 DB에 인덱싱 여부'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '문서'
        verbose_name_plural = '문서들'

    def __str__(self):
        return self.title 