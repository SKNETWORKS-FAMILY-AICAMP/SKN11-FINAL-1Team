# Onboarding Quest - Django + FastAPI + RAG 통합 프로젝트

LangGraph 기반 RAG 시스템이 통합된 멘토링 플랫폼입니다. Django 웹 애플리케이션과 FastAPI 백엔드가 **완전 통합**되어 하나의 일관된 시스템으로 구성되어 있습니다.

## 🏗️ 통합 아키텍처

```
Django (8000) → FastAPI (8001) → RAG Agent + Qdrant + PostgreSQL
```

**완전 통합 완료**: ✅ 포트 충돌 해결, ✅ 중복 서버 제거, ✅ 통합 API 엔드포인트

## 🗂️ 프로젝트 구조

```
final_prj/
├── .env                          # 🔑 환경 변수 설정 (중요!)
├── django_prj/                   # Django 웹 애플리케이션
│   └── onboarding_quest/
│       ├── manage.py
│       ├── requirements.txt
│       ├── rag_agent_graph_db_v3_finaltemp_v2.py  # 🤖 LangGraph RAG 에이전트
│       ├── account/              # 사용자 인증 관리
│       ├── common/               # 공통 기능 (챗봇, 문서)
│       ├── core/                 # 핵심 설정 및 유틸리티
│       ├── mentee/               # 멘티 관련 기능
│       ├── mentor/               # 멘토 관련 기능
│       └── templates/            # Django 템플릿
├── fast_api/                     # 🚀 FastAPI 통합 백엔드 서버
│   ├── main.py                   # FastAPI 메인 앱
│   ├── config.py                 # 설정 관리
│   ├── requirements.txt
│   └── routers/                  # 통합 API 라우터
│       ├── chat.py               # 🤖 RAG 채팅 + 세션 관리
│       ├── documents.py          # 📄 문서 업로드/관리 (신규)
│       ├── users.py              # 👥 사용자 관리
│       ├── tasks.py              # 📋 태스크 관리
│       └── ...                   # 기타 기능별 라우터
└── agent_test/                   # AI 에이전트 테스트
```

### 🔄 주요 변경사항 (완전 통합)

**제거된 파일들:**
- ❌ `rag_fastapi_server.py` (백업: `rag_fastapi_server.py.backup`)
- ❌ `fast_api/routers/rag.py` (중복 제거)

**새로 생성된 파일들:**
- ✅ `fast_api/routers/documents.py` (문서 관리 통합)

**통합된 API 구조:**
```
/api/chat/rag              # RAG 기반 챗봇
/api/chat/session/*        # 세션 관리
/api/documents/*           # 문서 관리 (업로드/삭제/수정)
/api/users/*               # 사용자 관리
/api/tasks/*               # 태스크 관리
```

## 🚀 설치 및 실행 가이드

### 🔧 1. 시스템 요구사항

- **Python**: 3.11 이상
- **PostgreSQL**: 17 이상
- **Qdrant**: 1.7 이상 (벡터 데이터베이스)
- **OpenAI API Key**: GPT-4 또는 GPT-4o-mini 사용

### 📋 2. 환경 설정

#### 2.1 `.env` 파일 생성
프로젝트 루트(`final_prj/`)에 `.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# =================================
# 🔑 API 키 설정
# =================================
OPENAI_API_KEY=sk-your-openai-api-key-here

# =================================
# 🌐 서버 설정
# =================================
# Django 서버
DJANGO_HOST=0.0.0.0
DJANGO_PORT=8000
DJANGO_BASE_URL=http://localhost:8000

# FastAPI 서버
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8001
FASTAPI_BASE_URL=http://localhost:8001

# =================================
# 🗄️ 데이터베이스 설정
# =================================
# PostgreSQL (메인 데이터베이스)
DB_NAME=onboarding_quest_db
DB_USER=postgres
DB_PASSWORD=your-postgresql-password
DB_HOST=localhost
DB_PORT=5432

# =================================
# 🔒 보안 설정
# =================================
SECRET_KEY=your-super-secret-django-key-change-in-production
DEBUG=True

# CORS 설정
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*.localhost
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8001,http://127.0.0.1:3000,http://127.0.0.1:8000,http://127.0.0.1:8001

# =================================
# 🔐 인증 설정 (JWT)
# =================================
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# =================================
# 🤖 RAG 시스템 설정
# =================================
# Qdrant 벡터 데이터베이스
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=rag_multiformat

# RAG API 설정
RAG_API_URL=http://localhost:8001

# =================================
# 📁 파일 업로드 설정
# =================================
UPLOAD_BASE_DIR=uploaded_docs
MAX_FILE_SIZE=50
MEDIA_ROOT=media
MEDIA_URL=/media/

# =================================
# 📋 로깅 설정
# =================================
LOG_LEVEL=INFO
```

