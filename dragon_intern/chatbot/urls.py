from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.ChatbotView.as_view(), name='chat'),
    path('apply-settings/', views.apply_settings, name='apply_settings'),
    path('chat-message/', views.chat_message, name='chat_message'),
    path('clear-chat/', views.clear_chat, name='clear_chat'),
    path('get-user-settings/', views.get_user_settings, name='get_user_settings'),
    path('save-config/', views.save_mcp_config, name='save_config'),
    path('initialize-mcp/', views.initialize_mcp, name='initialize_mcp'),
]