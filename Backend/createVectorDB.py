#createVectorDB.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import (PyPDFDirectoryLoader, DirectoryLoader, TextLoader, UnstructuredWordDocumentLoader)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from configLoader import loadConfig

api_key = os.getenv("Gemini_API_Key")
backendConfig = loadConfig('.env')

#pdf_paths = "documents/regulamin.pdf"

pdfs_path = backendConfig.get("DOCUMENTS_PATH")
db_path = backendConfig.get("VECTOR_DB_PATH")

def createVectorDataBase():
    allDocuments = []

    # PDF
    try:
        pdfLoader = PyPDFDirectoryLoader(pdfs_path)
        loaded_pdfs = pdfLoader.load()
        allDocuments += loaded_pdfs
        print(f"[RAG] Załadowano {len(loaded_pdfs)} stron PDF")
    except Exception as e:
        print(f"[RAG] Błąd ładowania PDF: {e}")

    # TXT
    try:
        txtLoader = DirectoryLoader(
            pdfs_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        loaded_txtDocs = txtLoader.load()
        allDocuments += loaded_txtDocs
        print(f"[RAG] Załadowano {len(loaded_txtDocs)} plików TXT")
    except Exception as e:
        print(f"[RAG] Błąd ładowania TXT: {e}")

    # DOCX
    try:
        docxLoader = DirectoryLoader(
            pdfs_path,
            glob="**/*.docx",
            loader_cls=UnstructuredWordDocumentLoader
        )
        loaded_docxDocs = docxLoader.load()
        allDocuments += loaded_docxDocs
        print(f"[RAG] Załadowano {len(loaded_docxDocs)} plików DOCX")
    except Exception as e:
        print(f"[RAG] Błąd ładowania DOCX: {e}")

    if not allDocuments:
        print("[RAG] Brak dokumentów do wektoryzacji!")
        return

    recursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
        separators=["\n§", "§", "\n\n", "\n", ".", " "],
        chunk_size=1000,
        chunk_overlap=200,
        keep_separator=True
    )
    chunks = recursiveCharacterTextSplitter.split_documents(allDocuments)
    print(f"[RAG] Podzielono na {len(chunks)} fragmentów")

    embeddingModel = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )
    vectorDataBase = FAISS.from_documents(chunks, embeddingModel)
    vectorDataBase.save_local(db_path)
    print(f"[RAG] Baza wektorowa zapisana w: {db_path}")

if __name__ == "__main__":
    createVectorDataBase()