### 🐘 3. PostgreSQL 설치 및 설정

#### 3.1 PostgreSQL 설치 (Windows)

**방법 1: 공식 설치 (권장)**
1. https://www.postgresql.org/download/windows/ 접속
2. "Download the installer" 클릭
3. Windows x86-64 17 버전 다운로드
4. 설치 중 설정:
   - **설치 경로**: 기본값 사용
   - **구성 요소**: 모두 선택 (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)
   - **비밀번호**: `.env` 파일의 `DB_PASSWORD`와 동일하게 설정
   - **포트**: 5432 (기본값)

#### 3.2 데이터베이스 생성
```bash
# PostgreSQL 명령줄 접속
psql -U postgres -h localhost

# 데이터베이스 생성
CREATE DATABASE onboarding_quest_db;

# 권한 설정 (필요시)
GRANT ALL PRIVILEGES ON DATABASE onboarding_quest_db TO postgres;

# 종료
\q
```

### 🔍 4. Qdrant 설치 및 실행

#### 4.1 Docker를 사용한 Qdrant 실행 (권장)
```bash
# Qdrant 컨테이너 실행
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

#### 4.2 직접 설치 (옵션)
```bash
# Qdrant 설치
pip install qdrant-client

# 또는 conda 사용
conda install -c conda-forge qdrant-client
```

### 🐍 5. Python 환경 설정

#### 5.1 가상환경 생성 및 활성화
```bash
# Conda 환경 생성 (권장)
conda create -n onboarding_quest python=3.11
conda activate onboarding_quest

# 또는 venv 사용
python -m venv onboarding_quest
# Windows
onboarding_quest\Scripts\activate
# macOS/Linux
source onboarding_quest/bin/activate
```

### 🌐 6. Django 설정 및 실행

```bash
# Django 프로젝트 디렉토리로 이동
cd django_prj/onboarding_quest

# 의존성 설치
pip install -r requirements.txt

# 추가 패키지 설치 (PostgreSQL 지원)
pip install psycopg2-binary

# 데이터베이스 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 슈퍼유저 생성 (선택사항)
python manage.py createsuperuser

# 샘플 데이터 생성 (있는 경우)
python manage.py make_sample

# Django 개발 서버 실행 (포트 8000)
python manage.py runserver 0.0.0.0:8000
```

### ⚡ 7. FastAPI 설정 및 실행

**새 터미널을 열어서:**

```bash
# 가상환경 활성화
conda activate onboarding_quest

# FastAPI 프로젝트 디렉토리로 이동
cd fast_api

# 의존성 설치
pip install -r requirements.txt

# FastAPI 서버 실행 (포트 8001)
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 🚀 8. 시스템 실행 순서 (통합 버전)

올바른 시스템 시작 순서:

1. **PostgreSQL 서비스 시작** (자동 시작 설정 권장)
2. **Qdrant 서버 실행**
   ```bash
   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```
3. **🚀 FastAPI 통합 서버 실행 (8001포트)**
   ```bash
   cd fast_api
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```
4. **Django 서버 실행 (8000포트)**
   ```bash
   cd django_prj/onboarding_quest
   python manage.py runserver 0.0.0.0:8000
   ```

### ⚠️ 중요: 포트 통합 완료
- **기존**: rag_fastapi_server.py (8001) + fast_api (8001) → 포트 충돌!
- **현재**: Django (8000) + FastAPI 통합 서버 (8001) → 깔끔한 분리!

## 🌐 서비스 접속

- **🏠 Django 웹 애플리케이션**: http://localhost:8000
- **⚡ FastAPI 백엔드**: http://localhost:8001
- **📚 FastAPI API 문서**: http://localhost:8001/docs
- **🛠️ Django 관리자**: http://localhost:8000/admin
- **🤖 Qdrant 대시보드**: http://localhost:6333/dashboard (있는 경우)

## 🧪 설치 검증

### 시스템 상태 확인
```bash
# PostgreSQL 연결 확인
psql -U postgres -h localhost -c "SELECT version();"

# Qdrant 서버 확인
curl http://localhost:6333/health

# FastAPI 상태 확인
curl http://localhost:8001/health

# Django 상태 확인
curl http://localhost:8000/
```

### RAG 시스템 테스트
1. Django 웹페이지 접속: http://localhost:8000
2. 로그인 후 챗봇 페이지 이동
3. 테스트 질문 입력
4. FastAPI 로그에서 RAG 시스템 동작 확인

## 📊 FastAPI 통합 엔드포인트

