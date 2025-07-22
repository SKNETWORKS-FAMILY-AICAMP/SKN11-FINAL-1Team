import glob
from embed_and_upsert import advanced_embed_and_upsert, get_existing_point_ids, create_collection_if_not_exists

extensions = ["pdf", "docx", "csv", "txt", "md", "html", "pptx"]
files = []
for ext in extensions:
    files.extend(glob.glob(f"data/*.{ext}"))

# 1. 컬렉션이 없으면 생성
create_collection_if_not_exists()

# 2. 기존 point id 조회
existing_ids = get_existing_point_ids()

# 3. 신규 파일(또는 청크)만 임베딩/저장
for file_path in files:
    advanced_embed_and_upsert(file_path, existing_ids)
