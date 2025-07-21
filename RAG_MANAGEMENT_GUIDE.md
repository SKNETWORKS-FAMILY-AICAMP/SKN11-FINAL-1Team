# RAG 에이전트 관리 가이드

## 📁 파일 구조 및 역할

### 현재 구조
```
django_prj/onboarding_quest/
├── rag_agent_graph_db_v3_finaltemp_v2.py  # 메인 RAG 에이전트 파일
├── loaders.py                              # 문서 로더
├── embed_and_upsert.py                     # 임베딩 및 벡터 DB 업로드
└── batch_insert.py                         # 배치 데이터 처리
```

### 권장 구조 (리팩토링)
```
django_prj/onboarding_quest/
├── rag_system/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py              # 메인 LangGraph 에이전트
│   │   ├── database.py           # 데이터베이스 연결 관리
│   │   ├── models.py             # Pydantic 모델들
│   │   └── config.py             # RAG 시스템 설정
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── search.py             # 문서 검색 노드
│   │   ├── generation.py         # 답변 생성 노드
│   │   ├── evaluation.py         # 품질 평가 노드
│   │   └── rewrite.py            # 질문 재작성 노드
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── loaders.py            # 문서 로더들
│   │   ├── embeddings.py         # 임베딩 처리
│   │   └── quality_metrics.py    # 품질 메트릭
│   └── services/
│       ├── __init__.py
│       ├── qdrant_service.py     # Qdrant 연동
│       └── session_service.py    # 세션 관리
└── rag_agent_graph_db_v3_finaltemp_v2.py  # 호환성을 위한 레거시 파일
```

## 🔧 리팩토링 단계

### 1단계: 디렉토리 구조 생성
```bash
cd django_prj/onboarding_quest/
mkdir -p rag_system/{core,nodes,utils,services}
touch rag_system/__init__.py
touch rag_system/{core,nodes,utils,services}/__init__.py
```

### 2단계: 모듈 분리

#### rag_system/core/config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class RAGConfig:
    # API 키
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Qdrant 설정
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_multiformat")
    
    # PostgreSQL 설정
    DB_CONFIG = {
        'host': os.getenv("DB_HOST", "localhost"),
        'port': os.getenv("DB_PORT", "5432"),
        'database': os.getenv("DB_NAME", "onboarding_quest_db"),
        'user': os.getenv("DB_USER", "postgres"),
        'password': os.getenv("DB_PASSWORD", "")
    }
    
    # LLM 설정
    LLM_MODEL = "gpt-4o-mini"
    WINDOW_SIZE = 10
```

#### rag_system/core/database.py
```python
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from .config import RAGConfig
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """PostgreSQL 연결 관리"""
    conn = None
    try:
        conn = psycopg2.connect(**RAGConfig.DB_CONFIG, cursor_factory=RealDictCursor)
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise e
    finally:
        if conn:
            conn.close()
```

#### rag_system/core/models.py
```python
from typing import TypedDict, List, Optional

class AgentState(TypedDict, total=False):
    question: str
    contexts: List[str]
    answer: str
    reflection: str
    rewritten_question: str
    chat_history: List[str]
    rewrite_count: int
    session_id: str
    summary: str
    evaluation_score: int
    needs_rewrite: bool
    evaluation_details: str
    question_type: str
    user_department_id: int
```

### 3단계: 서비스 레이어 분리

#### rag_system/services/session_service.py
```python
from datetime import datetime
from ..core.database import get_db_connection

class SessionService:
    @staticmethod
    def create_chat_session(user_id: str) -> str:
        """채팅 세션 생성"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO core_chatsession (user_id, summary) VALUES (%s, %s) RETURNING session_id",
                (int(user_id), "새 채팅 세션")
            )
            session_id = cursor.fetchone()['session_id']
        return str(session_id)
    
    @staticmethod
    def save_message(session_id: str, text: str, message_type: str):
        """메시지 저장"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO core_chatmessage (session_id, create_time, message_text, message_type, is_active) VALUES (%s, %s, %s, %s, %s)",
                (int(session_id), datetime.now(), text, message_type, True)
            )
```

### 4단계: 노드 분리

#### rag_system/nodes/search.py
```python
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from ..core.config import RAGConfig
from ..core.models import AgentState

class SearchNode:
    def __init__(self):
        self.client = QdrantClient(url=RAGConfig.QDRANT_URL)
        self.embeddings = OpenAIEmbeddings(openai_api_key=RAGConfig.OPENAI_API_KEY)
    
    def search_documents_filtered(self, state: AgentState) -> AgentState:
        """부서별 필터링 검색"""
        # 기존 search_documents_filtered 로직
        pass
```

## 🚀 마이그레이션 전략

### 1. 점진적 마이그레이션
1. 현재 파일 백업
2. 새 구조로 단계별 이주
3. 테스트 후 레거시 제거

### 2. 호환성 유지
```python
# rag_agent_graph_db_v3_finaltemp_v2.py (호환성 래퍼)
from rag_system.core.agent import graph
from rag_system.services.session_service import SessionService

# 기존 함수들을 새 서비스로 연결
create_chat_session = SessionService.create_chat_session
save_message = SessionService.save_message

# 그래프는 그대로 export
__all__ = ['graph', 'create_chat_session', 'save_message']
```

## 📊 모니터링 및 성능 최적화

### 1. 로깅 강화
```python
import logging
import time
from functools import wraps

def log_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} 실행 시간: {end_time - start_time:.2f}초")
        return result
    return wrapper
```

### 2. 메트릭 수집
```python
class RAGMetrics:
    def __init__(self):
        self.response_times = []
        self.quality_scores = []
        self.rag_usage_rate = 0
    
    def record_response_time(self, time_taken):
        self.response_times.append(time_taken)
    
    def record_quality_score(self, score):
        self.quality_scores.append(score)
```

## 🔒 보안 고려사항

### 1. 데이터베이스 보안
- 연결 풀링 구현
- SQL 인젝션 방지
- 민감 정보 암호화

### 2. API 보안
- 요청 제한 (Rate Limiting)
- 입력 검증 강화
- 로그 마스킹

## 🧪 테스트 전략

### 1. 유닛 테스트
```python
# tests/test_search_node.py
import pytest
from rag_system.nodes.search import SearchNode

class TestSearchNode:
    def test_search_documents_filtered(self):
        # 테스트 케이스 구현
        pass
```

### 2. 통합 테스트
```python
# tests/test_integration.py
from rag_system.core.agent import graph

def test_full_rag_pipeline():
    """전체 RAG 파이프라인 테스트"""
    initial_state = {
        "question": "테스트 질문",
        "session_id": "test_session",
        "user_department_id": 1
    }
    result = graph.invoke(initial_state)
    assert "answer" in result
```

## 🔄 배포 및 운영

### 1. 환경별 설정
```python
# rag_system/core/config.py
class Config:
    def __init__(self, env='development'):
        if env == 'production':
            self.LLM_MODEL = "gpt-4"
        else:
            self.LLM_MODEL = "gpt-4o-mini"
```

### 2. 헬스 체크
```python
async def health_check():
    """RAG 시스템 상태 체크"""
    checks = {
        'database': check_database_connection(),
        'qdrant': check_qdrant_connection(),
        'openai': check_openai_api()
    }
    return all(checks.values())
```

이 가이드를 따라 점진적으로 리팩토링하면 더 유지보수가 쉽고 확장 가능한 RAG 시스템을 구축할 수 있습니다.
