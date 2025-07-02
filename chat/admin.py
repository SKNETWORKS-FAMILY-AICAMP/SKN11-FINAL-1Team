from django.contrib import admin
from .models import ChatSession, ChatMessage, Document


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_name', 'user', 'message_count', 
        'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['session_name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = '메시지 수'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session', 'message_type', 'content_preview', 
        'query_type', 'retrieved_docs_count', 'response_time', 'created_at'
    ]
    list_filter = [
        'message_type', 'query_type', 
        'created_at', 'session__is_active'
    ]
    search_fields = ['content', 'session__session_name']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용 미리보기'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'content_preview', 'is_indexed', 
        'created_at', 'updated_at'
    ]
    list_filter = ['is_indexed', 'created_at', 'updated_at']
    search_fields = ['title', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = '내용 미리보기' 