### 🤖 RAG 채팅 시스템 (통합 완료)
- `POST /api/chat/rag` - **🚀 RAG 기반 챗봇 응답 생성** (메인 엔드포인트)
- `GET /api/chat/sessions/{user_id}` - 사용자 채팅 세션 목록 조회
- `POST /api/chat/session/create` - 새 채팅 세션 생성
- `POST /api/chat/session/delete` - 채팅 세션 삭제
- `GET /api/chat/messages/{session_id}` - 채팅 메시지 조회

### 📄 문서 관리 시스템 (신규 통합)
- `POST /api/documents/upload` - **문서 업로드 및 임베딩 처리**
- `POST /api/documents/delete` - 문서 삭제 (파일 + Qdrant 벡터)
- `POST /api/documents/update` - 문서 정보 수정
- `GET /api/documents/list` - 부서별 문서 목록 조회
- `GET /api/documents/download/{docs_id}` - 문서 다운로드

### 👥 인증 및 사용자 관리
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `GET /api/users/` - 사용자 목록 조회 (필터링 지원)
- `POST /api/users/` - 사용자 생성
- `GET /api/users/{user_id}` - 사용자 상세 조회
- `PUT /api/users/{user_id}` - 사용자 정보 수정
- `DELETE /api/users/{user_id}` - 사용자 삭제

### 🏢 회사 및 부서 관리
- `GET /api/companies/` - 회사 목록 조회
- `POST /api/companies/` - 회사 생성
- `GET /api/departments/` - 부서 목록 조회
- `POST /api/departments/` - 부서 생성

### 📋 멘토링 시스템
- `GET /api/mentorship/` - 멘토링 관계 조회
- `POST /api/mentorship/` - 멘토링 관계 생성
- `GET /api/tasks/manage/` - 태스크 관리
- `POST /api/tasks/assign/` - 태스크 할당

### ⚡ 시스템 상태
- `GET /health` - **통합 서버 상태 확인**
- `GET /docs` - **Swagger API 문서** (모든 엔드포인트 통합)

## 🔧 주요 기능

### Django 웹 애플리케이션
- **사용자 인증**: 로그인/로그아웃, 권한 관리
- **멘토링 시스템**: 멘토-멘티 매칭 및 관리
- **태스크 관리**: 할당, 진행상황 추적
- **🤖 RAG 챗봇**: LangGraph 기반 AI 상담 시스템 (통합 FastAPI 호출)
- **문서 관리**: 업로드, 다운로드, 벡터 검색

### FastAPI 통합 백엔드
- **🚀 완전 통합 구조**: 모든 API가 하나의 서버에 통합
- **RESTful API**: 완전한 CRUD 작업 지원
- **PostgreSQL 연동**: 관계형 데이터베이스 활용
- **🔍 RAG 시스템**: Qdrant + OpenAI 기반 벡터 검색
- **📄 문서 관리**: 업로드/삭제/수정/다운로드 (Qdrant 연동)
- **자동 API 문서화**: Swagger/OpenAPI 지원
- **CORS 설정**: 프론트엔드 연동 지원

### 🤖 LangGraph RAG 시스템
- **자동 질문 분류**: 일반 대화 vs 문서 검색 필요 판단
- **품질 평가 시스템**: 답변 품질 자동 평가 및 재작성
- **부서별 문서 필터링**: 사용자 부서에 맞는 문서만 검색
- **대화 히스토리 관리**: 세션 기반 문맥 유지
- **성능 모니터링**: 응답 시간 및 RAG 사용률 추적

## 🧪 개발 및 테스트

### RAG 시스템 테스트

#### 1. 통합 시스템 상태 확인
```bash
# FastAPI 통합 서버 상태 확인
curl http://localhost:8001/health

# Qdrant 연결 확인
curl http://localhost:6333/health

# Django 연결 확인
curl http://localhost:8000/
```

#### 2. RAG 챗봇 테스트 (통합 엔드포인트)
```bash
# 통합 RAG 챗봇 API 테스트
curl -X POST "http://localhost:8001/api/chat/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "휴가 신청 방법을 알려주세요",
    "user_id": 1,
    "department_id": 1,
    "session_id": null
  }'
```

#### 3. 문서 업로드 테스트 (통합 엔드포인트)
```bash
# 문서 업로드 (통합 FastAPI)
curl -X POST "http://localhost:8001/api/documents/upload" \
  -F "file=@document.pdf" \
  -F "department_id=1" \
  -F "common_doc=false" \
  -F "original_file_name=테스트문서.pdf" \
  -F "description=테스트용 문서입니다"
```

