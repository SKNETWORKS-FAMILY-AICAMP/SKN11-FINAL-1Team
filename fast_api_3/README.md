# 온보딩 퀘스트 API v3

신입사원 온보딩 프로세스 관리 시스템 FastAPI 애플리케이션입니다.  
**기존 `report_test.db` 데이터베이스 파일을 사용**하여 정확한 스키마와 데이터 타입을 지원합니다.

## 🚀 주요 특징

- **기존 데이터베이스 사용**: 새로운 데이터베이스를 생성하지 않고 기존 `report_test.db` 사용
- **정확한 스키마 매핑**: Django 마이그레이션 파일을 기반으로 한 정확한 데이터 타입 지원
- **사업자번호 형식**: `company_id`를 문자열 타입으로 처리 (000-00-00000 형식)
- **완벽한 관계 매핑**: 외래키 관계와 제약 조건 완벽 지원
- **역할 기반 시스템**: 멘토/멘티 역할 구분 및 멘토십 관리

## 🛠️ 설치 및 실행

### 1. 의존성 설치

```bash
pip install fastapi uvicorn sqlalchemy passlib pydantic python-multipart
```

### 2. 서버 실행

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8005 --reload
```

### 3. 웹 브라우저에서 접근

- **메인 페이지**: http://127.0.0.1:8005/
- **API 문서**: http://127.0.0.1:8005/docs
- **대안 API 문서**: http://127.0.0.1:8005/redoc
- **헬스 체크**: http://127.0.0.1:8005/health
- **스키마 정보**: http://127.0.0.1:8005/schema

## 📚 API 엔드포인트

### 기본 엔드포인트

- `GET /` - 루트 엔드포인트
- `GET /health` - 헬스 체크
- `GET /schema` - 데이터베이스 스키마 정보

### 회사 관리 (Companies)

- `GET /api/v1/companies` - 회사 목록 조회
- `POST /api/v1/companies` - 회사 생성
- `GET /api/v1/companies/{company_id}` - 회사 조회 (company_id는 문자열)
- `PUT /api/v1/companies/{company_id}` - 회사 수정
- `DELETE /api/v1/companies/{company_id}` - 회사 삭제
- `GET /api/v1/companies/{company_id}/departments` - 회사 소속 부서 목록
- `GET /api/v1/companies/{company_id}/users` - 회사 소속 사용자 목록

### 부서 관리 (Departments)

- `GET /api/v1/departments` - 부서 목록 조회
- `POST /api/v1/departments` - 부서 생성
- `GET /api/v1/departments/{department_id}` - 부서 조회
- `PUT /api/v1/departments/{department_id}` - 부서 수정
- `DELETE /api/v1/departments/{department_id}` - 부서 삭제
- `GET /api/v1/departments/{department_id}/users` - 부서 소속 사용자 목록
- `GET /api/v1/departments/{department_id}/curriculums` - 부서 소속 커리큘럼 목록

### 사용자 관리 (Users)

- `GET /api/v1/users` - 사용자 목록 조회
- `POST /api/v1/users` - 사용자 생성
- `GET /api/v1/users/{user_id}` - 사용자 조회
- `PUT /api/v1/users/{user_id}` - 사용자 수정
- `DELETE /api/v1/users/{user_id}` - 사용자 삭제
- `GET /api/v1/users/role/{role}` - 역할별 사용자 목록 (mentee/mentor)
- `GET /api/v1/users/email/{email}` - 이메일로 사용자 조회
- `GET /api/v1/users/employee-number/{employee_number}` - 사번으로 사용자 조회
- `GET /api/v1/users/{user_id}/task-assigns` - 사용자 할당 과제 목록

### 과제 할당 관리 (Task Assigns)

- `GET /api/v1/task-assigns` - 과제 할당 목록 조회
- `POST /api/v1/task-assigns` - 과제 할당 생성
- `GET /api/v1/task-assigns/{task_assign_id}` - 과제 할당 조회
- `PUT /api/v1/task-assigns/{task_assign_id}` - 과제 할당 수정
- `DELETE /api/v1/task-assigns/{task_assign_id}` - 과제 할당 삭제
- `GET /api/v1/task-assigns/user/{user_id}` - 사용자별 과제 할당 목록
- `GET /api/v1/task-assigns/mentorship/{mentorship_id}` - 멘토십별 과제 할당 목록
- `GET /api/v1/task-assigns/status/{status}` - 상태별 과제 할당 목록

### 멘토십 관리 (Mentorships)

- `GET /api/v1/mentorships` - 멘토십 목록 조회
- `POST /api/v1/mentorships` - 멘토십 생성
- `GET /api/v1/mentorships/{mentorship_id}` - 멘토십 조회
- `PUT /api/v1/mentorships/{mentorship_id}` - 멘토십 수정
- `DELETE /api/v1/mentorships/{mentorship_id}` - 멘토십 삭제
- `GET /api/v1/mentorships/mentor/{mentor_id}` - 멘토별 멘토십 목록
- `GET /api/v1/mentorships/mentee/{mentee_id}` - 멘티별 멘토십 목록
- `GET /api/v1/mentorships/{mentorship_id}/task-assigns` - 멘토십별 과제 할당 목록

## 📊 데이터베이스 스키마

### 핵심 테이블

1. **core_company**: 회사 정보
   - `company_id` (VARCHAR(12), PRIMARY KEY) - 사업자번호 형식
   - `company_name` (VARCHAR(255)) - 회사명

2. **core_department**: 부서 정보
   - `department_id` (INTEGER, PRIMARY KEY) - 부서 ID
   - `department_name` (VARCHAR(50)) - 부서명
   - `company_id` (VARCHAR(12), FOREIGN KEY) - 소속 회사 ID

3. **core_user**: 사용자 정보
   - `user_id` (INTEGER, PRIMARY KEY) - 사용자 ID
   - `email` (VARCHAR(254), UNIQUE) - 이메일
   - `employee_number` (INTEGER, UNIQUE) - 사번
   - `role` (VARCHAR(20)) - 역할 (mentee/mentor)
   - `company_id` (VARCHAR(12), FOREIGN KEY) - 소속 회사 ID
   - `department_id` (INTEGER, FOREIGN KEY) - 소속 부서 ID

4. **core_mentorship**: 멘토십 정보
   - `mentorship_id` (INTEGER, PRIMARY KEY) - 멘토십 ID
   - `mentor_id` (INTEGER, FOREIGN KEY) - 멘토 ID
   - `mentee_id` (INTEGER, FOREIGN KEY) - 멘티 ID

5. **core_taskassign**: 과제 할당 정보
   - `task_assign_id` (INTEGER, PRIMARY KEY) - 과제 할당 ID
   - `user_id` (INTEGER, FOREIGN KEY) - 사용자 ID
   - `mentorship_id` (INTEGER, FOREIGN KEY) - 멘토십 ID
   - `status` (INTEGER) - 상태

## 🔧 기술 스택

- **FastAPI**: 웹 프레임워크
- **SQLAlchemy**: ORM
- **SQLite**: 데이터베이스
- **Pydantic**: 데이터 검증
- **Uvicorn**: ASGI 서버
- **Passlib**: 비밀번호 해싱

## 📝 사용 예시

### 회사 생성

```bash
curl -X POST "http://127.0.0.1:8005/api/v1/companies" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "123-45-67890",
    "company_name": "테스트 회사"
  }'
