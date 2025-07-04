from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, 'login/login.html')

# Create your views here.
