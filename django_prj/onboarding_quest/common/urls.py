from django.urls import path
from . import views

urlpatterns = [
    path('chatbot/', views.chatbot, name='common_chatbot'),
    path('doc/', views.doc, name='common_doc'),
    path('task/add/', views.task_add, name='common_task_add'),
]
