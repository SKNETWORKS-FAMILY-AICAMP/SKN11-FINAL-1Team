# Onboarding Quest API - Django to FastAPI Migration

## 📋 프로젝트 개요

이 프로젝트는 Django 기반의 온보딩 퀘스트 애플리케이션을 FastAPI로 마이그레이션한 결과물입니다.

### 🔄 마이그레이션 완료 기능

- ✅ **사용자 관리 시스템** (인증, 권한 관리)
- ✅ **부서 관리** (CRUD 작업)
- ✅ **멘토쉽 관리** (멘토-멘티 매칭)
- ✅ **과제 관리** (커리큘럼, 과제 템플릿, 과제 할당)
- ✅ **JWT 기반 인증**
- ✅ **SQLAlchemy ORM**
- ✅ **Pydantic 데이터 검증**
- ✅ **자동 API 문서 생성**

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일 생성)
cp .env.example .env
```

### 2. 데이터베이스 초기화

```bash
# 데이터베이스 및 샘플 데이터 생성
python -m app.init_db
```

### 3. 서버 실행

```bash
# 개발 서버 실행
uvicorn app.main:app --reload

# 또는 Python으로 직접 실행
python -m app.main
```

### 4. API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📊 테스트

```bash
# API 테스트 실행
python test_api.py
```

## 🔐 기본 로그인 정보

데이터베이스 초기화 후 다음 계정으로 로그인할 수 있습니다:

- **관리자**: admin@example.com / admin123
- **멘토**: mentor@example.com / mentor123
- **멘티**: mentee@example.com / mentee123

## 🏗️ 프로젝트 구조

```
fast_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── config.py              # 설정 관리
│   ├── database.py            # 데이터베이스 연결
│   ├── dependencies.py        # 의존성 주입
│   ├── init_db.py             # 데이터베이스 초기화
│   ├── models/
│   │   └── __init__.py        # SQLAlchemy 모델
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py            # 사용자 스키마
│   │   ├── department.py      # 부서 스키마
│   │   ├── task.py            # 과제 스키마
│   │   ├── mentorship.py      # 멘토쉽 스키마
│   │   └── company.py         # 회사 스키마
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py            # 인증 라우터
│   │   ├── user.py            # 사용자 라우터
│   │   ├── department.py      # 부서 라우터
│   │   ├── task.py            # 과제 라우터
│   │   └── mentorship.py      # 멘토쉽 라우터
│   └── servies/
│       ├── __init__.py
│       ├── auth_service.py    # 인증 서비스
│       ├── user_service.py    # 사용자 서비스
│       ├── department_service.py
│       └── mentorship_service.py
├── requirements.txt           # 의존성 목록
├── test_api.py               # API 테스트 스크립트
├── .env.example              # 환경 변수 템플릿
└── README.md                 # 이 파일
```

## 🔄 Django vs FastAPI 비교

### Django → FastAPI 마이그레이션 내용

| 기능 | Django | FastAPI |
|------|--------|---------|
| **모델** | Django ORM | SQLAlchemy |
| **직렬화** | Django Serializers | Pydantic |
| **인증** | Django Auth + Sessions | JWT + Bearer Token |
| **라우팅** | Django URLs | FastAPI Routers |
| **검증** | Django Forms | Pydantic Models |
| **문서** | Django REST Framework | 자동 OpenAPI |

### 주요 개선사항

1. **성능 향상**: 비동기 처리로 더 빠른 응답 시간
2. **타입 안정성**: Python 타입 힌트 활용
3. **자동 문서화**: OpenAPI 기반 자동 문서 생성
4. **현대적 개발**: 최신 Python 기능 활용

## 📡 API 엔드포인트

### 🔐 인증 (Authentication)

```
POST   /auth/login           # 로그인
POST   /auth/login-json      # JSON 로그인
POST   /auth/logout          # 로그아웃
GET    /auth/me              # 현재 사용자 정보
GET    /auth/verify-token    # 토큰 검증
POST   /auth/refresh-token   # 토큰 갱신
```

### 👥 사용자 (Users)

```
GET    /users/               # 사용자 목록
POST   /users/               # 사용자 생성
GET    /users/{id}           # 사용자 조회
PUT    /users/{id}           # 사용자 수정
DELETE /users/{id}           # 사용자 삭제
POST   /users/{id}/activate  # 사용자 활성화
POST   /users/{id}/deactivate # 사용자 비활성화
POST   /users/{id}/change-password # 비밀번호 변경
POST   /users/{id}/reset-password  # 비밀번호 초기화
```

### 🏢 부서 (Departments)

```
GET    /departments/         # 부서 목록
POST   /departments/         # 부서 생성
GET    /departments/{id}     # 부서 조회
PUT    /departments/{id}     # 부서 수정
DELETE /departments/{id}     # 부서 삭제
```

### 📋 과제 (Tasks)

```
GET    /tasks/assigns        # 과제 할당 목록
GET    /tasks/assigns/{id}   # 과제 할당 조회
PUT    /tasks/assigns/{id}   # 과제 할당 수정
GET    /tasks/curriculums    # 커리큘럼 목록
POST   /tasks/curriculums    # 커리큘럼 생성
GET    /tasks/manages        # 과제 템플릿 목록
POST   /tasks/manages        # 과제 템플릿 생성
```

### 🤝 멘토쉽 (Mentorships)

```
GET    /mentorships/         # 멘토쉽 목록
POST   /mentorships/         # 멘토쉽 생성
GET    /mentorships/{id}     # 멘토쉽 조회
PUT    /mentorships/{id}     # 멘토쉽 수정
DELETE /mentorships/{id}     # 멘토쉽 삭제
```

## ⚙️ 환경 설정

`.env` 파일 예시:

```env
# 데이터베이스 설정
DATABASE_URL=sqlite:///./onboarding_quest.db

