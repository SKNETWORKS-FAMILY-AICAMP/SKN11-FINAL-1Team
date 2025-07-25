# Django-LangGraph Agent 통합 시스템 사용 가이드

## 📖 개요

`Agent_LangGraph_final.py`의 스케줄러 기반 Agent 시스템이 Django `onboarding_quest` 프로젝트에 성공적으로 통합되었습니다.

**최신 업데이트**: `Agent_LangGraph_final.py` → `agent_langgraph.py`로 경로 변경 완료! ✅

## 🔄 경로 변경 업데이트

### 📝 수정된 파일들

1. **`agent_integration.py`**
   - ❌ 기존: `from Agent_LangGraph_final import ...`
   - ✅ 변경: `from agent_langgraph import ...`
   - 복잡한 경로 설정 제거, 동일 프로젝트 내 직접 임포트

2. **`apps.py`**
   - ✅ 로그 메시지에 "(agent_langgraph.py 연동)" 추가
   - Agent 시스템 소스 명시

3. **`agent_langgraph.py`**
   - ✅ 중복 import 정리
   - ✅ 필요한 스케줄러 함수들 확인 완료

### 🎯 경로 변경의 장점

1. **경로 단순화**: 복잡한 상대 경로 대신 동일 프로젝트 내 직접 임포트
2. **관리 편의성**: Django 프로젝트 내에서 Agent 코드 직접 관리
3. **의존성 감소**: `agent_test` 폴더 의존성 제거
4. **배포 용이성**: Django 프로젝트와 함께 단일 배포 가능

## 🏗️ 통합 아키텍처

### 1. **이중 Agent 시스템**
- **Django Agent**: Django 모델 기반 자동 리뷰, 보고서 생성, 알림
- **LangGraph Agent**: SQLite 기반 스케줄러 워크플로우 (30초, 시간별, 일별)

### 2. **자동 시작/중지**
- Django 앱 시작 시 자동으로 통합 Agent 시스템 실행
- 앱 종료 시 자동으로 모든 Agent 시스템 중지

### 3. **이벤트 기반 트리거**
- 태스크 상태 변화 시 즉시 Agent 체크 실행
- Django ORM과 FastAPI 양쪽 모두 지원

## 🚀 주요 기능

### ✅ **자동 리뷰 시스템**
```python
# 태스크 상태가 '검토요청'으로 변경되면
# 1. Django Agent: AI 기반 자동 리뷰 생성
# 2. LangGraph Agent: 즉시 체크 트리거
# 3. 멘티에게 알림 발송
```

### ✅ **온보딩 완료 감지**
```python
# 모든 태스크가 '완료'로 변경되면
# 1. Django Agent: 최종 보고서 생성
# 2. LangGraph Agent: 보고서 워크플로우 실행
# 3. 멘토에게 알림 발송
```

### ✅ **마감일 체크**
```python
# 백그라운드 스케줄러가 자동으로
# 1. 매일 마감일 체크
# 2. 오늘/내일/지난 마감일 알림
# 3. 멘티에게 자동 알림 발송
```

## 📁 파일 구조

```
django_prj/onboarding_quest/
├── agent_integration.py         # 통합 Agent 시스템
├── agent_langgraph.py          # 🎯 LangGraph Agent (메인)
├── agent_status_view.py         # Agent 모니터링 뷰
├── test_agent_path.py          # 경로 변경 테스트
├── AGENT_INTEGRATION_GUIDE.md  # 상세 가이드 (이 파일)
├── apps.py                     # Django 앱 설정
├── core/
│   └── apps.py                  # Django 앱 시작 시 Agent 자동 실행
└── mentee/
    └── views.py                 # 태스크 상태 변화 시 Agent 트리거

agent_test/
└── Agent_LangGraph_final.py     # 원본 LangGraph Agent (백업)
```

## 🔧 사용 방법

### 1. **자동 실행** (권장)
Django 서버 시작만 하면 자동으로 Agent 시스템이 실행됩니다.

```bash
cd django_prj/onboarding_quest
python manage.py runserver
```

### 2. **수동 제어**
```python
from agent_integration import start_agent_system, stop_agent_system, get_agent_current_status

# Agent 시스템 시작
start_agent_system()

# Agent 시스템 중지  
stop_agent_system()

# 상태 조회
status = get_agent_current_status()
```

### 3. **이벤트 트리거**
```python
from agent_integration import handle_task_status_change

# 태스크 상태 변화 시 Agent 이벤트 트리거
handle_task_status_change(
    task_id=123,
    old_status='진행중',
    new_status='검토요청', 
    user_id=456
)
```

### 4. **경로 변경 테스트**
```bash
# 경로 변경 테스트 실행
cd django_prj/onboarding_quest
python test_agent_path.py
```

## 📊 모니터링 API

### **Agent 상태 조회**
```http
GET /agent/status/
```

