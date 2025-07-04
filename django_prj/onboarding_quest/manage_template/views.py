from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, 'manage_template/manage_template.html')

# Create your views here.
