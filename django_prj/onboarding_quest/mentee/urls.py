from django.urls import path
from . import views

urlpatterns = [
    path('mentee/', views.mentee, name='common_mentee'),
]
