import os
import re
import glob
import logging
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loaders import load_documents

# 로깅 설정
os.makedirs("log", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("log/embedding.log", mode="a", encoding="utf-8")
    ]
)

# 환경 변수 로딩 및 설정
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = "rag_multiformat"
VECTOR_SIZE = 1536

# Qdrant 클라이언트 및 임베딩 모델 초기화
client = QdrantClient(url=QDRANT_URL, check_compatibility=False)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small")

# 조항 패턴 목록 (멀티 포맷 대응)
SECTION_PATTERNS = [
    r"(제\s*\d+\s*조\s*[^\n]*)",  # 제1조 목적
    r"^\s*\d+\.\s*[^\n]+",        # 1. 개요
    r"^\s*\[\s*.+?\s*\]",         # [목적]
    r"^\s*제?\w+\s*조\s+[^\n]+"  # 제일조 목적
]

# 조항 단위로 섹션 분리
def extract_sections_with_titles(text):
    for pattern in SECTION_PATTERNS:
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        if len(matches) >= 3:  # 최소 3개 이상 조항 감지되면 성공
            logging.info(f"패턴 매치 성공: {pattern} / {len(matches)}개")
            sections = []
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i+1].start() if i+1 < len(matches) else len(text)
                title = match.group(1).strip() if match.groups() else match.group().strip()
                body = text[start + len(title):end].strip()
                sections.append((title, body))
            return sections
        else:
            logging.info(f"패턴 매치 실패: {pattern}")
    
    logging.warning("조항 패턴 매치 실패. 전체 문서를 단일 청크로 처리합니다.")
    return [("전체본문", text)]

# Qdrant에 컬렉션 생성
def create_collection_if_not_exists():
    collections = client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

# 기존에 저장된 point ID 조회
def get_existing_point_ids():
    create_collection_if_not_exists()
    existing_ids = set()
    scroll = client.scroll(collection_name=COLLECTION_NAME, with_payload=True, limit=10000)
    for point in scroll[0]:
        payload = point.payload or {}
        metadata = payload.get("metadata", {})
        file = metadata.get("source")
        chunk_id = metadata.get("chunk_id")
        if file is not None and chunk_id is not None:
            file = os.path.abspath(file)
            existing_ids.add(f"{file}-{chunk_id}")
    return existing_ids

# 문서 임베딩 및 Qdrant 업로드 (개선된 버전)
def advanced_embed_and_upsert(file_path, existing_ids, department_id=None, common_doc=False) -> int:
    """
    개선된 임베딩 및 업로드 함수
    Args:
        file_path: 파일 경로
        existing_ids: 기존 point ID 집합
        department_id: 부서 ID (필터링용)
        common_doc: 공통 문서 여부
    Returns:
        업로드된 청크 수
    """
    try:
        file_path = os.path.abspath(file_path)
        docs = load_documents(file_path)
        joined_text = "\n".join([doc.page_content for doc in docs])
        sections = extract_sections_with_titles(joined_text)
        
        logging.info(f"문서 로드 개수: {len(docs)}")
        logging.info(f"조항 추출 개수: {len(sections)}")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        
        split_docs = []
        for title, content in sections:
            chunks = text_splitter.split_text(content)
            for chunk in chunks:
                combined_text = f"[{title}]\n{chunk}"
                split_docs.append(Document(page_content=combined_text, metadata={"title": title}))
        
        logging.info(f"최종 청크 개수: {len(split_docs)}")
        
        texts = [doc.page_content for doc in split_docs]
        vectors = embeddings.embed_documents(texts)
        
        new_points = []
        for i, (doc, vector) in enumerate(zip(split_docs, vectors)):
            unique_key = f"{file_path}-{i}"
            if unique_key in existing_ids:
                continue
            
            # 메타데이터 확장 (부서 ID, 공통 문서 여부, 파일명 추가)
            doc.metadata["source"] = file_path
            doc.metadata["chunk_id"] = i
            doc.metadata["department_id"] = department_id  # 부서 ID 추가
            doc.metadata["common_doc"] = common_doc        # 공통 문서 여부 추가
            doc.metadata["file_name"] = os.path.basename(file_path)  # 파일명 추가
            
            new_points.append(
                PointStruct(
                    id=f"{file_path}-{i}",  # 고유 ID 생성
                    vector=vector,
                    payload={
                        "text": doc.page_content,
                        "metadata": doc.metadata
                    }
                )
            )
        
        if new_points:
            client.upsert(collection_name=COLLECTION_NAME, points=new_points)
            logging.info(f"{file_path} → 신규 청크 {len(new_points)}개 업로드 완료")
            return len(new_points)
        else:
            logging.info(f"{file_path} → 이미 저장된 청크만 존재 (업로드 생략)")
            return 0
            
    except Exception as e:
        logging.error(f"{file_path} 처리 중 오류 발생: {e}")
        return 0

# 다중 파일 자동 처리 엔트리포인트
if __name__ == "__main__":
    create_collection_if_not_exists()
    existing_ids = get_existing_point_ids()
    
    logging.info(f"existing_ids 개수: {len(existing_ids)}")
    
    extensions = ["pdf", "docx", "csv", "txt", "md", "html", "pptx"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(f"data/*.{ext}"))
    
    if not files:
        logging.warning("폴더에 문서가 없습니다.")
    else:
        total_chunks = 0
        total_files = 0
        for file_path in files:
            logging.info(f"\n처리 중: {file_path}")
            added = advanced_embed_and_upsert(file_path, existing_ids)
            if added > 0:
                total_files += 1
                total_chunks += added
    
        # 요약 보고
        logging.info("\n업로드 요약")
        logging.info(f"신규 문서 수: {total_files}")
        logging.info(f"총 신규 청크 수: {total_chunks}")
        logging.info("모든 처리가 완료되었습니다.")
