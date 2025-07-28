# 필수 라이브러리
import os
import uuid
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import re
import numpy as np
from datetime import datetime
from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_core.messages import SystemMessage, HumanMessage
import threading
from contextlib import contextmanager
from qdrant_client.http.models import Filter, FieldCondition, MatchValue 
from qdrant_client.models import MatchText

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 로딩
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 상단에 추가
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_multiformat")

# PostgreSQL DB 연결 설정
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': os.getenv("DB_PORT", "5432"),
    'database': os.getenv("DB_NAME", "onboarding_quest_db"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "")
}

@contextmanager
def get_db_connection():
    """안전한 PostgreSQL 연결 관리"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
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

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# LangChain 구성
client = QdrantClient(url=QDRANT_URL)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-large")
# llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-4o-mini")
llm_fast = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo")
llm_smart = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-4o-mini")


WINDOW_SIZE = 10

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
    user_department_id: int  # 부서 ID 추가
    doc_filter: List[str]  # ✅ 이 줄 추가

# 품질 평가 관리 클래스
class QualityMetrics:
    def __init__(self):
        self.evaluation_history = []
        self.success_threshold = 14  # 20점 만점 중 14점 기준
    
    def update_threshold(self, evaluation_score: int, user_satisfaction: bool):
        """사용자 만족도 기반 임계값 동적 조정"""
        self.evaluation_history.append({
            'score': evaluation_score,
            'satisfied': user_satisfaction,
            'timestamp': datetime.now()
        })
        
        # 최근 50개 평가 기준으로 임계값 조정
        recent_evaluations = self.evaluation_history[-50:]
        
        if len(recent_evaluations) >= 10:
            # 만족도가 높은 답변들의 평균 점수 계산
            satisfied_scores = [e['score'] for e in recent_evaluations if e['satisfied']]
            if satisfied_scores:
                self.success_threshold = max(12, min(18, int(np.mean(satisfied_scores)) - 1))
    
    def should_rewrite(self, evaluation_score: int) -> bool:
        return evaluation_score < self.success_threshold

# 전역 품질 메트릭 인스턴스
quality_metrics = QualityMetrics()

# 세션 및 메시지 DB 함수 (PostgreSQL 버전)
def create_chat_session(user_id: str) -> str:
    """PostgreSQL을 사용하는 세션 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # PostgreSQL SERIAL 타입이므로 session_id 자동 생성
        cursor.execute(
            "INSERT INTO core_chatsession (user_id, summary) VALUES (%s, %s) RETURNING session_id",
            (int(user_id), "새 채팅 세션")
        )
        
        # 생성된 session_id 조회
        session_id = cursor.fetchone()['session_id']
        
    return str(session_id)


def save_message(session_id: str, text: str, message_type: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO core_chatmessage (session_id, create_time, message_text, message_type, is_active) VALUES (%s, %s, %s, %s, %s)",
            (int(session_id), datetime.now(), text, message_type, True)
        )


