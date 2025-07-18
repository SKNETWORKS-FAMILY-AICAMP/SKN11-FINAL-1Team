# Onboarding Quest - Django + FastAPI 통합 프로젝트

멘토링 시스템을 위한 Django 웹 애플리케이션과 FastAPI 백엔드 서버가 통합된 온보딩 퀘스트 플랫폼입니다.

## 🏗️ 프로젝트 구조

```
final_prj/
├── .env                          # 환경 변수 설정
├── django_prj/                   # Django 웹 애플리케이션
│   └── onboarding_quest/
│       ├── manage.py
│       ├── requirements.txt
│       ├── account/              # 사용자 인증 관리
│       ├── common/               # 공통 기능 (챗봇, 문서)
│       ├── core/                 # 핵심 설정 및 유틸리티
│       ├── mentee/               # 멘티 관련 기능
│       ├── mentor/               # 멘토 관련 기능
│       └── templates/            # Django 템플릿
├── fast_api/                     # FastAPI 백엔드 서버
│   ├── main.py                   # FastAPI 메인 앱
│   ├── config.py                 # 설정 관리
│   ├── database.py               # 데이터베이스 연결
│   ├── models.py                 # SQLAlchemy 모델
│   ├── schemas.py                # Pydantic 스키마
│   ├── crud.py                   # CRUD 작업
│   ├── requirements.txt
│   └── routers/                  # API 라우터
└── agent_test/                   # AI 에이전트 테스트
```

## 🚀 설치 및 실행

### 1. 환경 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# OpenAI API 키
OPENAI_API_KEY=your-openai-api-key

# FastAPI 서버 설정
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8001
FASTAPI_BASE_URL=http://localhost:8001

# PostgreSQL 데이터베이스 설정
DB_NAME=onboarding_quest_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Django 보안 설정
SECRET_KEY=your-django-secret-key
DEBUG=True
```

## 1. PostgreSQL 설치

### 방법 1: 공식 PostgreSQL 설치 (권장)

#### 1.1 PostgreSQL 다운로드
1. https://www.postgresql.org/download/windows/ 접속
2. "Download the installer" 클릭
3. Windows x86-64 17 버전 다운로드

#### 1.2 설치 진행
1. 다운로드한 파일을 관리자 권한으로 실행
2. 설치 중 설정:
   - **설치 경로**: 기본값 사용 (C:\Program Files\PostgreSQL\17\)
   - **구성 요소**: 모두 선택 (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)
   - **데이터 디렉토리**: 기본값 사용
   - **비밀번호**: postgres 사용자 비밀번호 설정 (.env 파일에 추가)
   - **포트**: 5432 (기본값)
   - **로케일**: 기본값 사용

#### 1.3 환경 변수 설정 (자동으로 안 된 경우)
1. 시스템 속성 > 고급 > 환경 변수
2. 시스템 변수의 Path에 추가:
   - C:\Program Files\PostgreSQL\17\bin
   - C:\Program Files\PostgreSQL\17\lib
   - 

#### 데이터베이스 생성
```bash
# PostgreSQL 접속
sudo -u postgres psql

# 데이터베이스 생성
CREATE DATABASE onboarding_quest_db;
CREATE USER postgres WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE onboarding_quest_db TO postgres;
\q
```

### 3. Python 환경 설정

#### 가상환경 생성 및 활성화
```bash
# 가상환경 생성
conda create -n {env_name} python=3.11
conda activate {env_name}
```

### 4. Django 설정 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# Django 프로젝트 디렉토리로 이동
cd django_prj/onboarding_quest

# 데이터베이스 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 샘플 데이터 생성
python manage.py make_sample

# Django 개발 서버 실행 (포트 8000)
python manage.py runserver 8000
```

### 5. FastAPI 설정 및 실행

새 터미널을 열어서:

