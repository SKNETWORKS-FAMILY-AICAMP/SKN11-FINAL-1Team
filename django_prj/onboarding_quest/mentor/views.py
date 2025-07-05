from django.shortcuts import render

def mentor(request):
    return render(request, 'common/mentor.html')

def add_template(request):
    return render(request, 'mentor/add_template.html')

def manage_mentee(request):
    return render(request, 'mentor/manage_mentee.html')

def manage_template(request):
    return render(request, 'mentor/manage_template.html')