def load_session_history(session_id: str, limit: int = 10) -> List[str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_text, message_type
            FROM core_chatmessage
            WHERE session_id = %s
            ORDER BY create_time ASC
        """, (int(session_id),))
        
        messages = cursor.fetchall()

    history = []
    buffer = {}
    for row in messages:
        text, mtype = row['message_text'], row['message_type']
        if mtype == "user":
            buffer["user"] = text
        elif mtype in ["bot", "chatbot"]:
            buffer["bot"] = text
        if "user" in buffer and "bot" in buffer:
            history.append(f"Q: {buffer['user']}\nA: {buffer['bot']}")
            buffer = {}

    return history[-limit:]


# 질문 유형 분류 함수
def classify_question_type(question: str) -> str:
    """질문 유형을 분류하여 맞춤형 평가 기준 적용"""
    question_lower = question.lower()
    
    if any(keyword in question_lower for keyword in ['조항', '규정', '조례', '법률', '제', '조']):
        return "regulation"
    elif any(keyword in question_lower for keyword in ['절차', '방법', '어떻게', '신청', '처리']):
        return "procedure"
    elif any(keyword in question_lower for keyword in ['일정', '기간', '언제', '시간']):
        return "schedule"
    elif any(keyword in question_lower for keyword in ['담당자', '연락처', '부서', '누구']):
        return "contact"
    else:
        return "general"

# 개선된 답변 품질 평가 함수
def judge_answer_improved(state: AgentState) -> AgentState:
    start = time.time()
    logger.info("🟢 judge_answer_improved 시작")
    logger.info("📊 judge_answer_improved 실행")
    """구체적인 평가 기준으로 답변 품질을 평가"""
    context = "\n---\n".join(state.get("contexts", []))
    question = state['question']
    answer = state['answer']
    question_type = classify_question_type(question)
    
    # 질문 유형별 맞춤 평가 기준
    if question_type == "regulation":
        evaluation_criteria = """
        1. 완전성: 해당 조항 번호와 제목이 명시되었는가? (1-5점)
        2. 정확성: 조항의 구체적 내용이 정확히 인용되었는가? (1-5점)
        3. 구체성: 적용 범위나 예외사항이 설명되었는가? (1-5점)
        4. 관련성: 질문과 직접적으로 관련된 조항을 제시했는가? (1-5점)
        """
    elif question_type == "procedure":
        evaluation_criteria = """
        1. 완전성: 절차의 모든 단계가 순서대로 설명되었는가? (1-5점)
        2. 정확성: 필요한 서류나 조건이 구체적으로 명시되었는가? (1-5점)
        3. 구체성: 담당 부서나 연락처 정보가 포함되었는가? (1-5점)
        4. 관련성: 질문자의 상황에 맞는 절차를 제시했는가? (1-5점)
        """
    elif question_type == "schedule":
        evaluation_criteria = """
        1. 완전성: 정확한 일정이나 기간이 제시되었는가? (1-5점)
        2. 정확성: 제시된 일정이 현재 규정과 일치하는가? (1-5점)
        3. 구체성: 구체적인 날짜나 기간이 명시되었는가? (1-5점)
        4. 관련성: 질문과 관련된 일정 정보를 제공했는가? (1-5점)
        """
    else:
        evaluation_criteria = """
        1. 완전성: 질문의 모든 부분에 답변했는가? (1-5점)
        2. 정확성: 제공된 Context에 기반하여 정확한 답변인가? (1-5점)
        3. 구체성: 구체적인 정보와 예시가 포함되었는가? (1-5점)
        4. 관련성: 질문과 직접적으로 관련된 내용인가? (1-5점)
        """
    
    # 구체적인 평가 프롬프트
    evaluation_prompt = f"""
    다음 기준에 따라 답변의 품질을 평가하세요:
    
    **평가 기준 ({question_type} 유형):**
    {evaluation_criteria}
    
    **질문:** {question}
    
    **Context:** {context}
    
    **답변:** {answer}
    
    **평가 결과를 다음 형식으로 제출하세요:**
    완전성: X점 (이유: ...)
    정확성: X점 (이유: ...)
    구체성: X점 (이유: ...)
    관련성: X점 (이유: ...)
    총점: X점 (20점 만점)
    최종판단: [충분|부족]
    개선방향: (부족한 경우만) ...
    """
    
    # reflection = llm.invoke(evaluation_prompt)
    reflection = llm_fast.invoke(evaluation_prompt)
    
    # 점수 추출
    score_match = re.search(r'총점:\s*(\d+)', reflection.content)
    evaluation_score = int(score_match.group(1)) if score_match else 10
    
    # 개선 방향 추출
    improvement_match = re.search(r'개선방향:\s*(.+)', reflection.content)
    improvement_direction = improvement_match.group(1) if improvement_match else "더 구체적인 정보가 필요합니다."
    
    # 재작성 필요 여부 판단
    needs_rewrite = quality_metrics.should_rewrite(evaluation_score)
    elapsed = time.time() - start
    logger.info(f"🟢 judge_answer_improved 완료 - ⏱️ {elapsed:.2f}초")
    
    return {
        **state, 
        "reflection": reflection.content,
        "evaluation_score": evaluation_score,
        "needs_rewrite": needs_rewrite,
        "evaluation_details": improvement_direction,
        "question_type": question_type
    }

# 개선된 질문 재작성 함수
def reformulate_question_improved(state: AgentState) -> AgentState:
    start = time.time()
    logger.info("🟢 reformulate_question_improved 시작")
    logger.info("✏️ reformulate_question_improved 실행")
    """평가 결과를 바탕으로 질문을 개선하여 재작성"""
    question = state.get('question')
    contexts = state.get('contexts', [])
    improvement_direction = state.get('evaluation_details', '더 구체적인 정보가 필요합니다.')
    question_type = state.get('question_type', 'general')
    
    # 사용 가능한 Context 키워드 추출
    context_keywords = []
    for context in contexts:
        if '[' in context and ']' in context:
            keyword = context.split('[')[1].split(']')[0]
            context_keywords.append(keyword)
    
    # 질문 유형별 재작성 가이드
    if question_type == "regulation":
        rewrite_guide = """
        1. 구체적인 조항 번호나 제목 언급
        2. 해당 규정의 적용 범위 확인 요청
        3. 예외사항이나 특수 조건 포함
        4. 관련 하위 조항이나 시행령 확인
        """
    elif question_type == "procedure":
        rewrite_guide = """
        1. 단계별 절차의 구체적 순서 요청
        2. 필요한 서류나 준비물 명시 요구
        3. 담당 부서나 연락처 정보 포함
        4. 처리 기간이나 소요 시간 확인
        """
    else:
        rewrite_guide = """
        1. 더 구체적인 세부사항 요청
        2. 실무적 적용 방법 포함
        3. 예외 상황이나 추가 고려사항 확인
        4. 관련 문서나 참고 자료 요청
        """
    
    reformulate_prompt = f"""
    기존 질문을 다음 개선 방향에 따라 재작성하세요:
    
    **기존 질문:** {question}
    
    **개선 방향:** {improvement_direction}
    
    **질문 유형:** {question_type}
    
    **재작성 가이드:**
    {rewrite_guide}
    
    **사용 가능한 Context 키워드:**
    {', '.join(context_keywords)}
    
    **재작성 원칙:**
    - 기존 질문의 핵심 의도는 유지하면서 더 구체적으로 작성
    - 평가에서 부족했던 부분을 보완할 수 있는 방향으로 재작성
    - 사용 가능한 Context의 키워드를 활용하여 정확한 답변을 유도
    
    **재작성된 질문:**
    """
    
    new_question = llm_fast.invoke(reformulate_prompt).content.strip()
    elapsed = time.time() - start
    logger.info(f"🟢 reformulate_question_improved 완료 - ⏱️ {elapsed:.2f}초")
    
    return {
        **state, 
        "rewritten_question": new_question, 
        "rewrite_count": state.get("rewrite_count", 0) + 1
    }

# # 개선된 판단 함수
# def decide_to_reflect_improved(state: AgentState) -> str:
#     """점수 기반으로 재작성 여부 결정"""
#     if state.get("rewrite_count", 0) >= 2:
#         return "summarize"
    
#     # 평가 점수 기반 판단
#     if state.get("needs_rewrite", False):
#         return "rewrite"
#     else:
#         return "summarize"

def decide_to_reflect_improved(state: AgentState) -> str:
    start = time.time()
    logger.info("🟢 decide_to_reflect_improved 시작")
    logger.info(f"🧭 decide_to_reflect_improved 실행 - score={state.get('evaluation_score')}, count={state.get('rewrite_count')}")
    if state.get("evaluation_score", 20) >= 14:
        return "summarize"  # 점수 높으면 바로 종료
    if state.get("rewrite_count", 0) >= 1:
        return "summarize"  # 이미 한 번 재작성 했으면 그만
    elapsed = time.time() - start
    logger.info(f"🟢 decide_to_reflect_improved 완료 - ⏱️ {elapsed:.2f}초")
    return "rewrite"  # 그 외에만 재작성


def search_documents_with_rerank(state: AgentState) -> AgentState:
    import re
    import collections
    start = time.time()
    logger.info("● search_documents_with_rerank 시작")

    query = state.get("rewritten_question") or state["question"]
    user_department_id = state.get("user_department_id")
    query_vec = embeddings.embed_query(query)

    doc_filter = state.get("doc_filter")

    # ✅ 조건에 따라 컬렉션 + 필터 설정
    combined_results = []

    # ✅ 항상 부서 + 공통 컬렉션 순회 (필터 여부는 내부에서 분기)
    collections_to_search = []
    if user_department_id:
        collections_to_search.append(f"rag_{user_department_id}")
    collections_to_search.append("rag_common")

    # 컬렉션 대상 결정
    collections_to_search = []

    if doc_filter:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT original_file_name, department_id, common_doc
                FROM core_docs
                WHERE original_file_name = ANY(%s)
                """,
                (doc_filter,)
            )
            for row in cursor.fetchall():
                if row["common_doc"]:
                    collections_to_search.append("rag_common")
                elif row["department_id"] is not None:
                    collections_to_search.append(f"rag_{row['department_id']}")
    else:
        if user_department_id:
            collections_to_search.append(f"rag_{user_department_id}")
        collections_to_search.append("rag_common")

    collections_to_search = list(set(collections_to_search))  # 중복 제거

    # Qdrant 검색
    combined_results = []

    for col in collections_to_search:
        try:
            if doc_filter:
                logger.info(f"📎 필터 대상 파일명 목록: {doc_filter}")
                logger.info(f"📎 컬렉션: {col}")
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="metadata.original_file_name",
                            # match=MatchValue(value=filename)
                            match=MatchText(text=filename)  # 변경
                        ) for filename in doc_filter
                    ]
                )
            else:
                query_filter = None

            logger.info(f"📁 검색: {col} | 필터: {doc_filter}")
            result = client.search(
                collection_name=col,
                query_vector=query_vec,
                query_filter=query_filter,
                limit=10,
                with_payload=True
            )
            for r in result:
                logger.info(f"📌 검색된 청크: {r.payload.get('metadata', {}).get('original_file_name')} / "
                            f"{r.payload.get('metadata', {}).get('hierarchy_path')}")
            combined_results.extend(result)

        except Exception as e:
            logger.warning(f"⚠️ Qdrant 검색 실패 - 컬렉션: {col} | 이유: {e}")


            logger.info(f"📁 정확 검색 - 컬렉션: {col} | 필터: {doc_filter}")
            result = client.search(
                collection_name=col,
                query_vector=query_vec,
                query_filter=query_filter,
                limit=10,
                with_payload=True
            )
            combined_results.extend(result)

        except Exception as e:
            logger.warning(f"⚠️ 컬렉션 '{col}' 검색 중 오류: {e}")




    # if not combined_results:
    #     return {**state, "contexts": []}
        if not combined_results:
            return {**state, "contexts": []}

        # response = llm_smart.invoke(doc_prompt).content.strip()
        # logger.warning(f"📤 GPT rerank 응답: {response}")

        # selected_idxs = [int(x.strip()) for x in re.findall(r'\d+', response)]
        # valid_idxs = [i for i in selected_idxs if 1 <= i <= len(document_candidates)]

        # if not valid_idxs:
        #     logger.warning(f"⚠️ GPT rerank가 문서 선택 안 함 → selected_idxs = {selected_idxs}")
        #     logger.warning(f"📉 검색된 문서 수: {len(document_candidates)} / 검색된 청크 수: {len(combined_results)}")
        #     fallback_contexts = []
        #     combined_top = sorted(combined_results, key=lambda x: x.score, reverse=True)[:3]
        #     for r in combined_top:
        #         meta = r.payload.get("metadata", {})
        #         title = meta.get("title", "무제")
        #         text = r.payload.get("text", "")
        #         file_name = meta.get("original_file_name", "unknown")
        #         hierarchy_path = meta.get("hierarchy_path")
        #         if hierarchy_path:
        #             fallback_contexts.append(f"[{hierarchy_path} | {title}] (출처: {file_name})\n{text}")
        #         else:
        #             fallback_contexts.append(f"[{title}] (출처: {file_name})\n{text}")
        #     return {**state, "contexts": fallback_contexts}

        # contexts = []
        # for idx in valid_idxs:
        #     chunk = document_candidates[idx - 1]
        #     meta = chunk["metadata"]
        #     title = meta.get("title", "무제")
        #     text = chunk["text"]
        #     file_name = meta.get("original_file_name", "unknown")
        #     hierarchy_path = meta.get("hierarchy_path")
        #     if hierarchy_path:
        #         contexts.append(f"[{hierarchy_path} | {title}] (출처: {file_name})\n{text}")
        #     else:
        #         contexts.append(f"[{title}] (출처: {file_name})\n{text}")

        # return {**state, "contexts": contexts}



    # 환경 설정: 문서 별 무료
    docs_map = collections.defaultdict(list)
    for r in combined_results:
        file_name = r.payload.get("metadata", {}).get("original_file_name") or r.payload.get("metadata", {}).get("file_name") or "unknown"
        docs_map[file_name].append(r)

    # 문서 단위로 representative chunk를 2~3개로 발체
    document_candidates = []
    for i, (file_name, results) in enumerate(docs_map.items(), 1):
        chunks_text = ""
        for j, r in enumerate(results[:3], 1):
            meta = r.payload.get("metadata", {})
            title = meta.get("title", f"chunk {j}")
            chunk = r.payload.get("text", "")
            hierarchy_path = meta.get("hierarchy_path")
            if hierarchy_path:
                chunks_text += f"- {hierarchy_path} | {title}: {chunk[:200]}...\n"
            else:
                chunks_text += f"- {title}: {chunk[:200]}...\n"
        document_candidates.append((i, file_name, chunks_text.strip(), results))

    doc_prompt = f"""
    아래는 사용자의 질문에 관련될 수 있는 여러 문서입니다.
    각 문서는 대표 청크 일부를 요약한 것이며, 관련된 문서를 고르세요.

    질문:
    {query}

    문서 후보:
    """
    for idx, file_name, chunks, _ in document_candidates:
        doc_prompt += f"\n문서 {idx} ({file_name}):\n{chunks}\n"

    doc_prompt += """
    가장 관련 있는 문서 번호를 1개 또는 2개 선택하세요.
    문서 번호만 쉼표로 구분해 출력하세요. (예: 1 또는 1,2)
    다른 텍스트는 출력하지 마세요.
    """

    response = llm_smart.invoke(doc_prompt).content.strip()
    logger.warning(f"📤 GPT rerank 응답: {response}")

    selected_idxs = [int(x.strip()) for x in re.findall(r'\d+', response)]
    valid_idxs = [i for i in selected_idxs if 1 <= i <= len(document_candidates)]

    if not valid_idxs:
        logger.warning(f"⚠️ GPT rerank가 문서 선택 안 함 → selected_idxs = {selected_idxs}")
        logger.warning(f"📉 검색된 문서 수: {len(document_candidates)} / 검색된 청크 수: {len(combined_results)}")
        # return {**state, "contexts": []}  # fallback 제거
        return {
            **state,
            "contexts": ["[안내] 선택한 문서에서 관련 정보를 찾지 못했습니다."]
        }


    # if not valid_idxs:
    #     logger.warning(f"⚠️ GPT rerank가 문서 선택 안 함 → selected_idxs = {selected_idxs}")
    #     logger.warning(f"📉 검색된 문서 수: {len(document_candidates)} / 검색된 청크 수: {len(combined_results)}")
    #     fallback_contexts = []
    #     combined_top = sorted(combined_results, key=lambda x: x.score, reverse=True)[:3]
    #     for r in combined_top:
    #         meta = r.payload.get("metadata", {})
    #         title = meta.get("title", "무제")
    #         text = r.payload.get("text", "")
    #         file_name = meta.get("original_file_name", "unknown")
    #         hierarchy_path = meta.get("hierarchy_path")
    #         if hierarchy_path:
    #             fallback_contexts.append(f"[{hierarchy_path} | {title}] (출처: {file_name})\n{text}")
    #         else:
    #             fallback_contexts.append(f"[{title}] (출처: {file_name})\n{text}")
    #     return {**state, "contexts": fallback_contexts}

    contexts = []
    for idx in valid_idxs:
        _, file_name, _, results = document_candidates[idx - 1]
        for r in results[:3]:
            meta = r.payload.get("metadata", {})
            title = meta.get("title", "무제")
            text = r.payload.get("text", "")
            hierarchy_path = meta.get("hierarchy_path")
            if hierarchy_path:
                last_level = hierarchy_path.split('>')[-1].strip()
                if last_level == title:
                    contexts.append(f"[{hierarchy_path}] (출처: {file_name})\n{text}")
                else:
                    contexts.append(f"[{hierarchy_path} | {title}] (출처: {file_name})\n{text}")
            else:
                contexts.append(f"[{title}] (출처: {file_name})\n{text}")

    elapsed = time.time() - start
    logger.info(f"● search_documents_with_rerank 완료 - ⏱ {elapsed:.2f}초")
    return {**state, "contexts": contexts}

    # response = llm_smart.invoke(doc_prompt).content.strip()
    # selected_idxs = [int(x.strip()) for x in re.findall(r'\d+', response)]

    # logger.warning(f"⚠️ GPT rerank가 문서 선택 안 함 → selected_idxs = {selected_idxs}")
    # logger.warning(f"📉 검색된 문서 수: {len(document_candidates)} / 검색된 청크 수: {len(combined_results)}")

    # contexts = []
    # for idx in selected_idxs:
    #     if 1 <= idx <= len(document_candidates):
    #         _, file_name, _, results = document_candidates[idx - 1]
    #         for r in results[:3]:
    #             meta = r.payload.get("metadata", {})
    #             title = meta.get("title", "무제")
    #             text = r.payload.get("text", "")
    #             hierarchy_path = meta.get("hierarchy_path")
    #             if hierarchy_path:
    #                 last_level = hierarchy_path.split('>')[-1].strip()
    #                 if last_level == title:
    #                     contexts.append(f"[{hierarchy_path}] (출처: {file_name})\n{text}")
    #                 else:
    #                     contexts.append(f"[{hierarchy_path} | {title}] (출처: {file_name})\n{text}")
    #             else:
    #                 contexts.append(f"[{title}] (출처: {file_name})\n{text}")

    # elapsed = time.time() - start
    # logger.info(f"\u25cf search_documents_with_rerank 완료 - \u231a {elapsed:.2f}초")
    # return {**state, "contexts": contexts}



