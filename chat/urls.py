from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # 웹 페이지
    path('', views.ChatbotView.as_view(), name='chatbot'),
    
    # API 엔드포인트
    path('chat/', views.chat_api, name='chat_api'),
    path('sessions/', views.chat_sessions_api, name='sessions_api'),
    path('sessions/create/', views.create_session_api, name='create_session_api'),
    path('sessions/<uuid:session_id>/', views.chat_session_detail_api, name='session_detail_api'),
    path('sessions/<uuid:session_id>/delete/', views.delete_session_api, name='delete_session_api'),
    path('documents/upload/', views.upload_document_api, name='upload_document_api'),
    path('health/', views.health_check_api, name='health_check_api'),
] 