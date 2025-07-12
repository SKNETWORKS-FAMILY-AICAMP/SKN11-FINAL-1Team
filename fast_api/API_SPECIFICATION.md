# OnBoarding Quest FastAPI - API 명세서

## 개요

OnBoarding Quest는 새로운 직원의 온보딩 과정을 관리하는 FastAPI 기반의 RESTful API 서비스입니다.

- **Base URL**: `http://localhost:8000`
- **API 버전**: v1
- **데이터 형식**: JSON
- **인증**: 현재 미구현 (향후 JWT 토큰 기반 인증 예정)

## 데이터 모델

### 1. Company (회사)
```json
{
  "company_id": 1,
  "company_name": "string"
}
```

### 2. Department (부서)
```json
{
  "department_id": 1,
  "department_name": "string",
  "description": "string (optional)",
  "company_id": 1,
  "company": {
    "company_id": 1,
    "company_name": "string"
  }
}
```

### 3. User (사용자)
```json
{
  "user_id": 1,
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "job_part": "string",
  "position": 1,
  "join_date": "YYYY-MM-DD",
  "skill": "string (optional)",
  "role": "mentor|mentee",
  "exp": 0,
  "admin": false,
  "department_id": 1,
  "mentorship_id" : 1,
  "company_id": 1,
  "department": {...},
  "company": {...}
}
```

### 4. Template (템플릿)
```json
{
  "template_id": 1,
  "template_title": "string",
  "template_description": "string (optional)",
  "department_id": 1,
  "department": {...}
}
```

### 5. TaskManage (태스크 관리)
```json
{
  "task_manage_id": 1,
  "title": "string",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "difficulty": "string (optional)",
  "description": "string (optional)",
  "exp": 1,
  "order": 1,
  "template_id": 1,
  "template": {...}
}
```

### 6. TaskAssign (태스크 할당)
```json
{
  "task_assign_id": 1,
  "title": "string (optional)",
  "start_date": "YYYY-MM-DD (optional)",
  "end_date": "YYYY-MM-DD (optional)",
  "status": 0,
  "difficulty": "string (optional)",
  "description": "string (optional)",
  "exp": 0.0,
  "order": 1,
  "user_id": 1,
  "task_manage_id": 1,
  "mentorship_id": 1,
  "user": {...},
  "task_manage": {...}
}
```

## API 엔드포인트

## 1. 회사 관리 API

### 1.1 회사 생성
- **URL**: `POST /api/companies/`
- **설명**: 새 회사를 생성합니다.
- **요청 본문**:
```json
{
  "company_name": "SKN 테크놀로지"
}
```
- **응답**: `201 Created`
```json
{
  "company_id": 1,
  "company_name": "SKN 테크놀로지"
}
```

### 1.2 회사 목록 조회
- **URL**: `GET /api/companies/`
- **설명**: 모든 회사 목록을 조회합니다.
- **쿼리 파라미터**:
  - `skip`: int (기본값: 0) - 건너뛸 레코드 수
  - `limit`: int (기본값: 100) - 조회할 최대 레코드 수
- **응답**: `200 OK`
```json
[
  {
    "company_id": 1,
    "company_name": "SKN 테크놀로지"
  }
]
```

### 1.3 특정 회사 조회
- **URL**: `GET /api/companies/{company_id}`
- **설명**: 특정 회사 정보를 조회합니다.
- **응답**: `200 OK`
```json
{
  "company_id": 1,
  "company_name": "SKN 테크놀로지"
}
```

### 1.4 회사 정보 수정
- **URL**: `PUT /api/companies/{company_id}`
- **설명**: 회사 정보를 수정합니다.
- **요청 본문**:
```json
{
  "company_name": "SKN 테크놀로지 (수정됨)"
}
```
- **응답**: `200 OK`

### 1.5 회사 삭제
- **URL**: `DELETE /api/companies/{company_id}`
- **설명**: 회사를 삭제합니다.
- **응답**: `200 OK`
```json
{
  "message": "회사가 성공적으로 삭제되었습니다"
}
```

## 2. 부서 관리 API

### 2.1 부서 생성
- **URL**: `POST /api/departments/`
- **설명**: 새 부서를 생성합니다.
- **요청 본문**:
```json
{
  "department_name": "개발팀",
  "description": "소프트웨어 개발 부서",
  "company_id": 1
}
```
- **응답**: `201 Created`

