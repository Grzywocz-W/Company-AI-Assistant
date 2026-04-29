#create_vector_db.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

api_key = os.getenv("Gemini_API_Key")

pdf_paths = "documents/regulamin.pdf"

def createVectorDataBase():
    pdfLoader = PyPDFLoader(pdf_paths)
    pdfsContent = pdfLoader.load()

    chuckedContent = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = chuckedContent.split_documents(pdfsContent)

    embeddedDocuments = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

    vectorDataBase = FAISS.from_documents(documents,embeddedDocuments)#(tekst,wektor embbeded tego tekstu)

    vectorDataBase.save_local("vectorDB")

if __name__ == "__main__":
    createVectorDataBase()
