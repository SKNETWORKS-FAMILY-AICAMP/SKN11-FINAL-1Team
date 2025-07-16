from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # 기존 URL들
    path('chatbot/', views.chatbot, name='chatbot'),
    path('doc/', views.doc, name='doc'),
<<<<<<< Updated upstream
    path('task_add/', views.task_add, name='common_task_add'),
=======
    path('doc/upload/', views.doc_upload, name='doc_upload'),
    path('task_add/', views.task_add, name='task_add'),
    path('doc/<int:doc_id>/delete/', views.doc_delete, name='doc_delete'),
    
    # FastAPI 연동 URL들
    path('api/dashboard/', views.api_dashboard, name='api_dashboard'),
    path('api/test/auth/', views.api_test_auth, name='api_test_auth'),
    path('api/test/users/', views.api_test_users, name='api_test_users'),
    path('api/test/stats/', views.api_test_stats, name='api_test_stats'),
    path('api/proxy/<path:endpoint>/', views.api_proxy, name='api_proxy'),
    path('integrated/', views.integrated_dashboard, name='integrated_dashboard'),
>>>>>>> Stashed changes
]