# def search_documents_with_rerank(state: AgentState) -> AgentState:
#     start = time.time()
#     logger.info("🟢 search_documents_with_rerank 시작")
#     query = state.get("rewritten_question") or state["question"]
#     user_department_id = state.get("user_department_id")

#     query_vec = embeddings.embed_query(query)

#     collections_to_search = []
#     if user_department_id:
#         collections_to_search.append(f"rag_{user_department_id}")
#     collections_to_search.append("rag_common")

#     combined_results = []

#     for col in collections_to_search:
#         try:
#             logger.info(f"📁 컬렉션 검색: {col}")
#             result = client.search(
#                 collection_name=col,
#                 query_vector=query_vec,
#                 query_filter=None,  # 컬렉션 별로 나뉘므로 필터 불필요
#                 limit=10,
#                 with_payload=True
#             )
#             combined_results.extend(result)
#         except Exception as e:
#             logger.warning(f"⚠️ 컬렉션 '{col}' 검색 실패: {e}")

#     if not combined_results:
#         return {**state, "contexts": []}

#     # GPT rerank 프롬프트 구성
#     prompt_chunks = ""
#     for i, r in enumerate(combined_results, 1):
#         meta = r.payload.get("metadata", {})
#         title = meta.get("title", f"청크 {i}")
#         chunk = r.payload.get("text", "")
#         hierarchy_path = meta.get("hierarchy_path")
#         if hierarchy_path:
#             prompt_chunks += f"\n청크 {i} ({hierarchy_path} | {title}):\n{chunk}\n"
#         else:
#             prompt_chunks += f"\n청크 {i} ({title}):\n{chunk}\n"

