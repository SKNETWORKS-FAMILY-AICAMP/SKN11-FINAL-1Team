import os
import asyncio
from typing import List, Dict, Any, TypedDict
from dataclasses import dataclass

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.vectorstores import Qdrant as LangChainQdrant

# LangGraph imports
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Other imports
import json
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 설정 (실제 사용시 .env 파일에서 로드)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

class ChatState(TypedDict):
    """챗봇의 상태를 정의하는 클래스"""
    user_query: str
    chat_history: List[Dict[str, str]]
    retrieved_docs: List[Document]
    response: str
    query_type: str  # "document", "general", "greeting"
    needs_retrieval: bool

@dataclass
class ChatbotConfig:
    """챗봇 설정"""
    collection_name: str = "documents"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    temperature: float = 0.7

class QdrantVectorStore:
    """Qdrant 벡터 저장소 관리 클래스"""
    
    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Qdrant 컬렉션 초기화"""
        try:
            # 컬렉션 존재 확인
            collections = self.client.get_collections().collections
            collection_exists = any(
                collection.name == self.config.collection_name 
                for collection in collections
            )
            
            if not collection_exists:
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"컬렉션 '{self.config.collection_name}' 생성 완료")
            
            # LangChain Qdrant 벡터스토어 초기화
            self.vector_store = LangChainQdrant(
                client=self.client,
                collection_name=self.config.collection_name,
                embeddings=self.embeddings
            )
            
        except Exception as e:
            logger.error(f"Qdrant 초기화 오류: {e}")
            raise
    
    def add_documents(self, documents: List[Document]):
        """문서를 벡터 스토어에 추가"""
        try:
            if self.vector_store:
                self.vector_store.add_documents(documents)
                logger.info(f"{len(documents)}개 문서 추가 완료")
        except Exception as e:
            logger.error(f"문서 추가 오류: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """유사도 검색"""
        try:
            k = k or self.config.top_k
            if self.vector_store:
                return self.vector_store.similarity_search(query, k=k)
            return []
        except Exception as e:
            logger.error(f"검색 오류: {e}")
            return []

class DocumentRetriever:
    """문서 검색기"""
    
    def __init__(self, vector_store: QdrantVectorStore):
        self.vector_store = vector_store
    
    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """쿼리에 관련된 문서 검색"""
        return self.vector_store.similarity_search(query, k)
    
    def process_documents(self, documents: List[str]) -> List[Document]:
        """문서를 청크로 나누어 처리"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        all_docs = []
        for i, doc_text in enumerate(documents):
            chunks = text_splitter.split_text(doc_text)
            for j, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": f"document_{i}",
                        "chunk_id": j,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                all_docs.append(doc)
        
        return all_docs

class QueryClassifier:
    """사용자 쿼리 분류기"""
    
    @staticmethod
    def classify_query(query: str) -> str:
        """쿼리 유형을 분류"""
        query_lower = query.lower().strip()
        
        # 인사말 패턴
        greetings = ["안녕", "hello", "hi", "안녕하세요", "반가워", "처음 뵙겠습니다"]
        if any(greeting in query_lower for greeting in greetings):
            return "greeting"
        
        # 문서 관련 키워드
        document_keywords = [
            "문서", "자료", "정보", "내용", "설명", "어떻게", "무엇", "언제", "어디서",
            "document", "information", "explain", "how", "what", "when", "where"
        ]
        if any(keyword in query_lower for keyword in document_keywords):
            return "document"
        
        # 기본값은 일반 대화
        return "general"

