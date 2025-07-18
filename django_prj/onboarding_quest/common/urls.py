from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/new-session/', views.new_chat_session, name='new_chat_session'),
    path('chatbot/session/<int:session_id>/delete/', views.delete_chat_session, name='delete_chat_session'),
    path('doc/', views.doc, name='doc'),
    path('doc/upload/', views.doc_upload, name='doc_upload'),
    path('doc/<int:doc_id>/delete/', views.doc_delete, name='doc_delete'),
    path('doc/<int:doc_id>/download/', views.doc_download, name='doc_download'),
    path('task_add/', views.task_add, name='common_task_add'),
    path('doc/<int:doc_id>/update/', views.doc_update, name='doc_update'),
    path('chatbot/api/send/', views.chatbot_send_api, name='chatbot_send_api'),
]
