#RAG_agent.py.py
import os
###AI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import Tool
####RAG
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
###
from models import modelsList
#
api_key = os.getenv("Gemini_API_Key")



class RagAgent:
    def __init__(self, model: modelsList,pdf_paths: str = "dokumenty/regulamin.pdf"):
        
        self.agent = ChatGoogleGenerativeAI(
            model=model.value,#jest to enum, a nie tablica
            google_api_key=api_key,
            temperature=0.1#małą kreatywność
            )

        pdfLoader = PyPDFLoader(pdf_paths)
        pdfsContent = pdfLoader.load()

        chuckedContent = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        documents = chuckedContent.split_documents(pdfsContent)

        embeddedDocuments = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)


        self.vectorDataBase = FAISS.from_documents(documents,embeddedDocuments)#(tekst,wektor embbeded tego tekstu)

        def searchVectorDataBase(sentence: str):# dodano str, bo był błąd podczas pytania o liczby
            mostAccurateDocuments = self.vectorDataBase.similarity_search(sentence,k=3)#potestować dla różnego k
            result = ""
            for doc in mostAccurateDocuments:
                result += doc.page_content
                result += "\n\n...\n\n"
            return result



        
        
        self.tools =[
            Tool(name = "searchDocuments",
                 func= searchVectorDataBase,
                 description = "Używaj to przeszukwiania dokumentów"
                 ),
            ]
        

        
        systemPrompt = """
        Jesteś agentem ds. dokumentacji i warunków firmy. 
        Otrzymujesz polecenie od Koordynatora. Masz za zadanie przeszukanie odpowiedzi na pytanie w zbiorze dokumentów firmy do który dano Ci dostęp.
        

        ZASADY:
        1. ZAWSZE używaj narzędzia searchDocuments.
        2. Jako argumenty searchDocuments, podawaj słowa kluczone, ważne fragmenty zdań.
        3. Swoją odpowiedź opieraj tylko na dancyh zwróconych z narzędzia.
        
        Narzędzia: {tools}
        
        Format:
        Question: Rozkaz od Koordynatora
        Thought: Musisz przeszukać dokumenty.
        Action: {tool_names}
        Action Input: <szukana fraza>
        Observation: Fragmenty z wektorowej bazy danych.
        Thought: Masz potrzebne dane. Sformułuj raport.
        Final Answer: Raport dla Koordynatora.

        Question: {input}
        Thought:{agent_scratchpad}
        """

        prompt = PromptTemplate.from_template(systemPrompt)
        agentTMP = create_react_agent(self.agent, self.tools, prompt)

        self.agentExecutor = AgentExecutor(
            agent = agentTMP,
            tools = self.tools,
            verbose=True,#wypisuje w konsoli jak myśli
            handle_parsing_errors=True,
            )


    def ragAgentResponse(self, inputText: str):
        response = self.agentExecutor.invoke(
            {"input": inputText}
            )
        

        ###odpowiedź zawiera też podpis(signature)
        #response = response.content#wydobywamy tylko zawartość
        try:
            return response.get("output", "Błąd")#wydobywany pole text(niżej)
        except (IndexError, KeyError, TypeError):
            return str(response)

        return str(response)