```bash
# FastAPI 프로젝트 디렉토리로 이동
cd fast_api

# FastAPI 서버 실행 (포트 8001)
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 🌐 서비스 접속

- **Django 웹 애플리케이션**: http://localhost:8000
- **FastAPI 백엔드**: http://localhost:8001
- **FastAPI API 문서**: http://localhost:8001/docs
- **Django 관리자**: http://localhost:8000/admin

## 📊 FastAPI 주요 엔드포인트

### 인증 및 사용자 관리
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `GET /api/users/` - 사용자 목록 조회 (필터링 지원)
- `POST /api/users/` - 사용자 생성
- `GET /api/users/{user_id}` - 사용자 상세 조회
- `PUT /api/users/{user_id}` - 사용자 정보 수정
- `DELETE /api/users/{user_id}` - 사용자 삭제

### 회사 및 부서 관리
- `GET /api/companies/` - 회사 목록 조회
- `POST /api/companies/` - 회사 생성
- `GET /api/departments/` - 부서 목록 조회
- `POST /api/departments/` - 부서 생성

### 멘토링 시스템
- `GET /api/mentorship/` - 멘토링 관계 조회
- `POST /api/mentorship/` - 멘토링 관계 생성
- `GET /api/tasks/manage/` - 태스크 관리
- `POST /api/tasks/assign/` - 태스크 할당

### 챗봇 및 문서 관리
- `GET /api/chat/sessions/` - 채팅 세션 목록
- `POST /api/chat/sessions/` - 새 채팅 세션 생성
- `GET /api/docs/` - 문서 목록 조회
- `POST /api/docs/upload/` - 문서 업로드

### 기타
- `GET /health` - 서버 상태 확인
- `GET /api/` - API 정보

## 🔧 주요 기능

### Django 웹 애플리케이션
- **사용자 인증**: 로그인/로그아웃, 권한 관리
- **멘토링 시스템**: 멘토-멘티 매칭 및 관리
- **태스크 관리**: 할당, 진행상황 추적
- **챗봇 인터페이스**: AI 기반 상담 시스템
- **문서 관리**: 업로드, 다운로드, 버전 관리

### FastAPI 백엔드
- **RESTful API**: 완전한 CRUD 작업 지원
- **PostgreSQL 연동**: 관계형 데이터베이스 활용
- **자동 API 문서화**: Swagger/OpenAPI 지원
- **CORS 설정**: 프론트엔드 연동 지원
- **데이터 검증**: Pydantic 스키마 활용

## 🧪 개발 및 테스트

### requirements.txt 생성
```bash
# 현재 환경의 패키지 목록 저장
pip freeze > requirements.txt
```

### 데이터베이스 초기화
```bash
# Django
python manage.py flush

# PostgreSQL 직접 접근
sudo -u postgres psql
DROP DATABASE onboarding_quest_db;
CREATE DATABASE onboarding_quest_db;
```

### API 테스트 예시

#### 회사 생성
```bash
curl -X POST "http://localhost:8001/api/companies/" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "테스트 회사"}'
```

#### 사용자 생성
```bash
curl -X POST "http://localhost:8001/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "테스트 사용자",
    "role": "mentee",
    "company_id": "COMP001",
    "department_id": 1
  }'
```

## 🛠️ 기술 스택

### Backend
- **Django 4.x**: 웹 프레임워크
- **FastAPI**: REST API 서버
- **PostgreSQL**: 메인 데이터베이스
- **SQLAlchemy**: ORM (FastAPI)
- **Django ORM**: ORM (Django)

### Frontend
- **Django Templates**: 서버 사이드 렌더링
- **Bootstrap**: UI 프레임워크
- **JavaScript**: 클라이언트 사이드 로직

### AI/ML
- **OpenAI API**: 챗봇 기능
- **LangGraph**: AI 에이전트 워크플로우

## 🔒 보안 고려사항

- 환경 변수를 통한 민감 정보 관리
- Django CSRF 보호
- SQL Injection 방지 (ORM 사용)
- 사용자 인증 및 권한 검증