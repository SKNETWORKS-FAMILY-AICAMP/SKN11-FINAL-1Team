import os
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, CSVLoader, TextLoader, JSONLoader,
    UnstructuredHTMLLoader, BSHTMLLoader, UnstructuredPowerPointLoader
)

def load_documents(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".csv":
        loader = CSVLoader(file_path)
    elif ext in [".txt", ".md"]:
        loader = TextLoader(file_path)
    elif ext == ".json":
        loader = JSONLoader(file_path)
    elif ext in [".html", ".htm"]:
        try:
            loader = UnstructuredHTMLLoader(file_path)
        except ImportError:
            loader = BSHTMLLoader(file_path)
    elif ext in [".pptx", ".ppt"]:
        loader = UnstructuredPowerPointLoader(file_path, mode="elements")
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")
    return loader.load()
