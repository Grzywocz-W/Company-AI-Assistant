#create_vector_db.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from configLoader import loadConfig

api_key = os.getenv("Gemini_API_Key")
backendConfig = loadConfig('config.txt')

#pdf_paths = "documents/regulamin.pdf"

pdf_paths = backendConfig.get("DOCUMENTS_PATH")
db_path = backendConfig.get("VECTOR_DB_PATH")

def createVectorDataBase():
    pdfLoader = PyPDFLoader(pdf_paths)
    pdfsContent = pdfLoader.load()

    chuckedContent = RecursiveCharacterTextSplitter(separators = ["\n§","§","\n\n","\n","."," "],#hierarchia cięcia.
        chunk_size=1000,chunk_overlap=200,keep_separator=True)
    documents = chuckedContent.split_documents(pdfsContent)

    embeddedDocuments = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

    vectorDataBase = FAISS.from_documents(documents,embeddedDocuments)#(tekst,wektor embbeded tego tekstu)

    vectorDataBase.save_local(db_path)

if __name__ == "__main__":
    createVectorDataBase()
