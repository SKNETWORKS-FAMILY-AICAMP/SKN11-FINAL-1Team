# inspect_qdrant.py

import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# 환경 변수 로딩
load_dotenv()

# Qdrant 클라이언트 생성 (버전 경고 무시)
client = QdrantClient(url=os.getenv("QDRANT_URL"))

def inspect_qdrant():
    # 1. 컬렉션 목록 확인
    collections = client.get_collections().collections
    print(f"📦 현재 Qdrant 컬렉션 목록:")
    for c in collections:
        print(f" - {c.name}")

    # 2. rag_multiformat 컬렉션 벡터 수 확인
    try:
        collection_info = client.get_collection(collection_name="rag_multiformat")
        print(f"✅ rag_multiformat 컬렉션 벡터 수: {collection_info.vectors_count}")
    except Exception as e:
        print(f"❌ 컬렉션 정보를 가져오지 못했습니다: {e}")
        return

    # 3. 벡터 샘플 메타데이터 확인 (10개 제한)
    print(f"\n🔍 벡터 메타데이터 샘플:")
    scroll = client.scroll(collection_name="rag_multiformat", with_payload=True, limit=10)
    for i, point in enumerate(scroll[0]):
        metadata = point.payload.get("metadata", {})
        print(f"[{i+1}] title={metadata.get('title')}, dep={metadata.get('department_id')}, common={metadata.get('common_doc')}, source={metadata.get('source')}")

    # 4. 누락된 메타데이터 확인
    print(f"\n🧹 dep 또는 common 누락된 벡터:")
    missing = 0
    for point in scroll[0]:
        metadata = point.payload.get("metadata", {})
        if metadata.get("department_id") is None or metadata.get("common_doc") is None:
            missing += 1
            print(f"[❌ 누락] title={metadata.get('title')}, dep={metadata.get('department_id')}, common={metadata.get('common_doc')}, source={metadata.get('source')}")
    if missing == 0:
        print("✅ 누락된 메타데이터 없음!")

if __name__ == "__main__":
    inspect_qdrant()
