"""
URL configuration for onboarding_quest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from account import views as account_views
from core import views as core_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', account_views.login_view, name='root_login'),

    # 디버그 엔드포인트
    path('debug/mentorship/', core_views.debug_mentorship_from_db, name='debug_mentorship'),

    path('mentor/', include('mentor.urls')),
    path('mentee/', include('mentee.urls')),
    path('account/', include('account.urls')),
    path('common/', include('common.urls')),
    
    # 알람 API 직접 연결 (별도 네임스페이스)
    path('django-api/', include(('common.urls', 'common_api'), namespace='django_api')),

    # API 프록시 (FastAPI로 전달) - 가장 마지막에 배치
    re_path(r'^api/(?P<path>.*)$', core_views.fastapi_proxy, name='fastapi_proxy'),

]

# 미디어 파일 서빙 설정 추가
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)