### 2.2 부서 목록 조회
- **URL**: `GET /api/departments/`
- **설명**: 모든 부서 목록을 조회합니다.
- **쿼리 파라미터**:
  - `skip`: int (기본값: 0)
  - `limit`: int (기본값: 100)

### 2.3 특정 부서 조회
- **URL**: `GET /api/departments/{department_id}`
- **설명**: 특정 부서 정보를 조회합니다.

### 2.4 부서 정보 수정
- **URL**: `PUT /api/departments/{department_id}`
- **설명**: 부서 정보를 수정합니다.

### 2.5 부서 삭제
- **URL**: `DELETE /api/departments/{department_id}`
- **설명**: 부서를 삭제합니다.

## 3. 사용자 관리 API

### 3.1 사용자 생성
- **URL**: `POST /api/users/`
- **설명**: 새 사용자를 생성합니다.
- **요청 본문**:
```json
{
  "first_name": "길동",
  "last_name": "홍",
  "email": "hong@example.com",
  "password": "securepassword123",
  "job_part": "백엔드 개발",
  "position": 1,
  "join_date": "2024-01-15",
  "skill": "Python, FastAPI",
  "role": "mentor",
  "exp": 5,
  "level": 3,
  "admin": false,
  "department_id": 1,
  "company_id": 1
}
```
- **응답**: `201 Created`

### 3.2 사용자 목록 조회
- **URL**: `GET /api/users/`
- **설명**: 모든 사용자 목록을 조회합니다.
- **쿼리 파라미터**:
  - `skip`: int (기본값: 0)
  - `limit`: int (기본값: 100)

### 3.3 멘토 목록 조회
- **URL**: `GET /api/users/mentors/`
- **설명**: 멘토 역할의 사용자 목록을 조회합니다.

### 3.4 멘티 목록 조회
- **URL**: `GET /api/users/mentees/`
- **설명**: 멘티 역할의 사용자 목록을 조회합니다.

### 3.5 특정 사용자 조회
- **URL**: `GET /api/users/{user_id}`
- **설명**: 특정 사용자 정보를 조회합니다.

### 3.6 사용자 정보 수정
- **URL**: `PUT /api/users/{user_id}`
- **설명**: 사용자 정보를 수정합니다.

### 3.7 사용자 삭제
- **URL**: `DELETE /api/users/{user_id}`
- **설명**: 사용자를 삭제합니다.

### 3.8 특정 멘토의 멘티 목록 조회
- **URL**: `GET /api/users/mentors/{mentor_id}/mentees`
- **설명**: 특정 멘토가 담당하는 멘티 목록을 조회합니다.

## 4. 템플릿 관리 API

### 4.1 템플릿 생성
- **URL**: `POST /api/templates/`
- **설명**: 새 템플릿을 생성합니다.
- **요청 본문**:
```json
{
  "template_title": "신입 개발자 온보딩",
  "template_description": "신입 개발자를 위한 온보딩 프로세스",
  "department_id": 1
}
```

### 4.2 템플릿 목록 조회
- **URL**: `GET /api/templates/`
- **설명**: 모든 템플릿 목록을 조회합니다.

### 4.3 특정 템플릿 조회
- **URL**: `GET /api/templates/{template_id}`
- **설명**: 특정 템플릿 정보를 조회합니다.

### 4.4 템플릿 정보 수정
- **URL**: `PUT /api/templates/{template_id}`
- **설명**: 템플릿 정보를 수정합니다.

### 4.5 템플릿 삭제
- **URL**: `DELETE /api/templates/{template_id}`
- **설명**: 템플릿을 삭제합니다.

## 5. 태스크 관리 API

### 5.1 태스크 관리 생성
- **URL**: `POST /api/tasks/manage/`
- **설명**: 새 태스크 관리를 생성합니다.
- **요청 본문**:
```json
{
  "title": "FastAPI 기본 학습",
  "start_date": "2024-01-15",
  "end_date": "2024-01-30",
  "difficulty": "중급",
  "description": "FastAPI 기본 개념 학습",
  "exp": 100,
  "order": 1,
  "template_id": 1
}
```

### 5.2 태스크 관리 목록 조회
- **URL**: `GET /api/tasks/manage/`
- **설명**: 모든 태스크 관리 목록을 조회합니다.