#     rerank_prompt = f"""
# 다음 질문과 가장 관련 있는 청크를 3개 이내로 선택해 주세요.

# 질문:
# {query}

# 후보 청크:
# {prompt_chunks}

# 선택한 청크의 번호를 쉼표로 구분해서 출력하세요 (예: 1,3,5).
# 다른 설명은 하지 마세요.
# """

#     response = llm_fast.invoke(rerank_prompt).content.strip()
#     selected_nums = [int(x.strip()) for x in re.findall(r'\d+', response)]

#     contexts = []
#     for idx in selected_nums:
#         if 1 <= idx <= len(combined_results):
#             r = combined_results[idx - 1]
#             meta = r.payload.get("metadata", {})
#             title = meta.get("title", "무제")
#             text = r.payload.get("text", "")
#             file_name = meta.get("original_file_name") or meta.get("file_name", "알 수 없음")
#             hierarchy_path = meta.get("hierarchy_path")
#             if hierarchy_path:
#                 last_level = hierarchy_path.split('>')[-1].strip()
#                 if last_level == title:
#                     contexts.append(f"[{hierarchy_path}] (출처: {file_name})\n{text}")
#                 else:
#                     contexts.append(f"[{hierarchy_path} | {title}] (출처: {file_name})\n{text}")
#             else:
#                 contexts.append(f"[{title}] (출처: {file_name})\n{text}")

