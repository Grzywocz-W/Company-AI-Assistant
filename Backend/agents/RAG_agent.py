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
from langchain_community.vectorstores import FAISS
###
from models import modelsList
from modelSelector import createLLM
#
api_key = os.getenv("Gemini_API_Key")



class RagAgent:
    def __init__(self, model: modelsList,db_path: str = "vectorDB"):
        self.agent = createLLM(model, temperature=0.0)
##        self.agent = ChatGoogleGenerativeAI(
##            model=model.value,#jest to enum, a nie tablica
##            google_api_key=api_key,
##            temperature=0.1#małą kreatywność
##            )

        
        embeddedModel = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

        try:
            self.vectorDataBase = FAISS.load_local(
                folder_path=db_path, 
                embeddings=embeddedModel, 
                allow_dangerous_deserialization=True
                )
        except Exception as e:
            print(f"[RAG_agent] nie da się załadować bazy wektorowej: {e}")
            self.vectorDataBase = None

        def searchVectorDataBase(sentence: str):# dodano str, bo był błąd podczas pytania o liczby
            if self.vectorDataBase == None:
                return "Błąd backednu. Baza wektorowa niezdefiniowana"
            try:
                mostAccurateDocuments = self.vectorDataBase.similarity_search(sentence,k=3)#potestować dla różnego k
                result = ""
                for doc in mostAccurateDocuments:
                    result += doc.page_content
                    result += "\n\n...\n\n"
                return result
            except Exception as e:
                print(f"Błąd przeszukiwania dokumentów: {e}")
                return(f"Błąd przeszukiwania dokumentów: {e}")



        
        
        self.tools =[
            Tool(name = "searchDocuments",
                 func= searchVectorDataBase,
                 description = "Używaj to przeszukwiania dokumentów"
                 ),
            ]
        

        
        systemPrompt = """
        Jesteś agentem ds. dokumentacji i warunków firmy. 
        Otrzymujesz polecenie od Koordynatora. Masz za zadanie przeszukanie odpowiedzi na pytanie w zbiorze dokumentów firmy do który dano Ci dostęp.
        

        ZASADY BEZPIECZEŃSTWA I REALIZACJI ZADAŃ (GUARDRAILS):
        1. NIGDY nie zgaduj informacji. W tym celu przeszukaj bazę danych.
        1. ZAWSZE używaj narzędzia searchDocuments.
        2. Jako argumenty searchDocuments, podawaj słowa kluczone, ważne fragmenty zdań aby działało efektywniej:  np. "zwrot towaru termin reklamacja", a nie "ile dni ma klient na zwrot towaru".
        3. Swoją odpowiedź opieraj tylko na dancyh zwróconych z narzędzia. Nie wspominaj skąd je masz, tylko zwróc koordynatorowi to co zwróciłeś.
        4. Jeśli regulamin zawiera kroki, zwróc je w skróconej i czytelnej formie.
        
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
        try:
            response = self.agentExecutor.invoke(
                {"input": inputText}
                )
        
            if isinstance(response, dict):#czasem zwracany jest słownik, a czasem nie
                return response.get("output", str(response))#trzba sparsować na str
            else:
                return str(response)
        
        except Exception as e:
            print(f"[RAG_agent] Błąd wywołania agenta: {e}")
            return f"Błąd komunikacji z agentem RAG: {e}"