### 5.3 특정 태스크 관리 조회
- **URL**: `GET /api/tasks/manage/{task_id}`
- **설명**: 특정 태스크 관리 정보를 조회합니다.

### 5.4 태스크 관리 수정
- **URL**: `PUT /api/tasks/manage/{task_id}`
- **설명**: 태스크 관리 정보를 수정합니다.

### 5.5 태스크 관리 삭제
- **URL**: `DELETE /api/tasks/manage/{task_id}`
- **설명**: 태스크 관리를 삭제합니다.

## 6. 태스크 할당 API

### 6.1 태스크 할당 생성
- **URL**: `POST /api/tasks/assign/`
- **설명**: 사용자에게 태스크를 할당합니다.
- **요청 본문**:
```json
{
  "title": "FastAPI 기본 학습",
  "start_date": "2024-01-15",
  "end_date": "2024-01-30",
  "status": 0,
  "difficulty": "중급",
  "description": "FastAPI 기본 개념 학습",
  "exp": 100,
  "order": 1,
  "user_id": 1,
  "task_manage_id": 1,
  "mentorship_id": 1
}
```

### 6.2 태스크 할당 목록 조회
- **URL**: `GET /api/tasks/assign/`
- **설명**: 모든 태스크 할당 목록을 조회합니다.

### 6.3 특정 태스크 할당 조회
- **URL**: `GET /api/tasks/assign/{task_id}`
- **설명**: 특정 태스크 할당 정보를 조회합니다.

### 6.4 태스크 할당 수정
- **URL**: `PUT /api/tasks/assign/{task_id}`
- **설명**: 태스크 할당 정보를 수정합니다.

### 6.5 태스크 할당 삭제
- **URL**: `DELETE /api/tasks/assign/{task_id}`
- **설명**: 태스크 할당을 삭제합니다.

### 6.6 사용자별 할당된 태스크 조회
- **URL**: `GET /api/tasks/assign/user/{user_id}`
- **설명**: 특정 사용자에게 할당된 태스크 목록을 조회합니다.
- **쿼리 파라미터**:
  - `skip`: int (기본값: 0)
  - `limit`: int (기본값: 100)

### 6.7 태스크 상태 업데이트
- **URL**: `PATCH /api/tasks/assign/{task_id}/status`
- **설명**: 태스크 할당의 상태를 업데이트합니다.
- **쿼리 파라미터**:
  - `status`: int (0: 미시작, 1: 진행중, 2: 완료, 3: 보류)
- **응답**: `200 OK`
```json
{
  "message": "태스크 상태가 '진행중'로 업데이트되었습니다"
}
```

## 7. 하위 태스크 API

### 7.1 하위 태스크 생성
- **URL**: `POST /api/tasks/subtask/`
- **설명**: 새 하위 태스크를 생성합니다.
- **요청 본문**:
```json
{
  "task_assign_id": 1
}
```

## 8. 멘토링 관계 API

### 8.1 멘토링 관계 생성
- **URL**: `POST /api/tasks/mentorship/`
- **설명**: 멘토와 멘티 간의 관계를 생성합니다.
- **요청 본문**:
```json
{
  "mentor_id": 1,
  "mentee_id": 2
}
```

### 8.2 멘토링 관계 목록 조회
- **URL**: `GET /api/tasks/mentorship/`
- **설명**: 모든 멘토링 관계 목록을 조회합니다.

## 9. 폼 관리 인터페이스

### 9.1 폼 관리 홈
- **URL**: `GET /forms/`
- **설명**: 폼 관리 메인 페이지를 표시합니다.
- **기능**: 
  - 시스템 개요 대시보드
  - 각 관리 기능으로의 빠른 링크
  - 시스템 정보 표시

### 9.2 회사 관리 폼
- **URL**: `GET /forms/companies`
- **설명**: 회사 생성 및 관리 인터페이스를 제공합니다.
- **기능**:
  - 회사 생성 폼
  - 등록된 회사 목록 조회
  - 회사 정보 수정/삭제 (향후 구현)

### 9.3 부서 관리 폼
- **URL**: `GET /forms/departments`
- **설명**: 부서 생성 및 관리 인터페이스를 제공합니다.
- **기능**:
  - 부서 생성 폼 (회사 선택 포함)
  - 등록된 부서 목록 조회
  - 부서 정보 수정/삭제 (향후 구현)