### **즉시 체크 트리거**
```http
POST /agent/trigger/
```

### **시스템 재시작** (관리자용)
```http
POST /agent/restart/
```

## 🔄 자동 워크플로우

### **태스크 검토 요청 워크플로우**
1. 멘티가 태스크 상태를 '검토요청'으로 변경
2. `mentee/views.py`의 `update_task_status()`에서 Agent 이벤트 트리거
3. Django Agent: 하위 태스크 기반 AI 자동 리뷰 생성
4. LangGraph Agent: 즉시 체크 실행으로 추가 워크플로우 처리
5. 멘티에게 리뷰 완료 알림 발송

### **온보딩 완료 워크플로우**
1. 마지막 태스크가 '완료'로 변경
2. Django Agent: 온보딩 완료 감지
3. AI 기반 종합 최종 보고서 생성
4. 보고서 파일 저장 (`reports/` 디렉토리)
5. LangGraph Agent: 최종 보고서 이메일 발송
6. 멘토에게 보고서 완성 알림

### **마감일 체크 워크플로우**
1. LangGraph Agent: 매일 오전 9시 자동 실행
2. 모든 멘티의 태스크 마감일 체크
3. 오늘/내일/지난 마감일 분류
4. 개인별 맞춤 알림 메시지 생성
5. 멘티에게 자동 알림 발송

## ⚙️ 설정

### **필수 환경 변수**
```bash
OPENAI_API_KEY=your_openai_api_key
DJANGO_SETTINGS_MODULE=onboarding_quest.settings
```

### **Agent 설정 수정**
`agent_integration.py`에서 다음 설정들을 수정할 수 있습니다:

```python
# Django 모니터링 주기 (기본: 5분)
time.sleep(300)

# LangGraph Agent 스케줄링 주기
# - 30초마다: 정기 체크
# - 매시 정각: 추가 체크  
# - 매일 오전 9시: 일일 종합 체크
```

## 🚨 주의사항

### **1. 경로 설정 (업데이트됨)**
- `agent_langgraph.py` 파일이 Django 프로젝트 내에 위치
- 기존 `agent_test` 폴더 의존성 제거됨
- 동일 프로젝트 내 직접 임포트 방식 사용

### **2. 데이터베이스 동시성**
- Django ORM과 SQLite 직접 접근이 동시에 발생할 수 있음
- WAL 모드 활성화로 동시성 개선

### **3. 로그 모니터링**
- Django 로그에서 Agent 시스템 상태 확인 가능
- `🤖`, `🚀`, `⚡`, `❌` 이모지로 Agent 관련 로그 식별
- "(agent_langgraph.py 연동)" 메시지로 새로운 경로 확인

## 🔍 트러블슈팅

### **Agent 시스템이 시작되지 않는 경우**
1. `agent_langgraph.py` 파일이 Django 프로젝트 내에 있는지 확인
2. OpenAI API 키 설정 확인
3. Django 로그에서 오류 메시지 확인

### **LangGraph Agent를 사용할 수 없는 경우**
- Django Agent만으로도 기본 기능 동작
- 로그에 "LangGraph not available" 메시지 확인

### **상태 변화가 감지되지 않는 경우**
- `mentee/views.py`의 `update_task_status()` 함수에서 Agent 호출 코드 확인
- 태스크 상태 변화 로그 확인

## 📈 확장 가능성

### **새로운 Agent 추가**
1. `agent_integration.py`에 새로운 Agent 클래스 추가
2. `start_monitoring()`에서 추가 Agent 시작
3. 이벤트 핸들러에서 새로운 Agent 호출

### **워크플로우 확장**
1. `agent_langgraph.py`에 새로운 노드 추가
2. LangGraph 워크플로우에 조건부 분기 추가
3. Django Agent에서 새로운 이벤트 타입 처리

## ✅ 확인 사항

- [x] `agent_integration.py`에서 `agent_langgraph` 임포트
- [x] `apps.py`에서 로그 메시지 업데이트  
- [x] `agent_langgraph.py`에 필요한 함수들 존재 확인
- [x] 가이드 문서 경로 정보 업데이트
- [x] 테스트 스크립트 생성
- [x] 경로 변경으로 인한 단순화 및 관리 편의성 향상

## 🚀 다음 단계

1. Django 서버 시작하여 Agent 시스템 동작 확인
2. 태스크 상태 변경으로 Agent 이벤트 트리거 테스트
3. Agent 모니터링 API 동작 확인
4. `python test_agent_path.py`로 경로 변경 테스트 실행

이제 Django `onboarding_quest` 프로젝트에서 강력한 LangGraph 기반 자동화 Agent 시스템을 사용할 수 있습니다! 🎉

**최신 업데이트**: `agent_langgraph.py`를 메인 Agent 시스템으로 사용하여 더욱 간편하고 효율적인 관리가 가능합니다!
