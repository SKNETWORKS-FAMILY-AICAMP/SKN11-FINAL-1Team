from django.urls import path
from . import views

app_name = 'mentee'

urlpatterns = [
    path('', views.mentee, name='mentee'),
    path('task_list/', views.task_list, name='task_list'),
    path('task_detail/<int:task_assign_id>/', views.task_detail, name='task_detail'),
    path('task_update/<int:task_assign_id>/', views.task_update, name='task_update'),
]
