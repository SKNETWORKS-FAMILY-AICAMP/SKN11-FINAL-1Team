import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 프로젝트 루트의 .env 파일 로드 (django_prj 상위 폴더)
PROJECT_ROOT = BASE_DIR.parent.parent
load_dotenv(PROJECT_ROOT / '.env')

def str2bool(v):
    """문자열을 boolean으로 변환"""
    return str(v).lower() in ("1", "true", "yes", "on")

def parse_list(v, delimiter=','):
    """문자열을 리스트로 변환"""
    if not v:
        return []
    return [item.strip() for item in v.split(delimiter) if item.strip()]

# =================================
# 🔒 보안 설정
# =================================
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
DEBUG = str2bool(os.getenv('DEBUG', 'False'))
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost', 
    '15.165.82.201',  # 현재 EC2 공인 IP
    '*',  # 모든 호스트 허용 (개발용, 운영에서는 권장하지 않음)
]
# =================================
# 📋 로깅 설정
# =================================
# .well-known 경로 404 로그 무시용 필터
class IgnoreWellKnown(logging.Filter):
    def filter(self, record):
        return '/.well-known/' not in record.getMessage()

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'ignore_well_known': {
            '()': IgnoreWellKnown,
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'filters': ['ignore_well_known'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.server': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'account.views': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'core.utils.fastapi_client': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
}

# =================================
# 📱 Django 애플리케이션 설정
# =================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'account',
    'common',
    'mentor',
    'mentee',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.fastapi_token.FastAPITokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'onboarding_quest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.mentorship_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'onboarding_quest.wsgi.application'

# =================================
# 🗄️ 데이터베이스 설정
# =================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'database-1',
        'USER': 'postgres',
        'PASSWORD': 'sungilbang',
        'HOST': 'database-1.czcym4u8awpn.ap-northeast-2.rds.amazonaws.com',
        'PORT': '5432'
        
    }
}

# =================================
# 🔐 비밀번호 검증
# =================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =================================
# 🌍 국제화 설정
# =================================
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# =================================
# 📁 정적 파일 및 미디어 설정
# =================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# 미디어 파일 설정 (.env에서 가져오기)
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, os.getenv('MEDIA_ROOT', 'media'))

# 파일 업로드 크기 제한
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE', '50'))
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024  # MB to bytes
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE_MB * 2 * 1024 * 1024  # 2x for safety

# =================================
# 🔐 인증 설정
# =================================
AUTH_USER_MODEL = 'core.User'

# CSRF 설정
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_HTTPONLY = False

# 로그인 관련 URL
LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/account/login/'

# =================================
# 🌐 외부 서비스 연동
# =================================
# FastAPI 서버 설정
FASTAPI_HOST = os.getenv('FASTAPI_HOST', 'localhost')
FASTAPI_PORT = int(os.getenv('FASTAPI_PORT', '8001'))
FASTAPI_BASE_URL = os.getenv('FASTAPI_BASE_URL', f'http://{FASTAPI_HOST}:{FASTAPI_PORT}')

# RAG 시스템 설정
RAG_API_URL = os.getenv('RAG_API_URL', FASTAPI_BASE_URL)
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'rag_multiformat')

# =================================
# 🚀 기타 설정
# =================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 디버그 모드에서 설정 정보 출력
if DEBUG:
    print(f"🐍 Django Settings Loaded:")
    print(f"   - Debug Mode: {DEBUG}")
    print(f"   - Database: {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}")
    print(f"   - FastAPI URL: {FASTAPI_BASE_URL}")
    print(f"   - Media Root: {MEDIA_ROOT}")
    print(f"   - RAG API: {RAG_API_URL}")
    print(f"   - Log Level: {LOG_LEVEL}")