#### 4. 세션 관리 테스트
```bash
# 새 세션 생성
curl -X POST "http://localhost:8001/api/chat/session/create" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=1"

# 사용자 세션 목록 조회
curl "http://localhost:8001/api/chat/sessions/1"
```

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
psql -U postgres -h localhost
DROP DATABASE onboarding_quest_db;
CREATE DATABASE onboarding_quest_db;
```

## 🛠️ 기술 스택

### Backend
- **Django 4.x**: 웹 프레임워크
- **🚀 FastAPI (통합)**: REST API 서버 (모든 기능 통합)
- **PostgreSQL**: 메인 데이터베이스
- **SQLAlchemy**: ORM (FastAPI)
- **Django ORM**: ORM (Django)

### AI/ML & RAG
- **🤖 LangGraph**: AI 에이전트 워크플로우 엔진
- **OpenAI API**: GPT-4/GPT-4o-mini 기반 언어 모델
- **Qdrant**: 벡터 데이터베이스 (문서 검색)
- **LangChain**: RAG 파이프라인 구성

### Frontend
- **Django Templates**: 서버 사이드 렌더링
- **Bootstrap**: UI 프레임워크
- **JavaScript**: 실시간 챗봇 인터페이스 (통합 API 호출)

### 🔄 통합 아키텍처
```
Django Templates → JavaScript → FastAPI 통합 서버 → RAG/Database
     (8000)                          (8001)           (PostgreSQL + Qdrant)
```

## 🔒 보안 고려사항

- 환경 변수를 통한 민감 정보 관리
- Django CSRF 보호
- SQL Injection 방지 (ORM 사용)
- 사용자 인증 및 권한 검증
- RAG 시스템 부서별 문서 접근 제어

## 🚨 문제 해결

### 통합 관련 일반적인 문제들

#### 포트 충돌 오류 (해결됨)
```bash
# ✅ 현재 상태: 포트 충돌 완전 해결
# Django: 8000번 포트
# FastAPI 통합 서버: 8001번 포트

# 🚫 이전 문제: rag_fastapi_server.py와 fast_api 모두 8001번 사용
# ✅ 해결: rag_fastapi_server.py 제거, 기능을 fast_api로 통합
```

#### PostgreSQL 연결 오류
```bash
# 서비스 상태 확인
sudo systemctl status postgresql
# 또는 Windows에서
net start postgresql-x64-17
```

#### Qdrant 연결 오류
```bash
# Docker 컨테이너 상태 확인
docker ps | grep qdrant

# 재시작
docker restart <qdrant_container_id>
```

#### RAG 시스템 초기화 실패
1. OpenAI API 키 확인 (`.env` 파일)
2. Qdrant 서버 실행 상태 확인
3. PostgreSQL 연결 확인
4. FastAPI 통합 서버 로그 확인

#### 문서 업로드 실패
1. 파일 크기 확인 (기본 50MB 제한)
2. 지원 파일 형식 확인
3. 업로드 디렉토리 권한 확인
4. 통합 엔드포인트 `/api/documents/upload` 사용 확인

#### Django 챗봇 API 호출 오류
```bash
# 챗봇 JavaScript에서 올바른 엔드포인트 사용 확인:
# ✅ http://127.0.0.1:8001/api/chat/rag
# ✅ http://127.0.0.1:8001/api/chat/sessions/{user_id}
# ✅ http://127.0.0.1:8001/api/chat/session/create
```

## 📈 성능 최적화

### 추천 설정
- **PostgreSQL**: connection pooling 설정
- **Qdrant**: 인덱스 최적화
- **Django**: 캐싱 활성화
- **🚀 FastAPI 통합 서버**: gunicorn 멀티워커 사용

### 모니터링
- FastAPI 통합 서버 로그에서 RAG 응답 시간 확인
- Qdrant 대시보드에서 벡터 검색 성능 모니터링
- PostgreSQL 쿼리 성능 분석
- `/docs` 엔드포인트에서 API 성능 모니터링

## 🎉 통합 완료 요약

### ✅ 완료된 작업
1. **포트 충돌 해결**: Django(8000) + FastAPI(8001) 깔끔한 분리
2. **서버 통합**: `rag_fastapi_server.py` 제거, 모든 기능을 `fast_api`로 통합
3. **API 경로 통합**: 일관된 `/api/*` 경로 구조
4. **문서 관리 통합**: 업로드/삭제/수정 기능을 FastAPI로 이전
5. **Django 챗봇 연동**: 통합 FastAPI 엔드포인트 호출로 변경

### 🏆 통합의 장점
- **단순한 아키텍처**: 하나의 FastAPI 서버로 모든 API 제공
- **유지보수성 향상**: 중복 코드 제거, 일관된 API 구조
- **배포 간소화**: 관리할 서버 수 감소
- **성능 향상**: 단일 서버에서 최적화된 처리

### 🚀 배포 준비 완료
현재 상태에서 바로 production 환경에 배포 가능한 안정된 구조입니다.