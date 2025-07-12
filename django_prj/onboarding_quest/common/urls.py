from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('chatbot/', views.chatbot, name='chatbot'),
    path('doc/', views.doc, name='doc'),
    path('task_add/', views.task_add, name='common_task_add'),
    path('doc/upload/', views.doc_upload, name='doc_upload'),
    path('doc/<int:doc_id>/delete/', views.doc_delete, name='doc_delete'),
]