```

### 사용자 생성

```bash
curl -X POST "http://127.0.0.1:8005/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "employee_number": 1001,
    "first_name": "홍",
    "last_name": "길동",
    "role": "mentee",
    "position": "신입사원",
    "job_part": "개발",
    "company_id": "123-45-67890",
    "department_id": 1
  }'
```

### 멘토십 생성

```bash
curl -X POST "http://127.0.0.1:8005/api/v1/mentorships" \
  -H "Content-Type: application/json" \
  -d '{
    "mentor_id": 1,
    "mentee_id": 2
  }'
```

## 🎯 주요 개선사항

1. **정확한 데이터 타입**: company_id를 문자열로 처리
2. **기존 데이터베이스 사용**: 새로운 테이블 생성 없이 기존 DB 활용
3. **완벽한 검증**: 사업자번호 형식, 역할 검증, 외래키 검증
4. **역할 기반 시스템**: 멘토/멘티 역할 구분 및 멘토십 관리
5. **한국어 지원**: 모든 응답 메시지 한국어 제공

## 🔒 보안 기능

- 비밀번호 해싱 (bcrypt)
- 데이터 검증 (Pydantic)
- 외래키 무결성 검사
- 역할 기반 접근 제어

## 📂 프로젝트 구조

```
fast_api_3/
├── main.py              # 메인 애플리케이션
├── database.py          # 데이터베이스 설정
├── models.py            # SQLAlchemy 모델
├── schemas.py           # Pydantic 스키마
├── crud.py              # CRUD 작업
├── routers/             # API 라우터
│   ├── __init__.py
│   ├── companies.py
│   ├── departments.py
│   ├── users.py
│   ├── task_assigns.py
│   └── mentorships.py
├── requirements.txt     # 의존성
└── README.md           # 문서
```

## 🚀 배포

실제 운영 환경에서는 다음과 같이 실행하세요:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8005
```

## 🎉 완료된 기능

- ✅ 기존 데이터베이스 연동
- ✅ 정확한 스키마 매핑
- ✅ company_id 문자열 타입 지원
- ✅ 멘토/멘티 역할 시스템
- ✅ 완벽한 CRUD 작업
- ✅ 데이터 검증 및 에러 처리
- ✅ 외래키 관계 지원
- ✅ 자동 API 문서 생성

---

**온보딩 퀘스트 API v3** - 기존 데이터베이스와 완벽한 호환성을 제공하는 신입사원 온보딩 관리 시스템 🎯 