class RAGChatbot:
    """RAG 기반 챗봇"""
    
    def __init__(self, config: ChatbotConfig = None):
        self.config = config or ChatbotConfig()
        self.vector_store = QdrantVectorStore(self.config)
        self.retriever = DocumentRetriever(self.vector_store)
        self.classifier = QueryClassifier()
        
        # OpenAI LLM 초기화
        self.llm = OpenAI(
            api_key=OPENAI_API_KEY,
            temperature=self.config.temperature
        )
        
        # 프롬프트 템플릿
        self.rag_prompt = PromptTemplate(
            template="""다음 문서들을 참고하여 사용자의 질문에 답변해주세요.

문서 내용:
{context}

사용자 질문: {question}

답변은 한국어로 작성하고, 문서의 내용을 기반으로 정확하고 도움이 되는 답변을 해주세요.
만약 문서에서 답을 찾을 수 없다면 그렇다고 말씀해주세요.

답변:""",
            input_variables=["context", "question"]
        )
        
        self.general_prompt = PromptTemplate(
            template="""사용자와 친근하게 대화해주세요.

사용자: {question}

답변은 한국어로 작성하고, 도움이 되고 친근한 톤으로 답변해주세요.

답변:""",
            input_variables=["question"]
        )
    
    def add_documents(self, documents: List[str]):
        """문서를 시스템에 추가"""
        processed_docs = self.retriever.process_documents(documents)
        self.vector_store.add_documents(processed_docs)
    
    def generate_response(self, state: ChatState) -> str:
        """응답 생성"""
        try:
            if state["query_type"] == "document" and state["retrieved_docs"]:
                # RAG 응답
                context = "\n\n".join([doc.page_content for doc in state["retrieved_docs"]])
                prompt = self.rag_prompt.format(
                    context=context,
                    question=state["user_query"]
                )
            else:
                # 일반 응답
                prompt = self.general_prompt.format(question=state["user_query"])
            
            response = self.llm(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"응답 생성 오류: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."

class ChatbotGraph:
    """LangGraph를 이용한 챗봇 워크플로우"""
    
    def __init__(self, chatbot: RAGChatbot):
        self.chatbot = chatbot
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """그래프 워크플로우 구성"""
        
        # 노드 함수들
        def classify_query_node(state: ChatState) -> ChatState:
            """쿼리 분류 노드"""
            query_type = self.chatbot.classifier.classify_query(state["user_query"])
            state["query_type"] = query_type
            state["needs_retrieval"] = query_type == "document"
            logger.info(f"쿼리 유형 분류: {query_type}")
            return state
        
        def retrieve_documents_node(state: ChatState) -> ChatState:
            """문서 검색 노드"""
            if state["needs_retrieval"]:
                docs = self.chatbot.retriever.retrieve(state["user_query"])
                state["retrieved_docs"] = docs
                logger.info(f"{len(docs)}개 문서 검색 완료")
            return state
        
        def generate_response_node(state: ChatState) -> ChatState:
            """응답 생성 노드"""
            response = self.chatbot.generate_response(state)
            state["response"] = response
            
            # 채팅 히스토리 업데이트
            state["chat_history"].append({
                "user": state["user_query"],
                "assistant": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return state
        
        # 조건부 라우팅
        def should_retrieve(state: ChatState) -> str:
            """문서 검색이 필요한지 결정"""
            return "retrieve" if state["needs_retrieval"] else "generate"
        
        # 그래프 구성
        workflow = StateGraph(ChatState)
        
        # 노드 추가
        workflow.add_node("classify", classify_query_node)
        workflow.add_node("retrieve", retrieve_documents_node)
        workflow.add_node("generate", generate_response_node)
        
        # 엣지 추가
        workflow.set_entry_point("classify")
        workflow.add_conditional_edges(
            "classify",
            should_retrieve,
            {
                "retrieve": "retrieve",
                "generate": "generate"
            }
        )
        workflow.add_edge("retrieve", "generate")
        workflow.set_finish_point("generate")
        
        return workflow.compile()
    
    async def chat(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """비동기 채팅 인터페이스"""
        initial_state = ChatState(
            user_query=user_query,
            chat_history=chat_history or [],
            retrieved_docs=[],
            response="",
            query_type="",
            needs_retrieval=False
        )
        
        try:
            # 그래프 실행
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "response": result["response"],
                "query_type": result["query_type"],
                "retrieved_docs_count": len(result.get("retrieved_docs", [])),
                "chat_history": result["chat_history"]
            }
            
        except Exception as e:
            logger.error(f"채팅 처리 오류: {e}")
            return {
                "response": "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.",
                "query_type": "error",
                "retrieved_docs_count": 0,
                "chat_history": chat_history or []
            }

# 전역 챗봇 인스턴스
chatbot_instance = None
chatbot_graph = None

def initialize_chatbot():
    """챗봇 초기화"""
    global chatbot_instance, chatbot_graph
    
    try:
        config = ChatbotConfig()
        chatbot_instance = RAGChatbot(config)
        chatbot_graph = ChatbotGraph(chatbot_instance)
        
        # 샘플 문서 추가 (실제 사용시에는 실제 문서 로드)
        sample_docs = [
            "이것은 샘플 문서입니다. 회사의 정책과 절차에 대한 정보를 담고 있습니다.",
            "고객 서비스 가이드라인: 모든 고객에게 친절하고 정중하게 응대해야 합니다.",
            "제품 사용법: 제품을 사용하기 전에 반드시 사용 설명서를 읽어보세요."
        ]
        chatbot_instance.add_documents(sample_docs)
        
        logger.info("챗봇 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"챗봇 초기화 오류: {e}")
        return False

async def chat_with_bot(user_query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """챗봇과 대화하는 메인 함수"""
    global chatbot_graph
    
    if not chatbot_graph:
        if not initialize_chatbot():
            return {
                "response": "챗봇을 초기화할 수 없습니다.",
                "query_type": "error",
                "retrieved_docs_count": 0,
                "chat_history": []
            }
    
    return await chatbot_graph.chat(user_query, chat_history)

# 동기적 래퍼 함수
def chat_sync(user_query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """동기적 채팅 인터페이스"""
    return asyncio.run(chat_with_bot(user_query, chat_history))

if __name__ == "__main__":
    # 테스트 코드
    async def test_chatbot():
        print("=== 챗봇 테스트 시작 ===")
        
        # 초기화
        if not initialize_chatbot():
            print("챗봇 초기화 실패")
            return
        
        # 테스트 쿼리들
        test_queries = [
            "안녕하세요!",
            "회사 정책에 대해 알려주세요",
            "고객 서비스는 어떻게 해야 하나요?",
            "오늘 날씨가 어때요?"
        ]
        
        chat_history = []
        
        for query in test_queries:
            print(f"\n사용자: {query}")
            result = await chat_with_bot(query, chat_history)
            print(f"챗봇 ({result['query_type']}): {result['response']}")
            print(f"검색된 문서 수: {result['retrieved_docs_count']}")
            chat_history = result['chat_history']
        
        print("\n=== 테스트 완료 ===")
    
    # 테스트 실행
    asyncio.run(test_chatbot())
