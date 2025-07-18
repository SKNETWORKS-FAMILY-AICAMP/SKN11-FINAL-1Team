# Onboarding Quest FastAPI (PostgreSQL Edition)

온보딩 퀘스트를 위한 FastAPI 기반 REST API 서버입니다. PostgreSQL 데이터베이스를 사용합니다.

## 🚀 특징

- **PostgreSQL 데이터베이스** 사용
- **완전한 CRUD 기능** 제공
- **RESTful API** 설계
- **한국어 지원** 및 유니코드 처리
- **자동 API 문서화** (Swagger/OpenAPI)
- **관계형 데이터 모델** 구현

## 📦 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. PostgreSQL 설정

#### PostgreSQL 설치 (Mac)
```bash
brew install postgresql
brew services start postgresql@14
```

#### 데이터베이스 생성
```bash
createdb onboarding_quest
```

### 3. 애플리케이션 실행

```bash
python main.py
```

서버가 http://localhost:8001 에서 실행됩니다.

## 🔧 설정

`config.py` 파일에서 데이터베이스 설정을 변경할 수 있습니다:

```python
# PostgreSQL 데이터베이스 설정
db_host: str = "localhost"
db_port: int = 5432
db_name: str = "onboarding_quest"
db_user: str = "your_username"
db_password: str = "your_password"
```

## 📊 데이터베이스 스키마

### 주요 테이블

1. **company** - 회사 정보
2. **department** - 부서 정보
3. **user** - 사용자 정보 (멘토/멘티)
4. **template** - 템플릿 정보
5. **task_manage** - 태스크 관리
6. **task_assign** - 태스크 할당
7. **mentorship** - 멘토링 관계
8. **chat_session** - 채팅 세션
9. **chat_message** - 채팅 메시지
10. **docs** - 문서 관리
11. **memo** - 메모 관리

## 🌐 API 엔드포인트

### 주요 엔드포인트

- **GET** `/health` - 서버 상태 확인
- **GET** `/api/` - API 정보 조회
- **GET** `/docs` - Swagger UI
- **GET** `/redoc` - ReDoc 문서

### 엔티티별 CRUD

#### 회사 (Companies)
- `GET /api/companies/` - 회사 목록 조회
- `POST /api/companies/` - 회사 생성
- `GET /api/companies/{company_id}` - 회사 상세 조회
- `PUT /api/companies/{company_id}` - 회사 정보 수정
- `DELETE /api/companies/{company_id}` - 회사 삭제

#### 부서 (Departments)
- `GET /api/departments/` - 부서 목록 조회
- `POST /api/departments/` - 부서 생성
- `GET /api/departments/{department_id}` - 부서 상세 조회
- `PUT /api/departments/{department_id}` - 부서 정보 수정
- `DELETE /api/departments/{department_id}` - 부서 삭제

#### 사용자 (Users)
- `GET /api/users/` - 사용자 목록 조회
- `POST /api/users/` - 사용자 생성
- `GET /api/users/{user_id}` - 사용자 상세 조회
- `PUT /api/users/{user_id}` - 사용자 정보 수정
- `DELETE /api/users/{user_id}` - 사용자 삭제

#### 템플릿 (Templates)
- `GET /api/templates/` - 템플릿 목록 조회
- `POST /api/templates/` - 템플릿 생성
- `GET /api/templates/{template_id}` - 템플릿 상세 조회
- `PUT /api/templates/{template_id}` - 템플릿 정보 수정
- `DELETE /api/templates/{template_id}` - 템플릿 삭제

#### 태스크 (Tasks)
- `GET /api/tasks/manage/` - 태스크 관리 목록 조회
- `POST /api/tasks/manage/` - 태스크 관리 생성
- `GET /api/tasks/assign/` - 태스크 할당 목록 조회
- `POST /api/tasks/assign/` - 태스크 할당 생성

## 🧪 테스트 예시

### 1. 회사 생성
```bash
curl -X POST "http://localhost:8001/api/companies/" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "테스트 회사"}'
```

### 2. 부서 생성
```bash
curl -X POST "http://localhost:8001/api/departments/" \
  -H "Content-Type: application/json" \
  -d '{"department_name": "개발팀", "description": "소프트웨어 개발 부서", "company_id": 1}'
```

### 3. 사용자 생성
```bash
curl -X POST "http://localhost:8001/api/users/" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "김", "last_name": "개발", "email": "kim@test.com", "password": "testpass123", "job_part": "백엔드", "position": 3, "join_date": "2024-01-15", "skill": "Python, FastAPI", "role": "mentor", "exp": 100, "department_id": 1, "company_id": 1}'
```

## 🎯 주요 변경사항 (SQLite → PostgreSQL)

1. **데이터베이스 드라이버**: `sqlite3` → `psycopg2-binary`
2. **데이터베이스 URL**: SQLite 파일 → PostgreSQL 연결 문자열
3. **데이터 타입**: SQLite 타입 → PostgreSQL 타입
4. **포트 번호**: 8000 → 8001 (충돌 방지)
5. **사용자 테이블**: `lvl` 컬럼 제거

## 📝 로그 및 디버깅

애플리케이션은 SQLAlchemy 쿼리 로그를 출력하여 디버깅을 지원합니다.

## 🔗 관련 링크

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/)

---

**개발자**: SKN11-FINAL-1Team  
**버전**: 1.0.0  
**데이터베이스**: PostgreSQL  
**Python**: 3.11+ 