from django.shortcuts import render

def chatbot(request):
    return render(request, 'common/chatbot.html')

def doc(request):
    return render(request, 'common/doc.html')

def task_add(request):
    return render(request, 'common/task_add.html')
