# AI 챗봇 시스템 - RAG 기반 문서 질의응답

이 프로젝트는 **RAG(Retrieval-Augmented Generation)** 기반의 AI 챗봇 시스템입니다. 사용자의 질의를 구분하여 문서 관련 질문일 때는 벡터 데이터베이스에서 관련 문서를 검색하고, 이를 바탕으로 답변을 생성하는 시스템입니다.

## 🏗️ 시스템 아키텍처

```
사용자 질의 → LangGraph 라우팅 → 
├── 문서 관련 질의 → RAG Agent (Qdrant 검색 + LLM 응답)
└── 일반 질의 → 일반 대화 Agent (LLM 직접 응답)
```

## 🔧 주요 기능

### 1. **Retriever 기능**
- **Qdrant** 벡터 데이터베이스를 사용한 문서 임베딩 및 검색
- **Sentence Transformers**를 이용한 문서 임베딩 생성
- 유사도 기반 관련 문서 검색

### 2. **LLM - Retriever - Vector DB 연결**
- **OpenAI GPT** 모델과 **Qdrant** 벡터 DB 연동
- 검색된 문서를 컨텍스트로 활용한 답변 생성
- 실시간 문서 추가 및 인덱싱

### 3. **LangGraph 구현**
- 사용자 질의를 자동으로 분류 (문서 관련 / 일반 대화 / 인사)
- 조건부 라우팅을 통한 적절한 에이전트 선택
- 비동기 워크플로우 처리

### 4. **Django 웹 UI**
- 실시간 채팅 인터페이스
- 세션 관리 및 채팅 히스토리
- 문서 업로드 기능
- 관리자 페이지

### 5. **REST API**
- 챗봇 대화 API
- 세션 관리 API
- 문서 업로드 API
- 헬스 체크 API

## 🛠️ 기술 스택

### Backend
- **Python 3.8+**
- **Django 4.2.7** - 웹 프레임워크
- **Django REST Framework** - API 개발
- **LangChain** - LLM 통합 프레임워크
- **LangGraph** - 워크플로우 관리
- **Qdrant** - 벡터 데이터베이스
- **OpenAI API** - 언어 모델
- **Sentence Transformers** - 텍스트 임베딩

### Frontend
- **HTML5 + CSS3 + JavaScript**
- **Bootstrap 5** - UI 프레임워크
- **Font Awesome** - 아이콘

### Database
- **SQLite** - 챗봇 데이터 저장
- **Qdrant** - 벡터 데이터 저장

## 📦 설치 및 실행

### 1. 프로젝트 클론 및 가상환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd SKN-FINAL-Project

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성 (또는 환경 변수 직접 설정)
export OPENAI_API_KEY="your-openai-api-key"
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="your-qdrant-api-key"  # 필요시
export DJANGO_SECRET_KEY="your-django-secret-key"
```

### 3. Qdrant 설정

```bash
# Docker를 이용한 Qdrant 실행
docker run -p 6333:6333 qdrant/qdrant

# 또는 Qdrant Cloud 서비스 사용
```

### 4. Django 설정 및 실행

```bash
# 데이터베이스 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 관리자 계정 생성 (선택사항)
python manage.py createsuperuser

# 개발 서버 실행
python manage.py runserver
```

### 5. 챗봇 테스트

```bash
# 챗봇 단독 테스트
python chatbot.py

# 웹 브라우저에서 접속
http://localhost:8000/
```

## 🚀 사용 방법

### 웹 인터페이스
1. 브라우저에서 `http://localhost:8000/` 접속
2. 채팅창에 메시지 입력
3. 문서 관련 질문 시 자동으로 관련 문서 검색 후 답변
4. 일반 대화는 직접 LLM 응답

### API 사용 예시

```python
import requests

# 챗봇 대화
response = requests.post('http://localhost:8000/chat/', 
    json={'message': '회사 정책에 대해 알려주세요'})
print(response.json())

# 문서 업로드
response = requests.post('http://localhost:8000/documents/upload/',
    json={
        'title': '회사 정책',
        'content': '회사 정책 내용...'
    })
```

## 📁 프로젝트 구조