# 보안 설정
SECRET_KEY=your-secret-key-here-change-in-production

# 애플리케이션 설정
DEBUG=true
ENVIRONMENT=development

# JWT 설정
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080

# 파일 업로드 설정
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760

# AI/ML 설정 (선택사항)
# OPENAI_API_KEY=your-openai-api-key
# QDRANT_URL=http://localhost:6333
```

## 📝 데이터베이스 스키마

### 주요 테이블

- **companies**: 회사 정보
- **departments**: 부서 정보
- **users**: 사용자 정보 (멘토/멘티)
- **curriculums**: 커리큘럼 정보
- **task_manages**: 과제 템플릿
- **mentorships**: 멘토쉽 관계
- **task_assigns**: 과제 할당
- **memos**: 메모
- **chat_sessions**: 채팅 세션
- **chat_messages**: 채팅 메시지
- **docs**: 문서

## 🔧 수정 및 고쳐야 할 부분

### 1. 현재 알려진 이슈

1. **파일 업로드 기능 미구현**
   - 문서 업로드 기능이 아직 구현되지 않았습니다.
   - `fast_api/app/routers/` 에 파일 업로드 라우터 추가 필요

2. **채팅 기능 미완성**
   - 채팅 모델은 있지만 실제 채팅 기능이 구현되지 않았습니다.
   - WebSocket 기반 실시간 채팅 구현 필요

3. **AI 기능 미구현**
   - OpenAI, Qdrant 연동 기능이 설정만 되어 있습니다.
   - 실제 AI 기능 구현 필요

### 2. 권장 수정사항

1. **에러 핸들링 개선**
   ```python
   # fast_api/app/exceptions.py 생성
   from fastapi import HTTPException
   
   class CustomHTTPException(HTTPException):
       def __init__(self, status_code: int, detail: str, error_code: str = None):
           super().__init__(status_code=status_code, detail=detail)
           self.error_code = error_code
   ```

2. **로깅 시스템 추가**
   ```python
   # fast_api/app/logger.py 생성
   import logging
   from app.config import settings
   
   logging.basicConfig(
       level=settings.LOG_LEVEL,
       format=settings.LOG_FORMAT
   )
   ```

3. **데이터베이스 마이그레이션 도구 추가**
   ```bash
   # Alembic 설정
   alembic init alembic
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

4. **테스트 코드 보강**
   ```python
   # tests/ 디렉토리 생성
   # pytest 기반 테스트 코드 작성
   pytest tests/
   ```

5. **CORS 설정 보완**
   ```python
   # main.py에서 CORS 설정 개선
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],  # 프론트엔드 도메인
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### 3. 성능 최적화

1. **데이터베이스 쿼리 최적화**
   - N+1 문제 해결을 위한 eager loading 사용
   - 인덱스 추가

2. **캐싱 구현**
   - Redis 기반 캐싱 시스템 구현
   - 자주 조회되는 데이터 캐싱

3. **비동기 처리 강화**
   - 더 많은 엔드포인트에서 비동기 처리 적용

## 🚀 배포 가이드

### 1. 도커 배포

```dockerfile
# Dockerfile 예시
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 프로덕션 설정

```python
# config.py에서 프로덕션 설정 추가
if settings.is_production():
    DATABASE_URL = "postgresql://user:password@localhost/db"
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
```

## 📞 지원 및 문의

문제가 발생하거나 추가 기능이 필요한 경우:

1. **이슈 보고**: GitHub Issues 활용
2. **문서 확인**: API 문서 (http://localhost:8000/docs) 참조
3. **로그 확인**: 애플리케이션 로그 파일 확인

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**마이그레이션 완료 시점**: 2024년 12월
**FastAPI 버전**: 0.104.1
**Python 버전**: 3.11+ 