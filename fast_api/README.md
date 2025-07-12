# 온보딩 퀘스트 FastAPI 서버 (SQLite3 DB 기반)

ERD 설계를 기반으로 한 멘토링 온보딩 퀘스트를 위한 완전한 FastAPI 백엔드 서버입니다.

## 🚀 주요 기능

### 🌐 폼 관리 인터페이스
웹 브라우저를 통한 직관적인 데이터 관리 인터페이스:
- **대시보드**: 시스템 개요 및 빠른 링크
- **회사/부서 관리**: 조직 구조 생성 및 관리
- **사용자 관리**: 멘토/멘티/관리자 계정 생성 및 관리
- **템플릿 관리**: 온보딩 템플릿 생성 및 관리
- **태스크 관리**: 학습 태스크 생성 및 난이도/경험치 설정
- **파일 업로드**: 문서, 이미지 등 파일 업로드 및 관리
- **실시간 피드백**: 성공/실패 메시지 및 유효성 검증

### 🔌 RESTful API
완전한 CRUD 기능을 제공하는 RESTful API 엔드포인트

### 📊 데이터베이스 구조
ERD 파일 `onboarding_v1.vuerd.json`을 기반으로 한 완전한 관계형 데이터베이스 구조:

- **Company**: 회사 정보 관리
- **Department**: 부서 정보 관리 
- **User**: 사용자 관리 (멘토/멘티 구분)
- **Template**: 온보딩 템플릿 관리
- **TaskManage**: 템플릿 내 태스크 관리
- **TaskAssign**: 사용자별 태스크 할당
- **Mentorship**: 멘토-멘티 관계 관리
- **Subtask**: 하위 태스크 관리
- **Memo**: 태스크별 메모 기능
- **ChatSession**: 채팅 세션 관리
- **ChatMessage**: 채팅 메시지 저장
- **Docs**: 문서 관리

### 🔧 기술 스택
- **FastAPI**: 고성능 웹 프레임워크
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **SQLite3**: 경량 데이터베이스
- **Pydantic**: 데이터 검증 및 직렬화
- **Passlib**: 비밀번호 암호화
- **Uvicorn**: ASGI 서버

## 🏗️ 프로젝트 구조

```
fast_api/
├── main.py              # FastAPI 애플리케이션 진입점
├── config.py            # 설정 관리
├── database.py          # 데이터베이스 연결 설정
├── models.py            # SQLAlchemy 모델 정의
├── schemas.py           # Pydantic 스키마 정의
├── crud.py              # CRUD 작업 함수
├── requirements.txt     # 의존성 패키지
├── API_SPECIFICATION.md # 완전한 API 명세서
├── routers/            # API 라우터
│   ├── __init__.py
│   ├── companies.py    # 회사 관리 API
│   ├── departments.py  # 부서 관리 API
│   ├── templates.py    # 템플릿 관리 API
│   ├── users.py        # 사용자 관리 API
│   ├── tasks.py        # 태스크 관리 API
│   ├── forms.py        # 폼 관리 인터페이스
│   └── chatbot.py      # 챗봇 API
├── templates/          # HTML 템플릿
│   ├── base.html       # 기본 레이아웃 템플릿
│   └── forms/          # 폼 관리 템플릿
│       ├── index.html           # 폼 관리 홈
│       ├── company_form.html    # 회사 관리 폼
│       ├── department_form.html # 부서 관리 폼
│       ├── user_form.html       # 사용자 관리 폼
│       ├── template_form.html   # 템플릿 관리 폼
│       ├── task_form.html       # 태스크 관리 폼
│       ├── upload_form.html     # 파일 업로드 폼
│       ├── upload_success.html  # 업로드 성공 페이지
│       └── uploaded_files.html  # 업로드된 파일 목록
├── static/             # 정적 파일
│   ├── css/
│   │   └── base.css    # 기본 스타일시트
│   ├── js/             # JavaScript 파일
│   ├── img/            # 이미지 파일
│   │   └── default_profile.png
│   └── uploads/        # 업로드된 파일 저장소
├── onboarding_quest.db # SQLite 데이터베이스 파일
└── README.md           # 프로젝트 문서
```

## 🚀 빠른 시작