### 9.4 사용자 관리 폼
- **URL**: `GET /forms/users`
- **설명**: 사용자 생성 및 관리 인터페이스를 제공합니다.
- **기능**:
  - 사용자 생성 폼 (멘토/멘티/관리자 역할 설정)
  - 등록된 사용자 목록 조회
  - 역할별 사용자 표시
  - 사용자 정보 수정/삭제 (향후 구현)

### 9.5 템플릿 관리 폼
- **URL**: `GET /forms/templates`
- **설명**: 온보딩 템플릿 생성 및 관리 인터페이스를 제공합니다.
- **기능**:
  - 템플릿 생성 폼
  - 등록된 템플릿 목록 조회
  - 템플릿 정보 수정/삭제 (향후 구현)

### 9.6 태스크 관리 폼
- **URL**: `GET /forms/tasks`
- **설명**: 학습 태스크 생성 및 관리 인터페이스를 제공합니다.
- **기능**:
  - 태스크 생성 폼 (난이도, 경험치, 순서 설정)
  - 등록된 태스크 목록 조회
  - 태스크 정보 수정/삭제 (향후 구현)

### 9.7 파일 업로드 관리
- **URL**: `GET /forms/upload`
- **설명**: 파일 업로드 인터페이스를 제공합니다.
- **기능**:
  - 파일 업로드 폼 (이미지, 문서, 텍스트 파일 지원)
  - 파일 유효성 검증 (형식, 크기 제한)
  - 업로드 성공 시 파일 정보 표시

### 9.8 업로드된 파일 목록
- **URL**: `GET /forms/uploads`
- **설명**: 업로드된 파일 목록 및 관리 인터페이스를 제공합니다.
- **기능**:
  - 업로드된 파일 목록 테이블
  - 파일 미리보기 (이미지 파일)
  - 파일 다운로드/보기 링크
  - 파일 형식별 분류 표시

## 상태 코드

### 성공 응답
- `200 OK`: 요청이 성공적으로 처리됨
- `201 Created`: 새 리소스가 성공적으로 생성됨

### 오류 응답
- `400 Bad Request`: 잘못된 요청 (예: 이미 등록된 이메일)
- `404 Not Found`: 요청한 리소스를 찾을 수 없음
- `422 Unprocessable Entity`: 요청 데이터 유효성 검증 실패
- `500 Internal Server Error`: 서버 내부 오류

### 오류 응답 형식
```json
{
  "detail": "오류 메시지"
}
```

## 사용 예시

### 1. 폼 관리 인터페이스 사용법

#### 웹 브라우저를 통한 관리 (권장)
1. **서버 접속**: http://localhost:8000/ (폼 관리 홈으로 자동 리다이렉트)
2. **회사 생성**: '회사 관리' 카드 클릭 → 회사명 입력 → '회사 생성' 버튼 클릭
3. **부서 생성**: '부서 관리' 카드 클릭 → 부서명, 설명, 회사 선택 → '부서 생성' 버튼 클릭
4. **사용자 생성**: '사용자 관리' 카드 클릭 → 사용자 정보 입력 → 역할 선택 → '사용자 생성' 버튼 클릭
5. **템플릿 생성**: '템플릿 관리' 카드 클릭 → 템플릿 제목, 설명, 부서 선택 → '템플릿 생성' 버튼 클릭
6. **태스크 생성**: '태스크 관리' 카드 클릭 → 태스크 정보, 난이도, 경험치 입력 → '태스크 생성' 버튼 클릭

### 2. API를 통한 직접 호출

#### 회사 및 부서 생성
```bash
# 회사 생성
curl -X POST "http://localhost:8000/api/companies/" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "SKN 테크놀로지"}'

# 부서 생성
curl -X POST "http://localhost:8000/api/departments/" \
  -H "Content-Type: application/json" \
  -d '{"department_name": "개발팀", "description": "소프트웨어 개발 부서", "company_id": 1}'
```

### 2. 사용자 생성
```bash
# 멘토 생성
curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "길동",
    "last_name": "홍",
    "email": "hong@example.com",
    "password": "securepassword123",
    "job_part": "백엔드 개발",
    "position": 1,
    "join_date": "2024-01-15",
    "skill": "Python, FastAPI",
    "role": "mentor",
    "exp": 5,
    "admin": false,
    "department_id": 1,
    "company_id": 1
  }'
```

