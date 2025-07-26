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
ALLOWED_HOSTS = parse_list(os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1'))

# CORS 설정
ALLOWED_ORIGINS = parse_list(os.getenv('ALLOWED_ORIGINS', 'http://localhost:8000,http://localhost:8001'))

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
                'core.context_processors.api_urls_context',
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
        'NAME': os.getenv('DB_NAME', 'onboarding_quest_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}

# =================================
# 🔐 비밀번호 검증 및 해싱
# =================================
# 비밀번호 해셔 설정 - bcrypt와 Django 기본 해셔 모두 지원
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

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

# 파일 업로드 관련 설정
UPLOAD_BASE_DIR = os.getenv('UPLOAD_BASE_DIR', 'uploaded_docs')
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE', '50'))
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024  # MB to bytes
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE_MB * 2 * 1024 * 1024  # 2x for safety

# =================================
# 🔐 인증 설정
# =================================
AUTH_USER_MODEL = 'core.User'

# JWT 설정
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

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
# Django 서버 설정
DJANGO_HOST = os.getenv('DJANGO_HOST', 'localhost')
DJANGO_PORT = int(os.getenv('DJANGO_PORT', '8000'))
DJANGO_BASE_URL = os.getenv('DJANGO_BASE_URL', f'http://{DJANGO_HOST}:{DJANGO_PORT}')

# FastAPI 서버 설정
FASTAPI_HOST = os.getenv('FASTAPI_HOST', 'localhost')
FASTAPI_PORT = int(os.getenv('FASTAPI_PORT', '8001'))
FASTAPI_BASE_URL = os.getenv('FASTAPI_BASE_URL', f'http://{FASTAPI_HOST}:{FASTAPI_PORT}')

# RAG 시스템 설정
RAG_API_URL = os.getenv('RAG_API_URL', FASTAPI_BASE_URL)
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'rag_multiformat')

# OpenAI API 설정
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# =================================
# 🤖 Agent 스케줄 설정
# =================================
# Agent 실행 주기 (초 단위)
AGENT_CYCLE_INTERVAL = int(os.getenv('AGENT_CYCLE_INTERVAL', '30'))
# 정시 체크 간격 (시간 단위)
AGENT_HOURLY_CHECK = int(os.getenv('AGENT_HOURLY_CHECK', '1'))
# 일일 체크 실행 시간 (24시간 형식)
AGENT_DAILY_CHECK_HOUR = int(os.getenv('AGENT_DAILY_CHECK_HOUR', '9'))
# Agent 활성화 여부
AGENT_ENABLED = str2bool(os.getenv('AGENT_ENABLED', 'True'))

# =================================
# 🚀 기타 설정
# =================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'