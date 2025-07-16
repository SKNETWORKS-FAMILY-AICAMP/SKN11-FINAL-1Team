"""
URL configuration for onboarding_quest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from account import views as account_views

def health_check(request):
    """Django 헬스 체크"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Django 프론트엔드 서버가 정상 작동 중입니다.',
        'version': '1.0.0'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    
    path('', account_views.login_view, name='root_login'),

    path('mentor/', include('mentor.urls')),
    path('mentee/', include('mentee.urls')),
    path('account/', include('account.urls')),
    path('common/', include('common.urls')),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)