#     elapsed = time.time() - start
#     logger.info(f"🟢 search_documents_with_rerank 완료 - ⏱️ {elapsed:.2f}초")

#     return {**state, "contexts": contexts}



# 세션 요약 함수 (PostgreSQL 버전)
def summarize_session(state: AgentState) -> AgentState:
    start = time.time()
    logger.info("🟢 summarize_session 시작")
    logger.info("📝 summarize_session 실행")
    """단일 연결에서 모든 작업 처리"""
    session_id = state.get("session_id")
    if not session_id:
        return state
    
    # 하나의 연결에서 모든 작업 처리
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 메시지 조회
        cursor.execute("""
            SELECT message_text, message_type
            FROM core_chatmessage
            WHERE session_id = %s
            ORDER BY create_time ASC
        """, (session_id,))
        
        messages = cursor.fetchall()
        
        # 히스토리 처리
        history = []
        buffer = {}
        for row in messages:
            text, mtype = row['message_text'], row['message_type']
            if mtype == "user":
                buffer["user"] = text
            elif mtype == "bot":
                buffer["bot"] = text
            if "user" in buffer and "bot" in buffer:
                history.append(f"Q: {buffer['user']}\nA: {buffer['bot']}")
                buffer = {}
        
        combined = "\n".join(history[-10:])
        
        # LLM으로 요약 생성
        messages_for_llm = [
            SystemMessage(content="당신은 기업 내부 상담용 챗봇입니다. 다음 대화 내용은 한 사용자의 상담 기록입니다. 핵심 질문과 답변이 무엇이었는지 중심으로 20글자 내로 요약해 주세요."),
            HumanMessage(content=f"대화 내용:\n{combined}\n\n요약:")
        ]
        
        summary = llm_fast.invoke(messages_for_llm).content.strip()
        
        # 같은 연결에서 요약 업데이트
        cursor.execute(
            "UPDATE core_chatsession SET summary = %s WHERE session_id = %s",
            (summary, session_id)
        )
    elapsed = time.time() - start
    logger.info(f"🟢 summarize_session 완료 - ⏱️ {elapsed:.2f}초")
    return {**state, "summary": summary}

