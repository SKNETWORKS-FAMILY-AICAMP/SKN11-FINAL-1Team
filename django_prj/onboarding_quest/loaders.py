import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    BSHTMLLoader,
    UnstructuredPowerPointLoader
)

def load_documents(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)

    # elif ext == ".docx":
    #     loader = Docx2txtLoader(file_path)
    elif ext == ".docx":
        try:
            loader = Docx2txtLoader(file_path)  # 기본
        except Exception:
            from langchain_community.document_loaders import UnstructuredWordDocumentLoader
            loader = UnstructuredWordDocumentLoader(file_path)  # fallback

    elif ext in [".txt", ".md"]:
        loader = TextLoader(file_path, encoding="utf-8-sig")

    # elif ext in [".html", ".htm"]:
    #     try:
    #         loader = UnstructuredHTMLLoader(file_path)
    #     except ImportError:
    #         loader = BSHTMLLoader(file_path)
    elif ext in [".html", ".htm"]:
        try:
            loader = UnstructuredHTMLLoader(file_path)  # 더 정제된 추출
        except Exception:
            loader = BSHTMLLoader(file_path)  # fallback for robustness


    elif ext in [".pptx", ".ppt"]:
        loader = UnstructuredPowerPointLoader(file_path, mode="elements")

    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")

    return loader.load()
