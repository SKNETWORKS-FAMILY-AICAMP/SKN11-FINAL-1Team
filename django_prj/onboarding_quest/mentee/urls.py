from django.urls import path
from . import views

app_name = 'mentee'

urlpatterns = [
    path('', views.mentee, name='mentee'),
    path('task_list/', views.task_list, name='task_list'),
]