# 기존 함수들 (필터링으로 변경)
def decide_use_rag(state: AgentState) -> AgentState:
    return state


def get_use_rag_condition(state: AgentState) -> str:
    question = state["question"]
    start = time.time()
    logger.info("🟢 get_use_rag_condition 시작")
    logger.info("🔥 get_use_rag_condition() 함수 호출됨!")

    prompt = f"""
너는 사용자의 질문이 '회사 내부 문서 검색이 필요한 질문'인지 판단하는 심사관이야.

다음의 기준에 따라 판단해:
- 회사 정책, 규정, 메뉴얼, 제출 기한, 휴가 제도, 신청 절차, 업무 처리 방식 등과 관련된 질문이면 "use_rag"
- 일반적인 잡담, 일상 대화, 개인적인 감정 또는 널리 알려진 상식 기반 질문이면 "skip_rag"

질문: "{question}"

반드시 딱 하나의 단어만 출력해: "use_rag" 또는 "skip_rag".
다른 말은 절대 하지 마.
"""

    result = llm_fast.invoke(prompt).content.strip().lower()
    # ✅ 로그 찍기
    logger.info(f"[RAG 판단] 질문: {question}")
    logger.info(f"[RAG 판단] LLM 응답: {result}")
    logger.info(f"[RAG 판단] 결과: {'✅ use_rag' if 'use_rag' in result else '❌ skip_rag'}")
    elapsed = time.time() - start
    logger.info(f"🟢 get_use_rag_condition 완료 - ⏱️ {elapsed:.2f}초")
    return "use_rag" if "use_rag" in result else "skip_rag"



