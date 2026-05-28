#createVectorDB.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from configLoader import loadConfig

api_key = os.getenv("Gemini_API_Key")
backendConfig = loadConfig('config.txt')

#pdf_paths = "documents/regulamin.pdf"

pdfs_path = backendConfig.get("DOCUMENTS_PATH")
db_path = backendConfig.get("VECTOR_DB_PATH")

def createVectorDataBase():
    #pdfLoader = PyPDFLoader(pdfs_path)
    pdfLoader = PyPDFDirectoryLoader(pdfs_path)
    loadedPdfs = pdfLoader.load()

    recursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(separators = ["\n§","§","\n\n","\n","."," "],#hierarchia cięcia.
        chunk_size=1000,chunk_overlap=200,keep_separator=True)
    chunks = recursiveCharacterTextSplitter.split_documents(loadedPdfs)

    embeddingModel = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

    vectorDataBase = FAISS.from_documents(chunks,embeddingModel)#(tekst,wektor embbeded tego tekstu)

    vectorDataBase.save_local(db_path)

if __name__ == "__main__":
    createVectorDataBase()
