from django.shortcuts import render

def mentee(request):
    return render(request, 'mentee/mentee.html')