def generate_answer(state: AgentState) -> AgentState:
    start = time.time()
    logger.info("🟢 generate_answer 시작")
    logger.info("💬 generate_answer 실행")
    context = "\n---\n".join(state.get("contexts", []))
    question = state.get("rewritten_question") or state["question"]
    full_history = state.get("chat_history", [])
    recent_history = full_history[-WINDOW_SIZE:]
    history_text = "\n".join(recent_history)
    
    # 출처 정보: 파일명별로 (hierarchy_path, title) 튜플을 set으로 집계 (완전 중복 제거)
    ref_map = {}  # {file_name: set((hierarchy_path, title))}
    for c in state.get("contexts", []):
        if c.startswith("["):
            first_line = c.split("\n")[0]
            if "(출처: " in first_line:
                file_name = first_line.split("(출처: ")[-1].split(")")[0].strip()
                left = first_line.split("]")[0].strip("[")
                # hierarchy_path와 title 분리
                if "|" in left:
                    hierarchy_path, title = left.split("|", 1)
                    hierarchy_path = hierarchy_path.strip()
                    title = title.strip()
                else:
                    hierarchy_path = ""
                    title = left.strip()
                ref_map.setdefault(file_name, set()).add((hierarchy_path, title))

    # 답변 프롬프트(출처 정보 없음)
    prompt = f"""
지금까지의 대화 기록:
{history_text}

아래 질문에 대해 context에 충실하게, 정확하고 자연스럽게 답변하세요.

💡 규칙:

Context:
{context}

질문: {question}

정확하고 친절한 답변:
"""

    # response = llm_smart.invoke(prompt)
    response = llm_smart.invoke(prompt)
    answer_text = response.content.strip()

    # 참고 문서 표시 추가 (파일명별로 계층+제목 리스트, 완전 중복 제거)
    if ref_map:
        ref_lines = []
        for file_name, hier_set in ref_map.items():
            ref_lines.append(f"📄 참고 문서: {file_name}")
            for hierarchy_path, title in sorted(hier_set, key=lambda x: (x[0], x[1])):
                # hierarchy_path의 마지막 계층이 title과 같으면 title만 표기
                if hierarchy_path:
                    # 마지막 계층 추출 (맨 뒤 > 기준으로 분리, 없으면 전체)
                    last_level = hierarchy_path.split('>')[-1].strip()
                    if last_level == title:
                        ref_lines.append(f" - {title}")
                    else:
                        ref_lines.append(f" - {hierarchy_path} | {title}")
                else:
                    ref_lines.append(f" - {title}")
        answer_text += "\n\n" + "\n".join(ref_lines)

    updated_history = full_history + [f"Q: {question}\nA: {answer_text}"]
    elapsed = time.time() - start
    logger.info(f"🟢 generate_answer 완료 - ⏱️ {elapsed:.2f}초")

    return {**state, "answer": answer_text, "chat_history": updated_history}