```
SKN-FINAL-Project/
├── chatbot.py                 # 메인 챗봇 로직
├── manage.py                  # Django 관리 스크립트
├── requirements.txt           # Python 패키지 목록
├── README.md                 # 프로젝트 문서
├── chatbot_project/          # Django 프로젝트 설정
│   ├── __init__.py
│   ├── settings.py           # Django 설정
│   ├── urls.py              # URL 라우팅
│   └── wsgi.py              # WSGI 설정
├── chat/                     # 챗봇 Django 앱
│   ├── __init__.py
│   ├── admin.py             # 관리자 페이지
│   ├── apps.py              # 앱 설정
│   ├── models.py            # 데이터베이스 모델
│   ├── views.py             # 뷰 로직
│   ├── urls.py              # URL 라우팅
│   └── serializers.py       # API 시리얼라이저
└── templates/               # HTML 템플릿
    ├── base.html            # 기본 템플릿
    └── chat/
        └── chatbot.html     # 챗봇 페이지
```

## 🔑 주요 구성 요소

### 1. 챗봇 엔진 (chatbot.py)
- **QdrantVectorStore**: 벡터 데이터베이스 관리
- **DocumentRetriever**: 문서 검색 엔진
- **QueryClassifier**: 질의 유형 분류기
- **RAGChatbot**: 메인 챗봇 클래스
- **ChatbotGraph**: LangGraph 워크플로우

### 2. Django 웹 애플리케이션
- **모델**: 채팅 세션, 메시지, 문서 관리
- **뷰**: API 엔드포인트 및 웹 페이지
- **템플릿**: 반응형 웹 UI

### 3. API 엔드포인트
- `POST /chat/` - 챗봇 대화
- `GET /sessions/` - 세션 목록
- `POST /sessions/create/` - 새 세션 생성
- `GET /sessions/{id}/` - 세션 상세 정보
- `DELETE /sessions/{id}/delete/` - 세션 삭제
- `POST /documents/upload/` - 문서 업로드
- `GET /health/` - 헬스 체크

## 🎯 핵심 기능 설명

### LangGraph 라우팅
```python
def classify_query_node(state):
    """사용자 질의를 분류하는 노드"""
    query_type = classifier.classify_query(state["user_query"])
    state["query_type"] = query_type
    state["needs_retrieval"] = query_type == "document"
    return state

def should_retrieve(state):
    """문서 검색 여부를 결정하는 조건부 라우팅"""
    return "retrieve" if state["needs_retrieval"] else "generate"
```

### RAG 프로세스
1. **문서 수집**: 사용자가 업로드한 문서들
2. **임베딩 생성**: Sentence Transformers로 벡터화
3. **벡터 저장**: Qdrant 데이터베이스에 저장
4. **유사도 검색**: 사용자 질의와 유사한 문서 검색
5. **컨텍스트 생성**: 검색된 문서를 LLM 프롬프트에 포함
6. **답변 생성**: OpenAI GPT 모델로 최종 답변 생성

## 🔧 커스터마이징

### 1. LLM 모델 변경
```python
# chatbot.py에서 LLM 모델 설정 변경
self.llm = OpenAI(
    model_name="gpt-4",  # 또는 다른 모델
    api_key=OPENAI_API_KEY,
    temperature=self.config.temperature
)
```

### 2. 임베딩 모델 변경
```python
# 다른 임베딩 모델 사용
self.embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

### 3. 벡터 데이터베이스 변경
- Qdrant 대신 Pinecone, Weaviate, Chroma 등 사용 가능
- `QdrantVectorStore` 클래스 수정

## 📊 모니터링 및 로깅

- Django 로깅 시스템 활용
- 채팅 세션 및 메시지 데이터베이스 저장
- 응답 시간 및 성능 메트릭 수집
- 관리자 페이지에서 실시간 모니터링

## 🚨 문제 해결

### 1. Qdrant 연결 오류
```bash
# Qdrant 서버 상태 확인
curl http://localhost:6333/collections

# Docker 컨테이너 재시작
docker restart <qdrant-container-id>
```

### 2. OpenAI API 오류
- API 키 확인
- 사용량 제한 확인
- 모델 가용성 확인

### 3. 메모리 부족
- 임베딩 모델 크기 조정
- 배치 크기 줄이기
- 문서 청크 크기 조정

## 📈 성능 최적화

1. **벡터 검색 최적화**: Qdrant 인덱스 튜닝
2. **캐싱**: Redis 캐시 도입
3. **비동기 처리**: 대용량 문서 처리 시 Celery 사용
4. **모델 최적화**: 더 빠른 임베딩 모델 사용

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원 및 문의

프로젝트 관련 문의사항이 있으시면 Issue를 등록해주세요.

---

**🎉 프로젝트 완성! 이제 AI 챗봇 시스템을 사용해보세요!** 