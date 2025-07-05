from django.shortcuts import render

def mentee(request):
    return render(request, 'mentee/mentee.html')

def task_list(request):
    return render(request, 'mentee/task_list.html')