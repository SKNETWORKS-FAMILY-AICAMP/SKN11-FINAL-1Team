# Django + FastAPI 통합 가이드

## 📋 개요

이 프로젝트는 Django 웹 프레임워크를 **프론트엔드**로, FastAPI를 **백엔드**로 사용하는 완전 분리형 아키텍처입니다. Django에서 복잡한 백엔드 로직을 제거하고 FastAPI가 모든 API와 비즈니스 로직을 담당합니다.

## 🏗️ 아키텍처

```
Django (프론트엔드)           FastAPI (백엔드)
        ↓                          ↓
    포트 8000                   포트 8001
        ↓                          ↓
  - 템플릿 렌더링              - REST API 제공
  - 기본 인증                  - 비즈니스 로직
  - 정적 파일 제공             - 데이터베이스 처리
  - FastAPI 연동               - JWT 인증
        ↓                          ↓
    동일한 SQLite 데이터베이스 공유
```

## 🔧 Django 프로젝트 변경사항

### ✅ 제거된 백엔드 로직
- **복잡한 CRUD 로직**: 부서/사용자 생성, 수정, 삭제
- **비즈니스 로직**: 멘토쉽 관리, 과제 관리, 커리큘럼 관리
- **데이터 처리**: 통계 계산, 복잡한 쿼리 처리
- **API 엔드포인트**: JSON 응답 처리
- **복잡한 폼 처리**: forms.py 파일 제거

### ✅ 유지된 프론트엔드 기능
- **템플릿 렌더링**: HTML 페이지 생성
- **기본 인증**: 로그인/로그아웃 (Django 세션)
- **정적 파일**: CSS, JavaScript, 이미지 제공
- **FastAPI 연동**: API 호출 및 프록시 기능
- **관리자 페이지**: 기본 사용자 관리만

### 🎯 각 앱의 역할 변경

#### 1. **account 앱**
- **이전**: 복잡한 사용자/부서 CRUD + 템플릿
- **현재**: 로그인/로그아웃 + 템플릿 렌더링만

#### 2. **mentor 앱**
- **이전**: 멘토쉽/커리큘럼 관리 로직 + 템플릿
- **현재**: 멘토 페이지 템플릿 렌더링만

#### 3. **mentee 앱**
- **이전**: 과제 관리 로직 + 템플릿
- **현재**: 멘티 페이지 템플릿 렌더링만

#### 4. **common 앱**
- **이전**: 문서/챗봇 로직 + FastAPI 연동
- **현재**: 기본 템플릿 + FastAPI 연동 기능

#### 5. **core 앱**
- **이전**: 모든 모델 관리자 등록
- **현재**: 기본 사용자 관리만

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# Django 의존성 설치
cd django_prj/onboarding_quest
pip install -r requirements.txt

# FastAPI 의존성 설치
cd ../../fast_api/app
pip install -r requirements.txt
```

### 2. 데이터베이스 마이그레이션

```bash
# Django 마이그레이션 (기본 테이블만)
cd django_prj/onboarding_quest
python manage.py migrate

# FastAPI 데이터베이스 초기화 (전체 데이터)
cd ../../fast_api/app
python init_db.py
```

### 3. 서버 실행

#### 방법 1: 통합 실행 스크립트 사용 (권장)
```bash
# 프로젝트 루트에서
python start_servers.py
```

#### 방법 2: 개별 서버 실행
```bash
# 터미널 1: Django 프론트엔드 서버
cd django_prj/onboarding_quest
python manage.py runserver 127.0.0.1:8000

# 터미널 2: FastAPI 백엔드 서버
cd fast_api
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## 🌐 액세스 포인트

### Django 프론트엔드
- **메인 페이지**: http://localhost:8000/
- **관리자 페이지**: http://localhost:8000/admin/
- **통합 대시보드**: http://localhost:8000/common/integrated/
- **API 테스트**: http://localhost:8000/common/api/dashboard/
- **헬스 체크**: http://localhost:8000/health/

### FastAPI 백엔드
- **API 루트**: http://localhost:8001/
- **API 문서**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **헬스 체크**: http://localhost:8001/health

## 🔐 인증 정보

### Django 관리자 계정
- **이메일**: admin@example.com
- **비밀번호**: admin123

### FastAPI 테스트 계정
- **관리자**: admin@example.com / admin123
- **멘토**: mentor@example.com / mentor123
- **멘티**: mentee@example.com / mentee123

## 📊 데이터 흐름

### 1. 사용자 로그인
```
사용자 → Django 로그인 → FastAPI JWT 토큰 생성 → 프론트엔드 저장
```

### 2. 데이터 조회
```
Django 템플릿 → FastAPI API 호출 → 데이터베이스 조회 → JSON 응답 → 화면 렌더링
```

### 3. 데이터 수정
```
Django 폼 → FastAPI API 호출 → 데이터베이스 수정 → 성공/실패 응답 → 리다이렉트
```

## 🔧 개발 가이드

### Django 개발 (프론트엔드)
```bash
# 새로운 페이지 추가
# 1. 템플릿 파일 생성
# 2. 뷰 함수 생성 (템플릿 렌더링만)
# 3. URL 패턴 추가

# 예시: 새로운 페이지 추가
def new_page(request):
    context = {
        'user': request.user,
        'fastapi_url': settings.FASTAPI_BASE_URL,
        'title': '새 페이지'
    }
    return render(request, 'app/new_page.html', context)
```

### FastAPI 개발 (백엔드)
```bash
# 새로운 API 추가
# 1. 스키마 정의
# 2. 라우터 함수 생성
# 3. 비즈니스 로직 구현

# 예시: 새로운 API 추가
@router.post("/new-endpoint")
async def new_endpoint(data: NewSchema, db: Session = Depends(get_db)):
    # 비즈니스 로직 구현
    return {"message": "성공"}
```

## 🚨 주의사항

### ⚠️ 하지 말아야 할 것
- Django 뷰에서 복잡한 데이터베이스 쿼리 수행
- Django에서 JSON API 응답 생성
- FastAPI에서 HTML 템플릿 렌더링

### ✅ 권장사항
- 모든 비즈니스 로직은 FastAPI에서 처리
- Django는 템플릿 렌더링과 정적 파일 제공만
- JavaScript로 FastAPI API 호출

## 🎯 향후 개선사항

### 🔄 개선 가능 사항
- [ ] 실시간 WebSocket 연동
- [ ] 프론트엔드 프레임워크 통합 (React, Vue.js)
- [ ] 마이크로서비스 아키텍처 확장
- [ ] 캐시 시스템 통합
- [ ] 로그 시스템 통합

## 📞 문제 해결

### 1. Django 프론트엔드 문제
```bash
# 템플릿 렌더링 문제
python manage.py check
python manage.py runserver --verbosity=2

# 정적 파일 문제
python manage.py collectstatic
```

### 2. FastAPI 백엔드 문제
```bash
# API 문제
cd fast_api
uvicorn app.main:app --reload --log-level debug

# 데이터베이스 문제
cd app
python init_db.py
```

---

**🎉 Django 프론트엔드 + FastAPI 백엔드 완전 분리형 아키텍처 완성!**

이제 Django는 순수 프론트엔드로, FastAPI는 순수 백엔드로 각각의 역할에 집중할 수 있습니다. 