def direct_answer(state: AgentState) -> AgentState:
    question = state["question"]
    history_text = "\n".join(state.get("chat_history", [])[-WINDOW_SIZE:])
    
    prompt = f"""
지금까지의 대화 내용:
{history_text}

Question: {question}

Answer:"""
    
    response = llm_fast.invoke(prompt)
    updated_history = state.get("chat_history", []) + [f"Q: {question}\nA: {response.content}"]
    
    return {**state, "answer": response.content, "chat_history": updated_history}

# LangGraph 정의 (개선된 노드 사용)
builder = StateGraph(AgentState)
builder.add_node("decide", decide_use_rag)
builder.add_node("judge_rag", get_use_rag_condition)
# builder.add_node("search", search_documents_filtered)  # 필터링 검색으로 변경
builder.add_node("search", search_documents_with_rerank)

builder.add_node("answer", generate_answer)
builder.add_node("judge", judge_answer_improved)  # 개선된 함수 사용
builder.add_node("rewrite", reformulate_question_improved)  # 개선된 함수 사용
builder.add_node("direct_answer", direct_answer)
builder.add_node("summarize", summarize_session)

builder.set_entry_point("decide")

builder.add_conditional_edges("decide", get_use_rag_condition, {
    "use_rag": "search", "skip_rag": "direct_answer"
})

builder.add_edge("search", "answer")
builder.add_edge("answer", "judge")

builder.add_conditional_edges("judge", decide_to_reflect_improved, {  # 개선된 함수 사용
    "summarize": "summarize", "rewrite": "rewrite"
})

builder.add_edge("rewrite", "search")
builder.add_edge("direct_answer", "summarize")
builder.add_edge("summarize", END)

graph = builder.compile()

# 실행 진입점
def run_agent(user_id: str):
    session_id = create_chat_session(user_id)
    history = load_session_history(session_id=session_id, limit=10)

    state: AgentState = {
        "chat_history": history,
        "rewrite_count": 0,
        "session_id": session_id
    }

    while True:
        question = input("\n질문을 입력하세요: ")
        if question.lower() == "exit":
            print("\n✅ 세션 종료")
            break

        save_message(session_id, question, "user")

        state["question"] = question
        state["rewrite_count"] = 0
        state.pop("rewritten_question", None)

        final = graph.invoke(state)

        answer = final["answer"]
        evaluation_score = final.get("evaluation_score", 0)

        # ✅ RAG 사용 여부 판단
        used_rag = bool(final.get("contexts"))  # context가 비어있지 않으면 RAG 사용
        rag_tag = "🧾 [RAG 사용]" if used_rag else "💬 [RAG 미사용]"

        # ✅ 사용자에게 출력
        print(f"\n{rag_tag}")
        print(f"\n🧠 답변:\n{answer}")
        print(f"\n📊 평가 점수: {evaluation_score}/20")

        # ✅ 로그에도 저장
        save_message(session_id, f"{rag_tag}\n\n{answer}", "bot")

        # 상태 업데이트
        state["chat_history"] = final.get("chat_history", [])


# 테스트용
if __name__ == "__main__":
    run_agent(user_id="로그인된-유저-id")
