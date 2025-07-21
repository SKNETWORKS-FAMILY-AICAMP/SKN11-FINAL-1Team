from django.urls import path
from . import views
from . import views_alarm

app_name = 'common'

urlpatterns = [
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/new-session/', views.new_chat_session, name='new_chat_session'),
    path('chatbot/session/<int:session_id>/delete/', views.delete_chat_session, name='delete_chat_session'),
    path('doc/', views.doc, name='doc'),
    path('doc/upload/', views.doc_upload, name='doc_upload'),
    path('doc/<int:doc_id>/delete/', views.doc_delete, name='doc_delete'),
    path('doc/<int:doc_id>/download/', views.doc_download, name='doc_download'),
    
    # 알람 API
    path('api/alarms/', views_alarm.get_alarms, name='api_alarms'),
    path('api/alarms/count/', views_alarm.get_alarm_count, name='api_alarm_count'),
    path('api/alarms/<int:alarm_id>/read/', views_alarm.mark_alarm_read, name='api_alarm_read'),
    path('api/alarms/<int:alarm_id>/toggle/', views_alarm.toggle_alarm_status, name='api_alarm_toggle'),
    path('api/alarms/<int:alarm_id>/delete/', views_alarm.delete_alarm, name='api_alarm_delete'),
    path('api/alarms/mark-all-read/', views_alarm.mark_all_alarms_read, name='api_alarms_read_all'),
    path('api/alarms/create/', views_alarm.create_alarm, name='api_alarm_create'),
]
