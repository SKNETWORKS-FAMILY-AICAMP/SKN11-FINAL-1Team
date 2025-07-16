from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def mentee(request):
    return render(request, 'mentee/mentee.html')

@login_required
def task_list(request):
    return render(request, 'mentee/task_list.html')
