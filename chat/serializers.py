from rest_framework import serializers
from .models import ChatSession, ChatMessage, Document


class ChatMessageSerializer(serializers.ModelSerializer):
    """채팅 메시지 시리얼라이저"""
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'session', 'message_type', 'content', 
            'query_type', 'retrieved_docs_count', 
            'response_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """채팅 세션 시리얼라이저"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_name', 'created_at', 
            'updated_at', 'is_active', 'messages', 'message_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class DocumentSerializer(serializers.ModelSerializer):
    """문서 시리얼라이저"""
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'content', 'file_path', 
            'metadata', 'is_indexed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatRequestSerializer(serializers.Serializer):
    """채팅 요청 시리얼라이저"""
    message = serializers.CharField(max_length=1000)
    session_id = serializers.UUIDField(required=False)
    
    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("메시지는 비어있을 수 없습니다.")
        return value.strip()


class ChatResponseSerializer(serializers.Serializer):
    """채팅 응답 시리얼라이저"""
    response = serializers.CharField()
    query_type = serializers.CharField()
    retrieved_docs_count = serializers.IntegerField()
    response_time = serializers.FloatField()
    session_id = serializers.UUIDField()
    message_id = serializers.UUIDField() 