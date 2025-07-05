from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('chatbot/', views.chatbot, name='common_chatbot'),
    path('doc/', views.doc, name='common_doc'),
    path('task_add/', views.task_add, name='common_task_add'),
]
