from django.urls import path
from . import views

urlpatterns = [
    path('', views.mentor, name='mentor'),
    path('add_template/', views.add_template, name='mentor_add_template'),
    path('manage_mentee/', views.manage_mentee, name='mentor_manage_mentee'),
    path('manage_template/', views.manage_template, name='mentor_manage_template'),
]
