from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, 'tasklist/task_add.html')

# Create your views here.
