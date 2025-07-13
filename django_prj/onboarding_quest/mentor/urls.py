from django.urls import path
from . import views

app_name = 'mentor'

urlpatterns = [
    path('', views.mentor, name='mentor'),
    path('add_template/', views.add_template, name='mentor_add_template'),
    path('manage_mentee/', views.manage_mentee, name='manage_mentee'),
    path('manage_template/', views.manage_template, name='manage_template'),
    path('clone_template/<int:curriculum_id>/', views.clone_template, name='clone_template'),
    path('delete_template/<int:curriculum_id>/', views.delete_template, name='delete_template'),
    path('edit_template/<int:curriculum_id>/', views.edit_template, name='edit_template'),
]