### 1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
python main.py
```

또는

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 폼 관리 인터페이스 및 API 문서 확인
서버 실행 후 다음 URL에서 시스템을 사용할 수 있습니다:
- **폼 관리 홈**: http://localhost:8000/ (메인 페이지, 자동 리다이렉트)
- **폼 관리 인터페이스**: http://localhost:8000/forms/
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API 엔드포인트

### 기본 엔드포인트
- `GET /` - 서버 상태 및 엔드포인트 정보
- `GET /health` - 헬스 체크

### 회사 관리 API (`/api/companies/`)
- `POST /` - 새 회사 생성
- `GET /` - 회사 목록 조회
- `GET /{company_id}` - 특정 회사 조회
- `PUT /{company_id}` - 회사 정보 수정
- `DELETE /{company_id}` - 회사 삭제

### 부서 관리 API (`/api/departments/`)
- `POST /` - 새 부서 생성
- `GET /` - 부서 목록 조회
- `GET /{department_id}` - 특정 부서 조회
- `PUT /{department_id}` - 부서 정보 수정
- `DELETE /{department_id}` - 부서 삭제

### 템플릿 관리 API (`/api/templates/`)
- `POST /` - 새 템플릿 생성
- `GET /` - 템플릿 목록 조회
- `GET /{template_id}` - 특정 템플릿 조회
- `PUT /{template_id}` - 템플릿 정보 수정
- `DELETE /{template_id}` - 템플릿 삭제

### 사용자 관리 API (`/api/users/`)
- `POST /` - 새 사용자 생성
- `GET /` - 모든 사용자 조회
- `GET /{user_id}` - 특정 사용자 조회
- `PUT /{user_id}` - 사용자 정보 수정
- `DELETE /{user_id}` - 사용자 삭제
- `GET /mentors/` - 멘토 목록 조회
- `GET /mentees/` - 멘티 목록 조회
- `GET /mentors/{mentor_id}/mentees` - 특정 멘토의 멘티 목록 조회

### 태스크 관리 API (`/api/tasks/`)
#### 태스크 관리 (템플릿 태스크)
- `POST /manage/` - 새 태스크 관리 생성
- `GET /manage/` - 태스크 관리 목록 조회
- `GET /manage/{task_id}` - 특정 태스크 관리 조회
- `PUT /manage/{task_id}` - 태스크 관리 수정
- `DELETE /manage/{task_id}` - 태스크 관리 삭제

#### 태스크 할당 (사용자 할당 태스크)
- `POST /assign/` - 새 태스크 할당 생성
- `GET /assign/` - 태스크 할당 목록 조회
- `GET /assign/{task_id}` - 특정 태스크 할당 조회
- `PUT /assign/{task_id}` - 태스크 할당 수정
- `DELETE /assign/{task_id}` - 태스크 할당 삭제
- `GET /assign/user/{user_id}` - 특정 사용자의 할당된 태스크 목록
- `PATCH /assign/{task_id}/status` - 태스크 상태 업데이트

#### 기타 태스크 기능
- `POST /subtask/` - 하위 태스크 생성
- `POST /mentorship/` - 멘토링 관계 생성
- `GET /mentorship/` - 멘토링 관계 목록 조회

### 챗봇 API (`/api/chatbot/`)
- `POST /message` - 챗봇 메시지 처리
- `GET /stats` - 챗봇 통계 조회
- `GET /history/{user_id}` - 사용자별 대화 이력 조회

## 🧪 API 테스트 예시

### 1. 회사 생성
```bash
curl -X POST "http://127.0.0.1:8000/api/companies/" \
-H "Content-Type: application/json" \
-d '{"company_name": "SKN 테크놀로지"}'
```

### 2. 부서 생성
```bash
curl -X POST "http://127.0.0.1:8000/api/departments/" \
-H "Content-Type: application/json" \
-d '{"department_name": "개발팀", "description": "소프트웨어 개발 부서", "company_id": 1}'
```

### 3. 사용자 생성
```bash
curl -X POST "http://127.0.0.1:8000/api/users/" \
-H "Content-Type: application/json" \
-d '{
  "first_name": "홍길동",
  "last_name": "홍", 
  "email": "hong@skn.co.kr",
  "password": "password123",
  "job_part": "백엔드 개발자",
  "position": 3,
  "join_date": "2024-01-01",
  "skill": "Python, FastAPI, Django",
  "role": "mentor",
  "department_id": 1,
  "company_id": 1
}'
```

### 4. 템플릿 생성
```bash
curl -X POST "http://127.0.0.1:8000/api/templates/" \
-H "Content-Type: application/json" \
-d '{
  "template_title": "신입 개발자 온보딩",
  "template_description": "신입 개발자를 위한 기본 온보딩 과정",
  "department_id": 1
}'
```

### 5. 태스크 관리 생성
```bash
curl -X POST "http://127.0.0.1:8000/api/tasks/manage/" \
-H "Content-Type: application/json" \
-d '{
  "title": "FastAPI 기본 학습",
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "difficulty": "초급",
  "description": "FastAPI 프레임워크의 기본 개념과 사용법을 학습합니다",
  "exp": 100,
  "order": 1,
  "template_id": 1
}'
```

### 6. 태스크 할당
```bash
curl -X POST "http://127.0.0.1:8000/api/tasks/assign/" \
-H "Content-Type: application/json" \
-d '{
  "title": "FastAPI 기본 학습 실습",
  "start_date": "2024-01-15",
  "end_date": "2024-01-20", 
  "status": 1,
  "difficulty": "초급",
  "description": "FastAPI로 간단한 API 만들기",
  "exp": 100.0,
  "order": 1,
  "user_id": 1,
  "task_manage_id": 1
}'
```

## 🔐 보안 기능

- **비밀번호 암호화**: Passlib + bcrypt를 사용한 안전한 비밀번호 저장
- **데이터 검증**: Pydantic을 통한 입력 데이터 검증
- **외래 키 제약**: SQLAlchemy를 통한 데이터 무결성 보장
- **CORS 설정**: 안전한 크로스 오리진 요청 관리

## 🎯 주요 특징

1. **완전한 CRUD 기능**: 모든 엔티티에 대한 생성, 조회, 수정, 삭제 기능
2. **관계형 데이터**: 복잡한 테이블 간 관계를 완벽히 구현
3. **자동 문서화**: FastAPI의 자동 API 문서 생성
4. **타입 안정성**: Pydantic을 통한 강력한 타입 검증
5. **확장 가능한 구조**: 모듈화된 라우터 구조로 쉬운 확장

## 🗄️ 데이터베이스

- **파일**: `onboarding_quest.db` (SQLite3)
- **자동 생성**: 서버 시작 시 자동으로 테이블 생성
- **관계 설정**: 외래 키를 통한 완전한 관계형 구조
- **인덱스**: 성능 최적화를 위한 자동 인덱스 생성

## 📝 개발 노트

- ERD 설계 파일: `erd/onboarding_v1.vuerd.json`
- Python 3.13 호환
- SQLAlchemy 2.0+ 사용
- FastAPI 최신 버전 사용
- 한국어 지원

이 프로젝트는 실제 운영 환경에서 사용할 수 있는 완전한 백엔드 API 서버로 설계되었습니다. 