### 3. 태스크 관리 및 할당
```bash
# 템플릿 생성
curl -X POST "http://localhost:8000/api/templates/" \
  -H "Content-Type: application/json" \
  -d '{"template_title": "신입 개발자 온보딩", "template_description": "신입 개발자를 위한 온보딩 프로세스", "department_id": 1}'

# 태스크 관리 생성
curl -X POST "http://localhost:8000/api/tasks/manage/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI 기본 학습",
    "start_date": "2024-01-15",
    "end_date": "2024-01-30",
    "difficulty": "중급",
    "description": "FastAPI 기본 개념 학습",
    "exp": 100,
    "order": 1,
    "template_id": 1
  }'

# 태스크 할당
curl -X POST "http://localhost:8000/api/tasks/assign/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI 기본 학습",
    "start_date": "2024-01-15",
    "end_date": "2024-01-30",
    "status": 0,
    "difficulty": "중급",
    "description": "FastAPI 기본 개념 학습",
    "exp": 100,
    "order": 1,
    "user_id": 1,
    "task_manage_id": 1
  }'
```

## 기술 스택

- **프레임워크**: FastAPI
- **데이터베이스**: SQLite3
- **ORM**: SQLAlchemy
- **데이터 검증**: Pydantic
- **비밀번호 암호화**: bcrypt
- **문서화**: OpenAPI/Swagger (자동 생성)

## 자동 문서화

FastAPI는 OpenAPI 표준을 기반으로 자동으로 API 문서를 생성합니다:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 서버 실행 방법

### 1. 의존성 설치
```bash
cd fast_api
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
uvicorn main:app --reload
```

### 3. 폼 관리 인터페이스 및 API 문서 확인
- **폼 관리 홈**: http://localhost:8000/ (자동 리다이렉트)
- **폼 관리 인터페이스**: http://localhost:8000/forms/
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 데이터베이스 구조

본 API는 다음과 같은 12개의 테이블로 구성된 관계형 데이터베이스를 사용합니다:

1. **company** - 회사 정보
2. **department** - 부서 정보 (회사와 1:N 관계)
3. **user** - 사용자 정보 (부서/회사와 N:1 관계)
4. **template** - 온보딩 템플릿 (부서와 N:1 관계)
5. **task_manage** - 태스크 관리 (템플릿과 N:1 관계)
6. **task_assign** - 태스크 할당 (사용자, 태스크 관리와 N:1 관계)
7. **subtask** - 하위 태스크 (태스크 할당과 N:1 관계)
8. **mentorship** - 멘토링 관계 (멘토-멘티 관계)
9. **memo** - 메모 (태스크 할당과 N:1 관계)
10. **chat_session** - 채팅 세션 (사용자와 N:1 관계)
11. **chat_message** - 채팅 메시지 (채팅 세션과 N:1 관계)
12. **docs** - 문서 (부서와 N:1 관계)

## 향후 개발 예정 기능

다음 기능들은 데이터 모델은 정의되어 있지만 API는 아직 구현되지 않았습니다:

### 1. 메모 관리 API
- 태스크별 메모 작성/조회/수정/삭제
- 사용자별 메모 관리

### 2. 채팅 기능 API
- 채팅 세션 생성/관리
- 실시간 메시지 송수신
- 채팅 기록 조회

### 3. 문서 관리 API
- 부서별 문서 업로드/관리
- 공용 문서 관리
- 파일 업로드/다운로드

### 4. 인증/권한 관리
- JWT 토큰 기반 인증
- 역할별 권한 관리
- 세션 관리

### 5. 알림 시스템
- 태스크 마감일 알림
- 멘토링 일정 알림
- 시스템 공지사항

## 보안 고려사항

- 비밀번호는 bcrypt 해시로 안전하게 저장됩니다
- 현재 인증 시스템은 구현되지 않았으므로 개발/테스트 환경에서만 사용하세요
- 프로덕션 환경에서는 JWT 토큰 기반 인증을 구현할 예정입니다

---

*본 문서는 OnBoarding Quest FastAPI 프로젝트의 API 명세서입니다. 최신 정보는 Swagger UI를 참고하시기 바랍니다.* 